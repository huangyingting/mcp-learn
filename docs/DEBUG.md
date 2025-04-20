DEBUG:mcp.server.sse:Sending message to writer: root=JSONRPCRequest(method='tools/call', params={'name': 'get_forecast', 'arguments': {'latitude': 47.6062, 'longitude': -122.3321}}, jsonrpc='2.0', id=2)

DEBUG:mcp.server.sse:Sending message via SSE: root=JSONRPCResponse(jsonrpc='2.0', id=2, result={'content': [{'type': 'text', 'text': 'This Afternoon:\nTemperature: 70°F\nWind: 3 mph SW\nForecast: Mostly sunny, with a high near 70. Southwest wind around 3 mph.\n---\nTonight:\nTemperature: 49°F\nWind: 6 mph NE\nForecast: A slight chance of rain showers between 1am and 4am. Mostly cloudy, with a low around 49. Northeast wind around 6 mph. Chance of precipitation is 20%. New rainfall amounts less than a tenth of an inch possible.\n---\nSaturday:\nTemperature: 58°F\nWind: 5 mph NNW\nForecast: A slight chance of rain showers after 1pm. Mostly cloudy, with a high near 58. North northwest wind around 5 mph. Chance of precipitation is 20%. New rainfall amounts less than a tenth of an inch possible.\n---\nSaturday Night:\nTemperature: 45°F\nWind: 6 mph SSE\nForecast: A slight chance of rain showers. Mostly cloudy, with a low around 45. South southeast wind around 6 mph. Chance of precipitation is 20%. New rainfall amounts less than a tenth of an inch possible.\n---\nSunday:\nTemperature: 57°F\nWind: 3 to 7 mph SSE\nForecast: Rain showers likely. Mostly cloudy, with a high near 57. South southeast wind 3 to 7 mph. Chance of precipitation is 70%. New rainfall amounts less than a tenth of an inch possible.'}], 'isError': False})


DEBUG:mcp.server.sse:Sending message to writer: root=JSONRPCRequest(method='tools/call', params={'name': 'get_forecast', 'arguments': {'latitude': 42.3601, 'longitude': -71.0589}}, jsonrpc='2.0', id=3)

DEBUG:mcp.server.sse:Sending message via SSE: root=JSONRPCResponse(jsonrpc='2.0', id=3, result={'content': [{'type': 'text', 'text': 'Tonight:\nTemperature: 55°F\nWind: 12 to 15 mph SW\nForecast: Mostly cloudy, with a low around 55. Southwest wind 12 to 15 mph, with gusts as high as 26 mph.\n---\nSaturday:\nTemperature: 80°F\nWind: 12 to 17 mph SW\nForecast: Partly sunny, with a high near 80. Southwest wind 12 to 17 mph, with gusts as high as 28 mph.\n---\nSaturday Night:\nTemperature: 54°F\nWind: 13 to 16 mph W\nForecast: Isolated rain showers between 9pm and 1am. Mostly cloudy, with a low around 54. West wind 13 to 16 mph, with gusts as high as 28 mph. Chance of precipitation is 20%.\n---\nSunday:\nTemperature: 62°F\nWind: 13 to 16 mph NW\nForecast: Sunny, with a high near 62. Northwest wind 13 to 16 mph, with gusts as high as 29 mph.\n---\nSunday Night:\nTemperature: 40°F\nWind: 3 to 12 mph NW\nForecast: Partly cloudy, with a low around 40. Northwest wind 3 to 12 mph.'}], 'isError': False})

[
  {
    "type": "function",
    "function": {
      "name": "get_alerts",
      "description": "\n  Tool to get active weather alerts for a US state.\n\n  Args:\n      state: Two-letter US state code (e.g., \"CA\" for California, \"NY\" for New York).\n\n  Returns:\n      str: Formatted string with active weather alerts, or a message if none are found.\n  ",
      "parameters": {
        "properties": {
          "state": {
            "title": "State",
            "type": "string"
          }
        },
        "required": [
          "state"
        ],
        "title": "get_alertsArguments",
        "type": "object"
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_forecast",
      "description": "\n  Tool to get the weather forecast for a specific location.\n\n  Args:\n      latitude: Latitude of the location.\n      longitude: Longitude of the location.\n\n  Returns:\n      str: Formatted string with the weather forecast for the next 5 periods, or an error message.\n  ",
      "parameters": {
        "properties": {
          "latitude": {
            "title": "Latitude",
            "type": "number"
          },
          "longitude": {
            "title": "Longitude",
            "type": "number"
          }
        },
        "required": [
          "latitude",
          "longitude"
        ],
        "title": "get_forecastArguments",
        "type": "object"
      }
    }
  }
]

[
  {
    "finish_reason": "tool_calls",
    "index": 0,
    "logprobs": null,
    "message": {
      "content": null,
      "refusal": null,
      "role": "assistant",
      "annotations": null,
      "audio": null,
      "function_call": null,
      "tool_calls": [
        {
          "id": "call_NdBNcz8FaAVtHInPMLGAZY71",
          "function": {
            "arguments": "{\"latitude\":47.6062,\"longitude\":-122.3321}",
            "name": "get_forecast"
          },
          "type": "function"
        }
      ]
    },
    "content_filter_results": {}
  }
]