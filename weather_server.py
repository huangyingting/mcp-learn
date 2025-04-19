from typing import Any
import httpx
from fastmcp import FastMCP
import argparse
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("weather")

# Initialize FastMCP server
weather_mcp = FastMCP("weather")

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
  """Make a request to the NWS API with proper error handling."""
  headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
  async with httpx.AsyncClient() as client:
    try:
      response = await client.get(url, headers=headers, timeout=30.0)
      response.raise_for_status()
      return response.json()
    except Exception:
      return None


def format_alert(feature: dict) -> str:
  """Format an alert feature into a readable string."""
  props = feature["properties"]
  return f"""
Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}
"""


@weather_mcp.tool()
async def get_alerts(state: str) -> str:
  """
  Tool to get active weather alerts for a US state.

  Args:
      state: Two-letter US state code (e.g., "CA" for California, "NY" for New York).

  Returns:
      str: Formatted string with active weather alerts, or a message if none are found.
  """
  url = f"{NWS_API_BASE}/alerts/active/area/{state.upper()}"
  data = await make_nws_request(url)

  if not data or "features" not in data:
      logger.warning(
          f"Failed to fetch alerts or malformed response for state: {state}")
      return "Unable to fetch alerts or no alerts found."

  features = data.get("features", [])
  if not features:
      logger.info(f"No active alerts for state: {state}")
      return "No active alerts for this state."

  alerts = [format_alert(feature) for feature in features]
  logger.debug(f"Found {len(alerts)} alert(s) for state: {state}")
  return "\n---\n".join(alerts)


@weather_mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
  """
  Tool to get the weather forecast for a specific location.

  Args:
      latitude: Latitude of the location.
      longitude: Longitude of the location.

  Returns:
      str: Formatted string with the weather forecast for the next 5 periods, or an error message.
  """
  # Get the forecast grid endpoint from NWS API
  points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
  points_data = await make_nws_request(points_url)

  if not points_data or "properties" not in points_data or "forecast" not in points_data["properties"]:
    logger.warning(
        f"Failed to fetch forecast grid endpoint for lat={latitude}, lon={longitude}")
    return "Unable to fetch forecast data for this location."

  # Get the forecast URL from the points response
  forecast_url = points_data["properties"]["forecast"]
  forecast_data = await make_nws_request(forecast_url)

  if not forecast_data or "properties" not in forecast_data or "periods" not in forecast_data["properties"]:
    logger.warning(
        f"Failed to fetch detailed forecast for lat={latitude}, lon={longitude}")
    return "Unable to fetch detailed forecast."

  # Format the periods into a readable forecast
  periods = forecast_data["properties"]["periods"]
  forecasts = []
  for period in periods[:5]:  # Only show next 5 periods
    forecast = (
        f"{period['name']}:\n"
        f"Temperature: {period['temperature']}°{period['temperatureUnit']}\n"
        f"Wind: {period['windSpeed']} {period['windDirection']}\n"
        f"Forecast: {period['detailedForecast']}\n"
    )
    forecasts.append(forecast.strip())

  return "\n---\n".join(forecasts)

# Example usage:
# To run the server with sse transport "uv run weather_server.py -t sse"
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="weather mcp server")
  parser.add_argument("--transport", "-t", choices=["stdio", "sse"], default="stdio",
                      help="MCP transport to use (stdio or sse)")
  args = parser.parse_args()
  weather_mcp.run(transport=args.transport)
