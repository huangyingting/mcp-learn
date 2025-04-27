# MCP Learn - Model Context Protocol Examples

This repository contains examples of using the Model Context Protocol (MCP).

## Overview

MCP allows Large Language Models (LLMs) to call external tools via a standardized protocol. This repository includes:

### MCP clients
- A cmdline client that can connect to any MCP server ([`clients/cmd_client.py`](clients/cmd_client.py))
- A chainlit client that can connect to any MCP server ([`clients/chainlit_client.py`](clients/chainlit_client.py))
- A streamlit client that can connect to any MCP server ([`clients/streamlit_client.py`](clients/streamlit_client.py))

### Agents that use MCP
- A langgraph agent that uses MCP to call external tools ([`agents/langgraph_agent.py`](agents/langgraph_agent.py))
- A semantic kernel agent that uses MCP to call external tools ([`agents/sk_agent.py`](agents/sk_agent.py))
- An autogen agent that uses MCP to call external tools ([`agents/autogen_agent.py`](agents/autogen_agent.py))
- An openai agent that uses MCP to call external tools ([`agents/openai_agent.py`](agents/openai_agent.py))
- An ADK(google) agent that uses MCP to call external tools ([`agents/adk_agent`](agents/adk_agent))
- A pydantic agent that uses MCP to call external tools ([`agents/pydantic_agent.py`](agents/pydantic_agent.py))
- An agno agent that uses MCP to call external tools ([`agents/agno_agent.py`](agents/agno_agent.py))
- A smolagents agent that uses MCP to call external tools ([`agents/smol_agent.py`](agents/smol_agent.py))
- An atomic agent that uses MCP to call external tools ([`agents/atomic_agent.py`](agents/atomic_agent.py))
- A llamaindex agent that uses MCP to call external tools ([`agents/llamainex_agent.py`](agents/llamaindex_agent.py))

### MCP servers
- A weather information server that provides weather forecasts and alerts ([`servers/weather_server.py`](servers/weather_server.py))
- A stock information server that provides stock prices and company information ([`servers/stock_server.py`](servers/stock_server.py))
- A NL2SQL server that translates natural language queries to SQL ([`servers/nl2sql_server.py`](servers/nl2sql_server.py))
- A time server that provides the current time ([`servers/timer_server.py`](servers/time_server.py))
- A search server that provides search capabilities ([`servers/search_server.py`](servers/search_server.py))
- A composite server that aggregrtes all MCP servers ([`servers/composite_server.py`](servers/composite_server.py))

## Setup

### Prerequisites

1. Python 3.10 or higher
2. [uv](https://github.com/astral-sh/uv) for Python package management

### Installation

```bash
# Clone this repository
git clone https://github.com/huangyingting/mcp-learn.git
cd mcp-learn

# Install dependencies
uv sync
```

### Environment Setup
Create a `.env` file in servers, clients, and agents directories by copying the `.env.example` file to `.env`:

```bash
cp .env.example .env
```
Update the `.env` file with your Azure OpenAI API key and other configurations as needed.

## Running the Examples

### Starting a Server

All MCP servers are located in the [`servers/`](servers/) directory. For example, to start the weather or stock server (both support two transport methods):

1. **stdio** (default): For direct communication with the client  
2. **sse**: For running as a web server

To start a server with SSE transport:

```bash
uv run servers/any_mcp_server.py -t sse
```

When using the SSE transport, the server starts on http://localhost:8000/sse by default.

There is a composite server that aggregates all MCP servers. To start the composite server:

```bash
uv run servers/composite_server.py -t sse
```

### Connecting with a client

MCP clients are located in the [`clients/`](clients/) directory. There are three client implementations available:

#### Command Line Client

The command line client (`cmd_client.py`) provides a simple text interface and can connect to either:
- A Python script server (stdio transport)
- An SSE web server

**To connect to a stdio server:**

```bash
uv run clients/cmd_client.py servers/any_mcp_server.py
```

**To connect to an SSE server:**

```bash
uv run clients/cmd_client.py http://localhost:8000/sse
```

Once connected, you can interact with the server through natural language queries. For example:

- Weather queries: "What's the weather forecast for latitude 40.7, longitude -74.0?" or "Are there any weather alerts in CA?"
- Stock queries: "What's the current price of AAPL?" or "Give me information about Google's stock"

Type `quit` or `exit` to end your session.

#### Chainlit Client

The Chainlit client (`chainlit_client.py`) provides a chat interface with message history and a more interactive experience:

```bash
uv run chainlit run clients/chainlit_client.py --port 9000
```

Then navigate to `http://localhost:9000` in your web browser to interact with the client.

#### Streamlit Client

The Streamlit client (`streamlit_client.py`) offers a web-based interface with additional UI capabilities:

```bash
uv run streamlit run clients/streamlit_client.py
```

Then navigate to `http://localhost:8501` in your web browser to interact with the client.

### Running the Agents

The agents are located in the [`agents/`](agents/) directory. Each agent demonstrates how to integrate MCP with different agent frameworks.

#### Semantic Kernel Agent
```bash
uv run agents/sk_agent.py
```

#### LangGraph Agent
```bash
uv run agents/langgraph_agent.py
```

#### AutoGen Agent
```bash
uv run agents/autogen_agent.py
```

#### OpenAI Agent
```bash
uv run agents/openai_agent.py
```

#### Google ADK Agent
```bash
uv run adk web --port 9000
```
Then, open your web browser and navigate to `http://localhost:9000` to interact with the agent through ADK's web interface.

#### Pydantic Agent
```bash
uv run agents/pydantic_agent.py
```

#### Agno Agent
```bash
uv run agents/agno_agent.py
```

#### SmolAgents Agent
```bash
uv run agents/smol_agent.py
```

#### Atomic Agent
```bash
uv run agents/atomic_agent.py
```

#### LlamaIndex Agent
```bash
uv run agents/llamaindex_agent.py
```

## Available MCP servers

### Weather Server

- `get_alerts`: Get weather alerts for a US state using a two-letter state code
- `get_forecast`: Get a weather forecast for a location by latitude and longitude

### Stock Server

- `current_date`: Get the current date
- `stock_price`: Get the stock price for a given ticker
- `stock_info`: Get information about a company by ticker
- `income_statement`: Get the quarterly income statement for a company

### NL2SQL Server

- `query_sql`: Execute a custom SQL query on the SQLite database
- `list_tables`: List all tables in the SQLite database
- `describe_table`: Get the structure of a specific table
- `execute_nonquery`: Execute a non-query SQL statement (INSERT, UPDATE, DELETE, etc.)
- `database_info`: Get general information about the connected SQLite database

### Time Server
- `get_current_time`: Get the current time in a specific timezone

### Search Server
- `web_search`: Search the web for a given query

### News Server
- `news_top_headlines`: Get top headlines from NewsAPI.
- `news_search`: Search for news articles using NewsAPI.
- `news_sources`: Get available news sources from