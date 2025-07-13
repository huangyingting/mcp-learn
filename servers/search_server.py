import argparse
import logging
from typing import Any
from fastmcp import FastMCP
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("search")

# Initialize FastMCP server
search_mcp = FastMCP("search")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TAVILY_SEARCH_ENDPOINT = "https://api.tavily.com/search"


@search_mcp.tool()
async def web_search(query: str, n: int = 1) -> str:
  """
  Search the web for real-time, up-to-date information using the Tavily API.

  Use this tool when you need current information, news, or answers from the internet that may not be in your training data. 
  This tool retrieves and summarizes the top online sources relevant to your query.

  Args:
      query: The search query string (what you want to find on the web).
      n: Number of top results to fetch and aggregate (default 3).

  Returns:
      str: Aggregated content from the top web search results, including titles, URLs, and content snippets.
  """
  if not TAVILY_API_KEY:
    logger.error("Tavily API key not set in environment variables.")
    return "Tavily API key not configured."

  headers = {
      "Authorization": f"Bearer {TAVILY_API_KEY}",
      "Content-Type": "application/json"
  }
  json_data = {
      "query": query,
      "num_results": n
  }
  async with httpx.AsyncClient() as client:
    try:
      response = await client.post(TAVILY_SEARCH_ENDPOINT, headers=headers, json=json_data, timeout=10.0)
      response.raise_for_status()
      data = response.json()
      results = data.get("results", [])
      if not results:
        return "No web results found."

      aggregated = []
      for item in results[:n]:
        url = item.get("url", "")
        title = item.get("title", "")
        snippet = item.get("content", "")
        aggregated.append(
            f"Title: {title}\nURL: {url}\nContent Snippet: {snippet}\n")
      return "\n---\n".join(aggregated)
    except Exception as e:
      logger.error(f"Tavily web search failed: {e}")
      return f"Web search failed: {e}"

# Example usage:
# To run the server with sse transport: "uv run search_server.py -t sse"
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="web search mcp server")
  parser.add_argument("--transport", "-t", choices=["stdio", "sse", "http"], default="stdio",
                      help="MCP transport to use (stdio or sse or http)")
  args = parser.parse_args()
  search_mcp.run(transport=args.transport)
