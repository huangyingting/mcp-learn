import json
import os
from collections.abc import Sequence
from contextlib import AsyncExitStack
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.sse import sse_client
from openai import AzureOpenAI
import logging
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)

class ColorFormatter(logging.Formatter):
  COLORS = {
      logging.DEBUG: Fore.CYAN,
      logging.INFO: Fore.GREEN,
      logging.WARNING: Fore.YELLOW,
      logging.ERROR: Fore.RED,
      logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT,
  }

  def format(self, record):
    color = self.COLORS.get(record.levelno, "")
    message = super().format(record)
    return f"{color}{message}{Style.RESET_ALL}"

# import mlflow
# mlflow.autolog()

# Set up logging with color
logger = logging.getLogger("client")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter("%(levelname)s: %(message)s"))
logger.handlers = [handler]

load_dotenv()

MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-4o"
MAX_TOKENS = 4096

class MCPClient:
  def __init__(self):
    self.session: ClientSession | None = None
    self.exit_stack = AsyncExitStack()

    self.openai = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

  async def connect_to_server(self, server_script_path: str):
    if not server_script_path.endswith(".py"):
      raise ValueError("Server script must be a .py file.")

    command = "python"
    server_params = StdioServerParameters(
        command=command, args=[server_script_path], env=None
    )

    stdio_transport = await self.exit_stack.enter_async_context(
        stdio_client(server_params)
    )
    self.stdio, self.write = stdio_transport
    self.session = await self.exit_stack.enter_async_context(
        ClientSession(self.stdio, self.write)
    )

    await self.session.initialize()

    response = await self.session.list_tools()
    self.available_tools = response.tools
    logger.debug(
        f"Connection to server with tools: {[tool.name for tool in self.available_tools]}")

  async def connect_to_sse_server(self, server_url: str):
    # Store the context managers so they stay alive
    self._streams_context = sse_client(url=server_url)
    streams = await self._streams_context.__aenter__()

    self._session_context = ClientSession(*streams)
    self.session: ClientSession = await self._session_context.__aenter__()

    await self.session.initialize()

    response = await self.session.list_tools()
    self.available_tools = response.tools
    logger.debug(
        f"Connection to server with tools: {[tool.name for tool in self.available_tools]}"
    )

  async def process_query(self, query: str) -> str:
    messages = [{"role": "user", "content": query}]
    available_tools = [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            },
        }
        for tool in self.available_tools
    ]

    # Recursive function to handle tool calls
    async def process_message():
      nonlocal messages

      response = self.openai.chat.completions.create(
          model=MODEL,
          max_tokens=MAX_TOKENS,
          messages=messages,
          tools=available_tools,
      )

      message = response.choices[0].message

      # If no tool calls, we're done
      if not message.tool_calls:
        return message.content

      # Add the assistant message with tool calls to the conversation
      messages.append(message)

      # Process each tool call
      for tool_call in message.tool_calls:
        tool_name = tool_call.function.name
        tool_call_id = tool_call.id

        tool_args = json.loads(tool_call.function.arguments)
        tool_result = await self.session.call_tool(tool_name, tool_args)
        tool_result_contents = [
            content.model_dump() for content in tool_result.content
        ]

        logger.debug(
            f"Tool call {tool_name} with args {tool_args} returned: {tool_result_contents}")
        # Add tool response message for this specific tool call
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call_id,
                "name": tool_name,
                "content": json.dumps(tool_result_contents),
            }
        )

      # Recursively process the next message with updated context
      return await process_message()

    # Start the recursive process
    return await process_message()

  async def chat_loop(self) -> None:

    print("MCP Client Started!")
    print("Type your queries or `quit` to exit.")

    while True:
      try:
        import readline
        query = input("Query: ").strip()
        if query.lower() == "quit" or query.lower() == "exit":
          break

        response = await self.process_query(query)
        print(response)
      except Exception as e:
        print(f"Error: {e!r}")

  async def cleanup(self):
    if hasattr(self, "_session_context") and self._session_context:
      await self._session_context.__aexit__(None, None, None)

    if hasattr(self, "_streams_context") and self._streams_context:
      await self._streams_context.__aexit__(None, None, None)

    await self.exit_stack.aclose()


async def main(argv: Sequence[str]) -> None:
  import sys

  if len(sys.argv) < 2:
    print("Usage:")
    print("  To connect to a Python script server:")
    print("    uv run client.py <path_to_server_script.py>")
    print("  To connect to an SSE server:")
    print("    uv run client.py <URL of SSE MCP server (e.g., http://localhost:8000/sse)>")
    sys.exit(1)

  arg = sys.argv[1]
  client = MCPClient()

  try:
    if arg.endswith(".py"):
      await client.connect_to_server(arg)
    elif arg.startswith("http"):
      await client.connect_to_sse_server(server_url=arg)
    else:
      print("Error: Argument must be either a .py file path or an HTTP(S) URL")
      sys.exit(1)

    await client.chat_loop()
  finally:
    await client.cleanup()

# Example usage:
# uv run client.py weather_server.py, or
# uv run client.py http://localhost:8000/sse
if __name__ == "__main__":
  import asyncio
  import sys

  asyncio.run(main(sys.argv))
