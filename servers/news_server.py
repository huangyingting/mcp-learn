import argparse
import logging
import os
from dotenv import load_dotenv
from newsapi import NewsApiClient
from fastmcp import FastMCP

# Load environment variables and set up logging
load_dotenv()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("news")

# Initialize FastMCP server
news_mcp = FastMCP("news")


class NewsAPIService:
  """Handles NewsAPI operations."""

  def __init__(self, api_key):
    self.api_key = api_key
    self.client = NewsApiClient(api_key=api_key)

  def get_top_headlines(self, **kwargs):
    try:
      return self.client.get_top_headlines(**kwargs)
    except Exception as e:
      return {"error": str(e)}

  def get_everything(self, **kwargs):
    try:
      return self.client.get_everything(**kwargs)
    except Exception as e:
      return {"error": str(e)}

  def get_sources(self, **kwargs):
    try:
      return self.client.get_sources(**kwargs)
    except Exception as e:
      return {"error": str(e)}

  @staticmethod
  def format_articles(articles):
    if not articles:
      return "No articles found."
    formatted = []
    for article in articles:
      formatted.append(
          f"Source: {article.get('source', {}).get('name', 'Unknown Source')}\n"
          f"Title: {article.get('title', 'No Title')}\n"
          f"Published: {article.get('publishedAt', '')}\n"
          f"Description: {article.get('description', 'No Description')}\n"
          f"URL: {article.get('url', '')}\n"
      )
    return "\n---\n".join(formatted)

  @staticmethod
  def format_sources(sources):
    if not sources:
      return "No sources found matching the criteria."
    formatted = []
    for source in sources:
      formatted.append(
          f"ID: {source.get('id', 'No ID')}\n"
          f"Name: {source.get('name', 'No Name')}\n"
          f"Description: {source.get('description', 'No Description')}\n"
          f"Category: {source.get('category', 'None')}\n"
          f"Language: {source.get('language', 'None')}\n"
          f"Country: {source.get('country', 'None')}\n"
          f"URL: {source.get('url', 'No URL')}\n"
      )
    return "\n---\n".join(formatted)


# Singleton for NewsAPIService
_news_api_service = None


def get_news_api_service():
  global _news_api_service
  if _news_api_service is None:
    api_key = os.environ.get("NEWS_API_KEY")
    if not api_key:
      logger.warning("NEWS_API_KEY not set in environment.")
      return None
    _news_api_service = NewsAPIService(api_key)
  return _news_api_service


@news_mcp.tool()
def news_top_headlines(
    country: str = None,
    category: str = None,
    sources: str = None,
    q: str = None,
    page_size: int = 5,
    page: int = 1,
) -> str:
  """
  Get top headlines from NewsAPI.
  """
  news_api = get_news_api_service()
  if not news_api:
    return "NewsAPI key not configured. Please set the NEWS_API_KEY environment variable."

  params = {k: v for k, v in {
      "country": country,
      "category": category,
      "sources": sources,
      "q": q,
      "page_size": min(page_size, 100) if page_size else None,
      "page": page,
  }.items() if v is not None}

  response = news_api.get_top_headlines(**params)
  if "error" in response:
    return f"Error: {response['error']}"

  articles = response.get("articles", [])
  total_results = response.get("totalResults", 0)
  formatted = news_api.format_articles(articles)
  return f"Found {total_results} articles. Showing {len(articles)} results.\n\n{formatted}"

# MCP Tool: Search for news articles


@news_mcp.tool()
def news_search(
    q: str,
    sources: str = None,
    domains: str = None,
    from_param: str = None,
    to: str = None,
    language: str = "en",
    sort_by: str = "publishedAt",
    page_size: int = 5,
    page: int = 1,
) -> str:
  """
  Search for news articles using NewsAPI.
  """
  news_api = get_news_api_service()
  if not news_api:
    return "NewsAPI key not configured. Please set the NEWS_API_KEY environment variable."

  params = {k: v for k, v in {
      "q": q,
      "sources": sources,
      "domains": domains,
      "from_param": from_param,
      "to": to,
      "language": language,
      "sort_by": sort_by,
      "page_size": min(page_size, 100) if page_size else None,
      "page": page,
  }.items() if v is not None}

  response = news_api.get_everything(**params)
  if "error" in response:
    return f"Error: {response['error']}"

  articles = response.get("articles", [])
  total_results = response.get("totalResults", 0)
  formatted = news_api.format_articles(articles)
  return f"Found {total_results} articles. Showing {len(articles)} results.\n\n{formatted}"

# MCP Tool: Get available news sources


@news_mcp.tool()
def news_sources(
    category: str = None,
    language: str = None,
    country: str = None,
) -> str:
  """
  Get available news sources from NewsAPI.
  """
  news_api = get_news_api_service()
  if not news_api:
    return "NewsAPI key not configured. Please set the NEWS_API_KEY environment variable."

  params = {k: v for k, v in {
      "category": category,
      "language": language,
      "country": country,
  }.items() if v is not None}

  response = news_api.get_sources(**params)
  if "error" in response:
    return f"Error: {response['error']}"

  sources = response.get("sources", [])
  formatted = news_api.format_sources(sources)
  return f"Found {len(sources)} sources:\n\n{formatted}"


# Run the server
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="News MCP server")
  parser.add_argument("--transport", "-t", choices=["stdio", "sse"], default="stdio",
                      help="MCP transport to use (stdio or sse)")
  args = parser.parse_args()
  news_mcp.run(transport=args.transport)
