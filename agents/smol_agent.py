from smolagents.agents import ToolCallingAgent
from smolagents import ToolCollection, AzureOpenAIServerModel
import os
from dotenv import load_dotenv
load_dotenv()

def main():
  model = AzureOpenAIServerModel(
      api_key=os.getenv("AZURE_OPENAI_API_KEY"),
      azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
      model_id=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
      api_version=os.getenv("AZURE_OPENAI_API_VERSION"))

  with ToolCollection.from_mcp({"url": "http://localhost:8000/sse"}, trust_remote_code=True) as tool_collection:
      agent = ToolCallingAgent(tools=[*tool_collection.tools], model=model)
      response = agent.run("What is the weather in New York?")
      print(response)

if __name__ == "__main__":
  main()