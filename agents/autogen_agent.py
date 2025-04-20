import asyncio
from autogen_ext.models.openai import AzureOpenAIChatCompletionClient
from autogen_ext.tools.mcp import SseMcpToolAdapter, SseServerParams
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
import os
from dotenv import load_dotenv
load_dotenv()

async def main() -> None:
    # Create server params for the remote MCP service
    server_params = SseServerParams(
        url="http://localhost:8000/sse",
        headers={"Content-Type": "application/json"},
        timeout=30,  # Connection timeout in seconds
    )

    # Get the weather tool from the server
    adapter = await SseMcpToolAdapter.from_server_params(server_params, "weather_get_forecast")

    model_client = AzureOpenAIChatCompletionClient(
        model=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY")
    )   
    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        tools=[adapter],
        system_message="You are a helpful assistant.",
    )

    # Let the agent translate some text
    await Console(
        agent.run_stream(task="What is the weather like today in Seattle?", cancellation_token=CancellationToken())
    )


if __name__ == "__main__":
    asyncio.run(main())
