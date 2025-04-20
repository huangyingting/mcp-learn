# Create server parameters for stdio connection
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_openai import AzureChatOpenAI
import os
from dotenv import load_dotenv
from langchain.schema import AIMessage
import asyncio

load_dotenv()

model = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
)


async def main():
  async with MultiServerMCPClient(
      {
          "math": {
              "command": "uv",
              # Replace with absolute path to your time_server.py file
              "args": ["run", "servers/time_server.py"],
              "transport": "stdio",
          },
          "weather": {
              "command": "uv",
              # Replace with absolute path to your weather_server.py file
              "args": ["run", "servers/weather_server.py"],
              "transport": "stdio",
          }
      }
  ) as client:
    agent = create_react_agent(
        model,
        client.get_tools()
    )
    response = await agent.ainvoke({"messages": "What is the current weather in New York?"})
    parsed_data = parse_ai_messages(response)
    for ai_message in parsed_data:
      print(ai_message)


def parse_ai_messages(data):
  messages = dict(data).get('messages', [])
  formatted_ai_responses = []

  for message in messages:
    if isinstance(message, AIMessage):
      formatted_message = f"### AI Response:\n\n{message.content}\n\n"
      formatted_ai_responses.append(formatted_message)

  return formatted_ai_responses


if __name__ == "__main__":
  asyncio.run(main())
