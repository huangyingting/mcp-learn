import os
import asyncio
from openai import AsyncAzureOpenAI
from openai import OpenAIError
from agents import Agent, Runner, OpenAIChatCompletionsModel
from agents.mcp import MCPServer, MCPServerSse
from dotenv import load_dotenv

load_dotenv()

async def run(mcp_server: MCPServer):
  try:
      # Create the Async Azure OpenAI client
      client = AsyncAzureOpenAI(
          api_key=os.getenv("AZURE_OPENAI_API_KEY"),
          api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
          azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
      )

      # Configure the agent with Azure OpenAI
      agent = Agent(
          name="Assistant",
          instructions="You are a helpful assistant, use the tools to answer the questions.",
          mcp_servers=[mcp_server],
          model=OpenAIChatCompletionsModel(
              model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
              openai_client=client,
          )
      )

      result = await Runner.run(agent, "What is the weather like today in Seattle?")
      print(result.final_output)

  except OpenAIError as e:
      print(f"OpenAI API Error: {str(e)}")
  except Exception as e:
      print(f"An unexpected error occurred: {str(e)}")    

async def main():
    async with MCPServerSse(
        name="composite",
        params={
            "url": "http://localhost:8000/sse",
        },
    ) as server:
      await run(server)

if __name__ == "__main__":
    asyncio.run(main())