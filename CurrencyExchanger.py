from typing import Tuple, Dict
import dotenv
import os
from dotenv import load_dotenv
import requests
import json
import streamlit as st
from openai import OpenAI

token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.github.ai/inference"
model_name = "openai/gpt-4o-mini"

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)


load_dotenv()
EXCHANGE_RATE_API_KEY = os.getenv('EXCHANGE_RATE_API_KEY')


def get_exchange_rate(base: str, target: str, amount: str) -> Tuple:
    url=f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/pair/{base}/{target}/{amount}"
    response = json.loads(requests.get(url).text)
    return (base, target, amount, f'{response["conversion_result"]:.2f}')

print(get_exchange_rate('USD','GBP',350))

def call_llm(textbox_input) -> Dict:
    """Make a call to the LLM with the textbox_input as the prompt.
       The output from the LLM should be a JSON (dict) with the base, amount and target"""
    
    tools = [
        {
                "type": "function",
                "function":{
                     "name": "get_exchange_rate",
                    "description": "Retrieves exchange rate.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "base": {
                                "type": "string",
                                "description": "Base Currency"
                            },
                            "target": {
                                "type": "string",
                                "description": "Target Currency"
                            },
                            "amount": {
                                "type": "string",
                                "description": "Amount"
                            },
                        },
                        "required": ["base","target","amount"]
                    }
                } 
        }
    ]
    try:
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                {
                    "role": "user",
                    "content": textbox_input,
                }
            ],
            temperature=1.0,
            top_p=1.0,
            max_tokens=1000,
            model=model_name,
            tools=tools
            )
    except Exception as e:
        print(f"Exception {e} for {textbox_input}")
    else:
        return response

def run_pipeline(user_input):
    """Based on textbox_input, determine if you need to use the tools (function calling) for the LLM.
    Call get_exchange_rate(...) if necessary"""
    response = call_llm(user_input)
    # st.write(response.choices[0].finish_reason)
    if response.choices[0].finish_reason == 'tool_calls': #tool_calls
        # Update this
        response_arguements = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
        base = response_arguements["base"];
        target = response_arguements["target"];
        amount = response_arguements["amount"];
        _, _, _, conversion_result = get_exchange_rate(base, target, amount)
        st.write(f"{amount} of {base} to {target} conversion is {conversion_result}")


    elif response.choices[0].finish_reason == 'stop': #tools not used
        # Update this
        st.write(f"{response.choices[0].message.content}")
    else:
        st.write("NotImplemented")

# Title of the app
st.title("Multilingual Money Exchanger")

# Text box for user input
user_input = st.text_input("Enter your currency and amount here:")

# Submit button
if st.button("Submit"):
    # Print the content of the text box
    run_pipeline(user_input)
    