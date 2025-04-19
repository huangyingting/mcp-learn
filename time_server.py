import argparse
import logging
from typing import Any
from fastmcp import FastMCP
import os
from dotenv import load_dotenv
import datetime
import pytz

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("time")

# Initialize FastMCP server
time_mcp = FastMCP("time")

@time_mcp.tool()
def get_current_time(timezone: str = "UTC") -> str:
    """
    Get the current date and time for any timezone.

    Use this tool when you need to know the current time or date for a specific city, country, or timezone (e.g., 'Asia/Taipei', 'UTC', 'America/New_York').

    Args:
        timezone: The timezone string (e.g., "Asia/Taipei"). Defaults to "UTC".

    Returns:
        str: The current date and time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) for the specified timezone.
        Example Response: "2023-07-25T14:30:00"
    """
    try:
        tz = pytz.timezone(timezone)
    except Exception:
        tz = pytz.timezone("UTC")
    now = datetime.datetime.now(tz)
    return now.isoformat(timespec="seconds")

# Example usage:
# To run the server with sse transport: "uv run time_server.py -t sse"
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="time mcp server")
    parser.add_argument("--transport", "-t", choices=["stdio", "sse"], default="stdio",
                        help="MCP transport to use (stdio or sse)")
    args = parser.parse_args()
    time_mcp.run(transport=args.transport)