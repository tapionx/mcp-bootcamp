"""
a simple script to interacto with OpenAI API
and providing a basic arithmetic tool the AI can use
"""

import json
import os

from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


def arithmetic_tool(operation, a, b):
    """
    Perform basic arithmetic operations.
    :param operation: str, one of ['add', 'subtract', 'multiply', 'divide']
    :param a: float, first number
    :param b: float, second number
    :return: float, result of the operation
    """
    if operation == "add":
        return a + b
    elif operation == "subtract":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        if b == 0:
            return "Error: Division by zero"
        return a / b
    else:
        return "Error: Unsupported operation"


def chat_with_tool(prompt):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "arithmetic_tool",
                "description": "Perform basic arithmetic operations",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                            "description": "The arithmetic operation to perform",
                        },
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"},
                    },
                    "required": ["operation", "a", "b"],
                },
            },
        }
    ]

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant capable of calling tools to perform arithmetic operations.",
        },
        {"role": "user", "content": prompt},
    ]

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if message.tool_calls:
        # Add the assistant's message with tool calls
        messages.append(message)

        tool_call = message.tool_calls[0]
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)

        if function_name == "arithmetic_tool":
            result = arithmetic_tool(
                function_args["operation"], function_args["a"], function_args["b"]
            )
            print(f"___ Tool call: {function_name} with args {function_args} and result {result}")

            # Add the tool result message
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                }
            )

            # Get the final response from OpenAI
            final_response = client.chat.completions.create(model="gpt-4", messages=messages)

            return final_response.choices[0].message.content
    else:
        return message.content


if __name__ == "__main__":
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        response = chat_with_tool(user_input)
        print(f"Assistant: {response}")
