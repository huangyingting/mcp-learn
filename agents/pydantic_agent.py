from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from openai import AsyncAzureOpenAI
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

client = AsyncAzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

model = OpenAIModel(
    'gpt-4o',
    provider=OpenAIProvider(openai_client=client),
)

server = MCPServerHTTP(url='http://localhost:8000/sse')  
agent = Agent(model, mcp_servers=[server])  

async def main():
    async with agent.run_mcp_servers():  
        result = await agent.run('What is the weather like today in Seattle?')
    print(result.output)

if __name__ == "__main__":
  asyncio.run(main())