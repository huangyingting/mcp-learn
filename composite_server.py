from fastmcp import FastMCP
from stock_server import stock_mcp 
from weather_server import weather_mcp
from time_server import time_mcp
from search_server import search_mcp
import argparse
import logging
import os
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("composite")

mcp = FastMCP("composite")

# Mount sub-apps with prefixes
mcp.mount("stock", stock_mcp)
mcp.mount("time", time_mcp)
mcp.mount("weather", weather_mcp)
mcp.mount("search", search_mcp)

@mcp.tool()
def ping(): 
    return "Composite OK"

# Example usage:
# To run the server with sse transport "uv run composite_server.py -t sse"
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="composite server")
  parser.add_argument("--transport", "-t", choices=["stdio", "sse"], default="stdio",
                      help="MCP transport to use (stdio or sse)")
  args = parser.parse_args()
  mcp.run(transport=args.transport)