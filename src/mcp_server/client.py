import asyncio
import sys, os
import ollama

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

SERVER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server.py")
MODEL_NAME = "llama3.2:1b"


def mcp_tool_to_ollama_format(tool) -> dict:
    """Converts an MCP tool's schema into the format Ollama expects."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.input_schema,
        },
    }

async def run_agent(user_question: str):
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER_SCRIPT])

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # --- Step 1: get the list of available tools from the server ---
            tools_result = await session.list_tools()
            ollama_tools = [mcp_tool_to_ollama_format(t) for t in tools_result.tools]
            print(f"Available tools: {[t.name for t in tools_result.tools]}\n")

            # --- Step 2: send the question + tool list to Ollama ---
            messages = [{"role": "user", "content": user_question}]
            response = ollama.chat(model=MODEL_NAME, messages=messages, tools=ollama_tools)

            # --- Step 3: if Ollama wants to call a tool, actually call it ---
            if response["message"].get("tool_calls"):
                for call in response["message"]["tool_calls"]:
                    tool_name = call["function"]["name"]
                    tool_args = call["function"]["arguments"]
                    print(f"LLM decided to call: {tool_name}({tool_args})")

                    result = await session.call_tool(tool_name, tool_args)
                    result_text = result.content[0].text

                    messages.append(response["message"])
                    messages.append({"role": "tool", "content": result_text})

                # --- Step 4: send the tool result back to Ollama for the final answer ---
                final_response = ollama.chat(model=MODEL_NAME, messages=messages, tools=ollama_tools)
                print("\nFinal answer:\n", final_response["message"]["content"])
            else:
                print("\nAnswer (no tool needed):\n", response["message"]["content"])


if __name__ == "__main__":
    question = "What is the current inventory for BOOK_SChand_5_Maths at Main Market?"
    asyncio.run(run_agent(question))