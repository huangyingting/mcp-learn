from agno.agent import Agent
from agno.models.azure import AzureOpenAI
from agno.tools.mcp import MCPTools
from mcp.client.sse import sse_client
from mcp import ClientSession
from dotenv import load_dotenv
import os
import asyncio

load_dotenv()

async def create_agent(session):
  """Create and configure a filesystem agent with MCP tools."""
  # Initialize the MCP toolkit
  mcp_tools = MCPTools(session=session)
  await mcp_tools.initialize()

  return Agent(
      model=AzureOpenAI(id="gpt-4o",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
      ),
      tools=[mcp_tools],
      instructions="You are a helpful assistant.",
      markdown=True
  )


async def run_agent(message: str) -> None:
    """Run the filesystem agent with the given message."""
    
    # Create a client session to connect to the MCP server
    async with sse_client(url="http://localhost:8000/sse") as (read, write):
        async with ClientSession(read, write) as session:
            agent = await create_agent(session)

            # Run the agent
            await agent.aprint_response(message, stream=True)


if __name__ == "__main__":
    asyncio.run(run_agent("What is the weather looks like at Seattle?"))
