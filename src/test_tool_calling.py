import ollama

from Agent.agent_tools import TOOLS


MODEL = "qwen2.5:3b"





def main():

    user_query = input("User: ")

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are a research assistant for AI GitHub projects.

Use tools when they are useful.
Do not invent project information.
Do not fetch GitHub data if existing data may be sufficient.
"""
            },
            {
                "role": "user",
                "content": user_query
            }
        ],
        tools=TOOL_DEFINITIONS
    )

    message = response["message"]

    print("\nLLM response:")
    print(message)

    if "tool_calls" not in message:
        print("\nNo tool call.")
        return

    for tool_call in message["tool_calls"]:

        function_name = tool_call["function"]["name"]
        arguments = tool_call["function"]["arguments"]

        print("\nTool selected:")
        print(function_name)

        print("\nArguments:")
        print(arguments)

        function = TOOLS[function_name]

        result = function(**arguments)

        print("\nTool result:")
        print(result)


if __name__ == "__main__":
    main()