import argparse
import sqlite3
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
import logging
import sys
import asyncio
from fastmcp import Context, FastMCP

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("nl2sql")

# SQLite database file path
SQLITE_DB_PATH = "data/chinook.db"

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[dict]:
  """Manage application lifecycle with type-safe context for SQLite"""
  logger.debug("Initializing SQLite database connection")
  conn = None
  try:
    def connect_db():
      logger.debug(f"Connecting to SQLite database at {SQLITE_DB_PATH}")
      return sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    loop = asyncio.get_event_loop()
    conn = await loop.run_in_executor(None, connect_db)
    logger.debug("SQLite database connection established successfully")
    yield {"conn": conn}
  except Exception as e:
    logger.error(
        f"SQLite connection error: {type(e).__name__}: {str(e)}", exc_info=True)
    yield {"conn": None}
  finally:
    if conn:
      logger.debug("Closing SQLite database connection")
      await asyncio.get_event_loop().run_in_executor(None, conn.close)

# Create an MCP server with the lifespan
nl2sql_mcp = FastMCP("nl2sql", lifespan=app_lifespan)


@nl2sql_mcp.tool()
async def query_sql(ctx: Context, query: str = None) -> str:
  """
  Tool to query the SQLite database with a custom query.
  Args:
                  query: The SQL query to execute. If not provided, will run a default query.
  Returns:
                  The query results as a string.
  """
  try:
    conn = ctx.request_context.lifespan_context["conn"]
    if conn is None:
      return "Database connection is not available. Check server logs for details."
    if not query:
      query = "SELECT name FROM sqlite_master WHERE type='table';"
    logger.debug(f"Executing query: {query}")

    def run_query():
      cursor = conn.cursor()
      try:
        cursor.execute(query)
        if cursor.description:
          columns = [column[0] for column in cursor.description]
          results = []
          for row in cursor.fetchall():
            results.append(dict(zip(columns, row)))
          return {"success": True, "results": results, "rowCount": len(results)}
        else:
          return {"success": True, "rowCount": cursor.rowcount, "message": f"Query affected {cursor.rowcount} rows"}
      except Exception as e:
        return {"success": False, "error": str(e)}
      finally:
        cursor.close()
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run_query)
    if result["success"]:
      if "results" in result:
        return f"Query results: {result['results']}"
      else:
        return result["message"]
    else:
      return f"Query error: {result['error']}"
  except Exception as e:
    logger.error(f"Query execution error: {type(e).__name__}: {str(e)}")
    return f"Error: {str(e)}"


@nl2sql_mcp.tool()
async def list_tables(ctx: Context) -> str:
  """List all tables in the SQLite database that can be queried."""
  try:
    conn = ctx.request_context.lifespan_context["conn"]
    if conn is None:
      return "Database connection is not available."

    def get_tables():
      cursor = conn.cursor()
      cursor.execute(
          "SELECT name FROM sqlite_master WHERE type='table';")
      tables = [row[0] for row in cursor.fetchall()]
      cursor.close()
      return tables
    loop = asyncio.get_event_loop()
    tables = await loop.run_in_executor(None, get_tables)
    return f"Available tables: {tables}"
  except Exception as e:
    return f"Error listing tables: {str(e)}"


@nl2sql_mcp.tool()
async def describe_table(ctx: Context, table_name: str) -> str:
  """
  Get the structure of a specific table in SQLite.
  Args:
                  table_name: Name of the table to describe
  Returns:
                  Column information for the specified table
  """
  try:
    conn = ctx.request_context.lifespan_context["conn"]
    if conn is None:
      return "Database connection is not available."

    def get_structure():
      cursor = conn.cursor()
      cursor.execute(f"PRAGMA table_info('{table_name}')")
      columns = []
      for row in cursor.fetchall():
        col_name, data_type = row[1], row[2]
        columns.append(f"{col_name} ({data_type})")
      cursor.close()
      return columns
    loop = asyncio.get_event_loop()
    structure = await loop.run_in_executor(None, get_structure)
    if structure:
      return f"Structure of table '{table_name}':\n" + "\n".join(structure)
    else:
      return f"Table '{table_name}' not found or has no columns."
  except Exception as e:
    return f"Error describing table: {str(e)}"


@nl2sql_mcp.tool()
async def execute_nonquery(ctx: Context, sql: str) -> str:
  """
  Execute a non-query SQL statement (INSERT, UPDATE, DELETE, etc.) in SQLite.
  Args:
                  sql: The SQL statement to execute
  Returns:
                  Result of the operation
  """
  try:
    conn = ctx.request_context.lifespan_context["conn"]
    if conn is None:
      return "Database connection is not available."

    def run_nonquery():
      try:
        cursor = conn.cursor()
        cursor.execute(sql)
        row_count = cursor.rowcount
        conn.commit()
        cursor.close()
        return {"success": True, "rowCount": row_count}
      except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e)}
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run_nonquery)
    if result["success"]:
      return f"Operation successful. Rows affected: {result['rowCount']}"
    else:
      return f"Operation failed: {result['error']}"
  except Exception as e:
    return f"Error executing SQL: {str(e)}"


@nl2sql_mcp.tool()
async def database_info(ctx: Context) -> str:
  """Get general information about the connected SQLite database"""
  try:
    conn = ctx.request_context.lifespan_context["conn"]
    if conn is None:
      return "Database connection is not available."

    def get_info():
      cursor = conn.cursor()
      cursor.execute("SELECT sqlite_version()")
      version = cursor.fetchone()[0]
      cursor.execute(
          "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
      table_count = cursor.fetchone()[0]
      cursor.close()
      return {
          "version": version,
          "database": SQLITE_DB_PATH,
          "table_count": table_count
      }
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, get_info)
    return (
        f"Database Information:\n"
        f"Database File: {info['database']}\n"
        f"SQLite Version: {info['version']}\n"
        f"Number of Tables: {info['table_count']}"
    )
  except Exception as e:
    return f"Error getting database info: {str(e)}"

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="nl2sql server")
  parser.add_argument("--transport", "-t", choices=["stdio", "sse"], default="stdio",
                      help="MCP transport to use (stdio or sse)")
  args = parser.parse_args()
  nl2sql_mcp.run(transport=args.transport)
