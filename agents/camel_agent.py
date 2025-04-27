import asyncio
from pathlib import Path
import os
from dotenv import load_dotenv
from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.toolkits.mcp_toolkit import MCPClient, MCPToolkit
from camel.types import ModelPlatformType, ModelType

load_dotenv()


async def main():
  mcp_toolkit = MCPClient(
      command_or_url="http://localhost:8000/sse",
  )

  await mcp_toolkit.connect()

  sys_msg = "You are a helpful assistant"
  model = ModelFactory.create(
      model_platform=ModelPlatformType.AZURE,
      model_type=ModelType.GPT_4O,
      api_key=os.getenv("AZURE_OPENAI_API_KEY"),
      url=os.getenv("AZURE_OPENAI_ENDPOINT"),
  )
  camel_agent = ChatAgent(
      system_message=sys_msg,
      model=model,
      tools=[*mcp_toolkit.get_tools()],
  )
  user_msg = "What is the weather like in New York?"
  response = await camel_agent.astep(user_msg)
  print(response.msgs[0].content)
  print(response.info['tool_calls'])

  await mcp_toolkit.disconnect()


if __name__ == "__main__":
  asyncio.run(main())
