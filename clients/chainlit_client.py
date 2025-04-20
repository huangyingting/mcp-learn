import json
from mcp import ClientSession
from openai import AsyncAzureOpenAI
import os
from dotenv import load_dotenv
import chainlit as cl

load_dotenv()

azure_openai = AsyncAzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
)

MODEL = os.getenv("AZURE_OPENAI_DEPLOYMENT") or "gpt-4o"
MAX_TOKENS = 4096

SYSTEM_PROMPT = "you are a helpful assistant."


@cl.on_mcp_connect
async def on_mcp_connect(connection, session: ClientSession):
  response = await session.list_tools()
  mcp_tools = cl.user_session.get("mcp_tools", {})
  mcp_tools[connection.name] = response.tools
  cl.user_session.set("mcp_tools", mcp_tools)


@cl.step(type="tool")
async def call_tool(tool_name, tool_args):

  current_step = cl.context.current_step
  current_step.name = tool_name
  mcp_tools = cl.user_session.get("mcp_tools", {})
  mcp_name = None

  tool_call_result = None

  for connection_name, tools in mcp_tools.items():
    if any(getattr(tool, "name", None) == tool_name for tool in tools):
      mcp_name = connection_name
      break

  if not mcp_name:
    tool_call_result = {
        "error": f"Tool {tool_name} not found in any MCP connection"}
    current_step.output = json.dumps(tool_call_result)
    return tool_call_result

  mcp_session, _ = cl.context.session.mcp_sessions.get(mcp_name)

  if not mcp_session:
    tool_call_result = {
        "error": f"MCP {mcp_name} not found in any MCP connection"}
    current_step.output = json.dumps(tool_call_result)
    return tool_call_result

  try:
    tool_call_result = await mcp_session.call_tool(tool_name, tool_args)
    current_step.output = tool_call_result
  except Exception as e:
    tool_call_result = {"error": str(e)}
    current_step.output = json.dumps(tool_call_result)

  return tool_call_result


async def call_azure_openai(chat_messages):
  def flatten(xss):
    return [x for xs in xss for x in xs]
  mcp_tools = cl.user_session.get("mcp_tools", {})
  available_tools = [
      {
          "type": "function",
          "function": {
              "name": tool.name,
              "description": tool.description,
              "parameters": tool.inputSchema,
          },
      }
      for tool in flatten([tools for _, tools in mcp_tools.items()])
  ]
  # Azure OpenAI expects messages in OpenAI format
  messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_messages

  # Only use non-streaming completion
  response = await azure_openai.chat.completions.create(
      model=MODEL,
      messages=messages,
      tools=available_tools if available_tools else None,
      max_tokens=MAX_TOKENS,
  )

  # Send the assistant's reply as a message
  message = response.choices[0].message
  if message.content:  # not None or empty
      await cl.Message(content=message.content).send()
  return message


@cl.on_chat_start
async def on_chat_start():
  cl.user_session.set("chat_messages", [])


@cl.on_message
async def on_message(msg: cl.Message):
  chat_messages = cl.user_session.get("chat_messages")
  chat_messages.append({"role": "user", "content": msg.content})
  response = await call_azure_openai(chat_messages)

  # Azure OpenAI tool call handling (if using tools)
  while hasattr(response, "tool_calls") and response.tool_calls:
    chat_messages.append(response.model_dump())
    tool_call_results = []
    for tool_call in response.tool_calls:
      tool_name = tool_call.function.name
      tool_args = json.loads(tool_call.function.arguments)
      tool_call_id = tool_call.id
      tool_call_result = await call_tool(tool_name, tool_args)
      tool_call_result_contents = [
          content.model_dump() for content in tool_call_result.content
      ]
      tool_call_results.append(
          {
              "role": "tool",
              "tool_call_id": tool_call_id,
              "name": tool_name,
              "content": json.dumps(tool_call_result_contents),
          }
      )
    chat_messages.extend(tool_call_results)
    response = await call_azure_openai(chat_messages)

  # Get the assistant's reply text
  content = response.content if hasattr(response, "content") else None

  chat_messages = cl.user_session.get("chat_messages")
  chat_messages.append({"role": "assistant", "content": content})
