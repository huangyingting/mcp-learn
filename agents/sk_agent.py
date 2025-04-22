import asyncio
import os
from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.connectors.mcp import MCPStdioPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from dotenv import load_dotenv

load_dotenv()


async def main():
  # 1. Create the agent
  async with (
      MCPStdioPlugin(
          name="Menu",
          description="Weather plugin, for any weather inquiry, call this plugin.",
          command="uv",
          args=[
              "run",
              "servers/weather_server.py",
          ],
      ) as weather_agent,
  ):
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        ),
        name="PersonalAssistant",
        instructions="Help the user with weather inquiry.",
        plugins=[weather_agent, TimePlugin()],
    )

    # 2. Create a thread to hold the conversation
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: ChatHistoryAgentThread | None = None
    while True:
      import readline
      user_input = input("User: ")
      if user_input.lower() == "exit":
        break
      # 3. Invoke the agent for a response
      response = await agent.get_response(messages=user_input, thread=thread)
      print(f"# {response.name}: {response} ")
      thread = response.thread

    # 4. Cleanup: Clear the thread
    await thread.delete() if thread else None

if __name__ == "__main__":
  asyncio.run(main())
