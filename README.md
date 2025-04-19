# MCP Learn - Model Control Protocol Examples

This repository contains examples of using the Model Control Protocol (MCP) to interact with external tools.

## Overview

MCP allows Large Language Models (LLMs) to call external tools via a standardized protocol. This repository includes:

- A client that connects to MCP servers and processes user queries
- A weather information server that provides weather forecasts and alerts
- A stock information server that provides stock prices and company information
- A NL2SQL server that translates natural language queries to SQL

## Setup

### Prerequisites

1. Python 3.10 or higher
2. [uv](https://github.com/astral-sh/uv) for Python package management

### Installation

```bash
# Clone this repository
git clone https://github.com/yourusername/mcp-learn.git
# or if using SSH
# git clone git@github.com:yourusername/mcp-learn.git
cd mcp-learn

# Install dependencies
uv sync
```

### Environment Setup

Create a `.env` file in the project root with your Azure OpenAI API credentials:

```
AZURE_OPENAI_ENDPOINT=<your-azure-openai-endpoint>
AZURE_OPENAI_API_KEY=<your-azure-openai-api-key>
OPENAI_API_VERSION=<api-version>
```

## Running the Examples

### Starting a Server

There are two server examples included: `weather_server.py` and `stock_server.py`. Both support two transport methods:

1. **stdio** (default): For direct communication with the client
2. **sse**: For running as a web server

To start a server with SSE transport:

```bash
uv run weather_server.py -t sse
# OR
uv run stock_server.py -t sse
```

When using the SSE transport, the server starts on http://localhost:8000/sse by default.

### Connecting the Client

The client can connect to either a Python script server (stdio) or an SSE server:

To connect to a stdio server:

```bash
uv run client.py weather_server.py
# OR
uv run client.py stock_server.py
# OR
uv run client.py nl2sql_server.py
```

To connect to an SSE server:

```bash
uv run client.py http://localhost:8000/sse
```

### Using the Client

Once connected, you can interact with the client by typing in queries. For example:

- Weather server: "What's the weather forecast for latitude 40.7, longitude -74.0?" or "Are there any weather alerts in CA?"
- Stock server: "What's the current price of AAPL?" or "Give me information about Google's stock"

Type `quit` or `exit` to end your session.

## Available Tools

### Weather Server

- `get_alerts`: Get weather alerts for a US state using a two-letter state code
- `get_forecast`: Get a weather forecast for a location by latitude and longitude

### Stock Server

- `current_date`: Get the current date
- `stock_price`: Get the stock price for a given ticker
- `stock_info`: Get information about a company by ticker
- `income_statement`: Get the quarterly income statement for a company
- `tickers://search/`: Search for a stock ticker by company name

### NL2SQL Server

- `query_sql`: Execute a custom SQL query on the SQLite database
- `list_tables`: List all tables in the SQLite database
- `describe_table`: Get the structure of a specific table
- `execute_nonquery`: Execute a non-query SQL statement (INSERT, UPDATE, DELETE, etc.)
- `list_odbc_drivers`: List available ODBC drivers (returns static info for SQLite)
- `database_info`: Get general information about the connected SQLite database

