import openai
import os

from utils import print_status

# Set OpenAI API key
openai.api_key_path = os.path.abspath(__file__ + "/../../.api-key")

# Function to call the GPT-3 API
# model: The model to use
# prompt: The prompt to use
# systemMessage: The system message to use
# userMessage: The user message to use
def call(model, systemMessage, userMessage):
  while True:
    # Generate a response
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": systemMessage},
            {"role": "user", "content": userMessage},
        ],

    )

    # Print the choices
    choices = response["choices"]
    for i, choice in enumerate(choices):
        print_status(f"{i}: {choice['message']['content']}")

    # Ask the user to choose a response
    choice = input("\033[1m\033[32mPress enter to accept the response, type in 'r' to regenrate:\033[0m ")
    if choice == "r":
        continue

    message = choices[0]["message"]["content"]
    break
    
  return message