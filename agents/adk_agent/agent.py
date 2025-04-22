import asyncio
from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, SseServerParams, StdioServerParameters
from google.adk.models.lite_llm import LiteLlm

load_dotenv('../.env')

async def get_tools_async():
  """Gets tools from MCP Server."""
  print("Attempting to connect to MCP server...")
  tools, exit_stack = await MCPToolset.from_server(
      connection_params=SseServerParams(url="http://localhost:8000/sse")
  )
  print("MCP toolset created successfully.")
  return tools, exit_stack

async def create_agent():
  """Gets tools from MCP Server."""
  tools, exit_stack = await get_tools_async()

  agent = LlmAgent(
      model=LiteLlm(model="azure/gpt-4o"),
      name='assistant',
      instruction='You are a helpful assistant.',
      tools=tools,
  )
  return agent, exit_stack


root_agent = create_agent()