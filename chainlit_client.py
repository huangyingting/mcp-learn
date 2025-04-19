# uv run chainlit run chainlit_client.py --port 9000

import os
import json
import asyncio
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import stdio_client, StdioServerParameters
import chainlit as cl

load_dotenv()

MODEL_NAME = "gpt-4o"
MAX_TOKENS = 4096

class MCPClientWeb:
    def __init__(self):
        self.session = None
        self.available_tools = []
        self._stdio_gen = None
        self._sse_gen = None

    async def connect(self, server_url_or_path: str):
        if server_url_or_path.endswith(".py"):
            command = "python"
            server_params = StdioServerParameters(
                command=command, args=[server_url_or_path], env=None
            )
            self._stdio_gen = stdio_client(server_params)
            stdio_transport = await self._stdio_gen.__aenter__()
            self.stdio, self.write = stdio_transport
            self.session = await ClientSession(self.stdio, self.write).__aenter__()
        elif server_url_or_path.startswith("http"):
            self._sse_gen = sse_client(url=server_url_or_path)
            streams = await self._sse_gen.__aenter__()
            self.session = await ClientSession(*streams).__aenter__()
        else:
            raise ValueError("Argument must be either a .py file path or an HTTP(S) URL")

        await self.session.initialize()
        response = await self.session.list_tools()
        self.available_tools = response.tools

    async def close(self):
        """Safely close all connections and resources."""
        
        # Helper function to safely close an async context manager
        async def safe_close(name, cm):
            if cm:
                try:
                    await cm.__aexit__(None, None, None)
                except RuntimeError as e:
                    if "cancel scope in a different task" in str(e):
                        print(f"Warning during {name} shutdown (expected): {e}")
                    else:
                        print(f"Error during {name} shutdown: {e}")
                except Exception as e:
                    print(f"Unexpected error during {name} shutdown: {e}")
                return None
            return cm
        
        # Close resources in reverse order of creation
        self.session = await safe_close("session", self.session)
        self._stdio_gen = await safe_close("stdio generator", self._stdio_gen)
        self._sse_gen = await safe_close("SSE generator", self._sse_gen)

    async def call(self, query: str):
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

        async def process_message():
            nonlocal messages
            import openai
            openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")
            openai.azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
            openai.api_type = "azure"
            openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")

            # Debug message - sending request to OpenAI
            await cl.Message(content=f"🔄 Sending request to OpenAI...", author="System").send()
            
            response = openai.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                max_tokens=MAX_TOKENS,
                tools=available_tools,
            )
            message = response.choices[0].message

            # Debug message - received response from OpenAI
            await cl.Message(content=f"✅ Received response from OpenAI", author="System").send()
            
            if not getattr(message, "tool_calls", None):
                return message.content

            messages.append(message.model_dump())
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_call_id = tool_call.id
                tool_args = json.loads(tool_call.function.arguments)
                
                # Debug message - calling tool
                code_fence = "```"
                await cl.Message(
                    content=f"🛠️ Calling tool: **{tool_name}**\nArguments: {json.dumps(tool_args, indent=2)}", 
                    author="System"
                ).send()
                
                tool_result = await self.session.call_tool(tool_name, tool_args)
                tool_result_contents = [
                    content.model_dump() for content in tool_result.content
                ]
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call_id,
                        "name": tool_name,
                        "content": json.dumps(tool_result_contents),
                    }
                )
            return await process_message()

        return await process_message()

client = MCPClientWeb()

@cl.on_chat_start
async def start():
    server = os.getenv("MCP_SERVER", "http://localhost:8000/sse")
    await client.connect(server)
    await cl.Message(content=f"Connected to MCP server: {server}").send()

@cl.on_message
async def main(message: cl.Message):
    query = message.content
    response = await client.call(query)
    await cl.Message(content=response).send()

@cl.on_chat_end
async def cleanup():
    await client.close()