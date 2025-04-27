from llama_index.llms.azure_openai import AzureOpenAI
import dotenv
import os
from llama_index.tools.mcp import McpToolSpec
from llama_index.core.agent.workflow import FunctionAgent, ToolCallResult, ToolCall
from llama_index.core.workflow import Context
from llama_index.tools.mcp import BasicMCPClient, McpToolSpec
import asyncio

dotenv.load_dotenv()

llm = AzureOpenAI(
    engine=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

SYSTEM_PROMPT = """\
You are a helpful assistant, use the tools to answer the questions.
"""


async def get_agent(tools: McpToolSpec):
  tools = await tools.to_tool_list_async()
  agent = FunctionAgent(
      name="Agent",
      description="An agent that can use the tools.",
      tools=tools,
      llm=llm,
      system_prompt=SYSTEM_PROMPT,
  )
  return agent


async def handle_user_message(
    message_content: str,
    agent: FunctionAgent,
    agent_context: Context,
    verbose: bool = False,
):
  handler = agent.run(message_content, ctx=agent_context)
  async for event in handler.stream_events():
    if verbose and type(event) == ToolCall:
      print(f"Calling tool {event.tool_name} with kwargs {event.tool_kwargs}")
    elif verbose and type(event) == ToolCallResult:
      print(f"Tool {event.tool_name} returned {event.tool_output}")

  response = await handler
  return str(response)


async def main():
  mcp_client = BasicMCPClient("http://localhost:8000/sse")
  mcp_tool = McpToolSpec(client=mcp_client)
  agent = await get_agent(mcp_tool)
  agent_context = Context(agent)
  # Run the agent!
  while True:
    import readline

    user_input = input("Query: ")
    if user_input == "exit":
      break
    print("User: ", user_input)
    response = await handle_user_message(user_input, agent, agent_context, verbose=True)
    print("Agent: ", response)

if __name__ == "__main__":
  asyncio.run(main())
