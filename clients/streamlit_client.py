from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages.tool import ToolMessage
from langchain_core.messages.ai import AIMessageChunk
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
import streamlit as st
import asyncio
import nest_asyncio
import os
from typing import Any, Dict, List, Callable, Optional
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
import uuid


async def stream_graph(
    graph: CompiledStateGraph,
    inputs: dict,
    config: Optional[RunnableConfig] = None,
    node_names: List[str] = [],
    callback: Optional[Callable] = None,
    stream_mode: str = "messages",
    include_subgraphs: bool = False,
) -> Dict[str, Any]:
  config = config or {}
  final_result = {}
  prev_node = ""

  if stream_mode == "messages":
    async for chunk_msg, metadata in graph.astream(
        inputs, config, stream_mode=stream_mode
    ):
      curr_node = metadata["langgraph_node"]
      final_result = {
          "node": curr_node,
          "content": chunk_msg,
          "metadata": metadata,
      }

      if not node_names or curr_node in node_names:
        if callback:
          result = callback({"node": curr_node, "content": chunk_msg})
          if hasattr(result, "__await__"):
            await result
        else:
          if curr_node != prev_node:
            print("\n" + "=" * 50)
            print(f"🔄 Node: \033[1;36m{curr_node}\033[0m 🔄")
            print("- " * 25)

          # Handle Claude/Anthropic model token chunks - always extract text only
          if hasattr(chunk_msg, "content"):
            if isinstance(chunk_msg.content, list):
              for item in chunk_msg.content:
                if isinstance(item, dict) and "text" in item:
                  print(item["text"], end="", flush=True)
            elif isinstance(chunk_msg, str):
              print(chunk_msg, end="", flush=True)
          else:
            print(chunk_msg, end="", flush=True)

        prev_node = curr_node

  elif stream_mode == "updates":
    async for chunk in graph.astream(
        inputs, config, stream_mode=stream_mode, subgraphs=include_subgraphs
    ):
      if isinstance(chunk, tuple) and len(chunk) == 2:
        namespace, node_chunks = chunk
      else:
        namespace = []
        node_chunks = chunk

      if isinstance(node_chunks, dict):
        for node_name, node_chunk in node_chunks.items():
          final_result = {
              "node": node_name,
              "content": node_chunk,
              "namespace": namespace,
          }

          if len(node_names) > 0 and node_name not in node_names:
            continue

          if callback is not None:
            result = callback({"node": node_name, "content": node_chunk})
            if hasattr(result, "__await__"):
              await result
          else:
            if node_name != prev_node:
              print("\n" + "=" * 50)
              print(f"🔄 Node: \033[1;36m{node_name}\033[0m 🔄")
              print("- " * 25)

            if isinstance(node_chunk, dict):
              for k, v in node_chunk.items():
                if isinstance(v, BaseMessage):
                  if hasattr(v, "content"):
                    if isinstance(v.content, list):
                      for item in v.content:
                        if (
                            isinstance(item, dict)
                            and "text" in item
                        ):
                          print(
                              item["text"], end="", flush=True
                          )
                    else:
                      print(v.content, end="", flush=True)
                  else:
                    v.pretty_print()
                elif isinstance(v, list):
                  for list_item in v:
                    if isinstance(list_item, BaseMessage):
                      if hasattr(list_item, "content"):
                        if isinstance(list_item.content, list):
                          for item in list_item.content:
                            if (
                                isinstance(item, dict)
                                and "text" in item
                            ):
                              print(
                                  item["text"],
                                  end="",
                                  flush=True,
                              )
                        else:
                          print(
                              list_item.content,
                              end="",
                              flush=True,
                          )
                      else:
                        list_item.pretty_print()
                    elif (
                        isinstance(list_item, dict)
                        and "text" in list_item
                    ):
                      print(list_item["text"], end="", flush=True)
                    else:
                      print(list_item, end="", flush=True)
                elif isinstance(v, dict) and "text" in v:
                  print(v["text"], end="", flush=True)
                else:
                  print(v, end="", flush=True)
            elif node_chunk is not None:
              if hasattr(node_chunk, "__iter__") and not isinstance(
                  node_chunk, str
              ):
                for item in node_chunk:
                  if isinstance(item, dict) and "text" in item:
                    print(item["text"], end="", flush=True)
                  else:
                    print(item, end="", flush=True)
              else:
                print(node_chunk, end="", flush=True)

          prev_node = node_name
      else:
        print("\n" + "=" * 50)
        print(f"🔄 Raw output 🔄")
        print("- " * 25)
        print(node_chunks, end="", flush=True)
        final_result = {"content": node_chunks}

  else:
    raise ValueError(
        f"Invalid stream_mode: {stream_mode}. Must be 'messages' or 'updates'."
    )

  return final_result

load_dotenv()

nest_asyncio.apply()

if "event_loop" not in st.session_state:
  loop = asyncio.new_event_loop()
  st.session_state.event_loop = loop
  asyncio.set_event_loop(loop)

SYSTEM_PROMPT = """<ROLE>
You are a smart agent with an ability to use tools. 
You will be given a question and you will use the tools to answer the question.
Pick the most relevant tool to answer the question. 
If you are failed to answer the question, try different tools to get context.
Your answer should be very polite and professional.
</ROLE>

----

<INSTRUCTIONS>
Step 1: Analyze the question
- Analyze user's question and final goal.
- If the user's question is consist of multiple sub-questions, split them into smaller sub-questions.

Step 2: Pick the most relevant tool
- Pick the most relevant tool to answer the question.
- If you are failed to answer the question, try different tools to get context.

Step 3: Answer the question
- Answer the question in the same language as the question.
- Your answer should be very polite and professional.

Step 4: Provide the source of the answer(if applicable)
- If you've used the tool, provide the source of the answer.
- Valid sources are either a website(URL) or a document(PDF, etc).

Guidelines:
- If you've used the tool, your answer should be based on the tool's output(tool's output is more important than your own knowledge).
- If you've used the tool, and the source is valid URL, provide the source(URL) of the answer.
- Skip providing the source if the source is not URL.
- Answer in the same language as the question.
- Answer should be concise and to the point.
- Avoid response your output with any other information than the answer and the source.  
</INSTRUCTIONS>

----

<OUTPUT_FORMAT>
(concise answer to the question)

**Source**(if applicable)
- (source1: valid URL)
- (source2: valid URL)
- ...
</OUTPUT_FORMAT>
"""

if "session_initialized" not in st.session_state:
  st.session_state.session_initialized = False
  st.session_state.agent = None
  st.session_state.history = []
  st.session_state.mcp_client = None
  st.session_state.timeout_seconds = (
      120
  )
  st.session_state.recursion_limit = 100  # Recursion call limit, default 100

if "thread_id" not in st.session_state:
  st.session_state.thread_id = uuid.uuid4()


async def close_mcp_client():
  """
  Safely terminates the existing MCP client.

  Properly releases resources if an existing client exists.
  """
  if "mcp_client" in st.session_state and st.session_state.mcp_client is not None:
    try:

      await st.session_state.mcp_client.__aexit__(None, None, None)
      st.session_state.mcp_client = None
    except Exception as e:
      import traceback

      st.warning(f"Error while terminating MCP client: {str(e)}")
      st.warning(traceback.format_exc())


def render_history():
  """
  Displays chat history on the screen.

  Distinguishes between user and assistant messages on the screen,
  and displays tool call information within the assistant message container.
  """
  i = 0
  while i < len(st.session_state.history):
    message = st.session_state.history[i]

    if message["role"] == "user":
      st.chat_message("user", avatar="🧑‍💻").markdown(message["content"])
      i += 1
    elif message["role"] == "assistant":
      with st.chat_message("assistant", avatar="🤖"):
        st.markdown(message["content"])
        if (
            i + 1 < len(st.session_state.history)
            and st.session_state.history[i + 1]["role"] == "assistant_tool"
        ):
          with st.expander("🔧 Tool Call Information", expanded=False):
            st.markdown(st.session_state.history[i + 1]["content"])
          i += 2
        else:
          i += 1
    else:
      i += 1


def create_stream_callback(text_placeholder, tool_placeholder):
  """
  Creates a streaming callback function.

  This function creates a callback function to display responses generated from the LLM in real-time.
  It displays text responses and tool call information in separate areas.

  Args:
      text_placeholder: Streamlit component to display text responses
      tool_placeholder: Streamlit component to display tool call information

  Returns:
      callback_func: Streaming callback function
      accumulated_text: List to store accumulated text responses
      accumulated_tool: List to store accumulated tool call information
  """
  accumulated_text = []
  accumulated_tool = []

  def callback_func(message: dict):
    nonlocal accumulated_text, accumulated_tool
    message_content = message.get("content", None)

    if isinstance(message_content, AIMessageChunk):
      content = message_content.content
      if isinstance(content, list) and len(content) > 0:
        message_chunk = content[0]
        if message_chunk["type"] == "text":
          accumulated_text.append(message_chunk["text"])
          text_placeholder.markdown("".join(accumulated_text))
        elif message_chunk["type"] == "tool_use":
          if "partial_json" in message_chunk:
            accumulated_tool.append(message_chunk["partial_json"])
          else:
            tool_call_chunks = message_content.tool_call_chunks
            tool_call_chunk = tool_call_chunks[0]
            accumulated_tool.append(
                "\n```json\n" + str(tool_call_chunk) + "\n```\n"
            )
          with tool_placeholder.expander(
              "🔧 Tool Call Information", expanded=True
          ):
            st.markdown("".join(accumulated_tool))
      elif (
          hasattr(message_content, "tool_calls")
          and message_content.tool_calls
          and len(message_content.tool_calls[0]["name"]) > 0
      ):
        tool_call_info = message_content.tool_calls[0]
        accumulated_tool.append(
            "\n```json\n" + str(tool_call_info) + "\n```\n")
        with tool_placeholder.expander(
            "🔧 Tool Call Information", expanded=True
        ):
          st.markdown("".join(accumulated_tool))
      elif isinstance(content, str):
        accumulated_text.append(content)
        text_placeholder.markdown("".join(accumulated_text))
      elif (
          hasattr(message_content, "invalid_tool_calls")
          and message_content.invalid_tool_calls
      ):
        tool_call_info = message_content.invalid_tool_calls[0]
        accumulated_tool.append(
            "\n```json\n" + str(tool_call_info) + "\n```\n")
        with tool_placeholder.expander(
            "🔧 Tool Call Information (Invalid)", expanded=True
        ):
          st.markdown("".join(accumulated_tool))
      elif (
          hasattr(message_content, "tool_call_chunks")
          and message_content.tool_call_chunks
      ):
        tool_call_chunk = message_content.tool_call_chunks[0]
        accumulated_tool.append(
            "\n```json\n" + str(tool_call_chunk) + "\n```\n"
        )
        with tool_placeholder.expander(
            "🔧 Tool Call Information", expanded=True
        ):
          st.markdown("".join(accumulated_tool))
      elif (
          hasattr(message_content, "additional_kwargs")
          and "tool_calls" in message_content.additional_kwargs
      ):
        tool_call_info = message_content.additional_kwargs["tool_calls"][0]
        accumulated_tool.append(
            "\n```json\n" + str(tool_call_info) + "\n```\n")
        with tool_placeholder.expander(
            "🔧 Tool Call Information", expanded=True
        ):
          st.markdown("".join(accumulated_tool))
    elif isinstance(message_content, ToolMessage):
      accumulated_tool.append(
          "\n```json\n" + str(message_content.content) + "\n```\n"
      )
      with tool_placeholder.expander("🔧 Tool Call Information", expanded=True):
        st.markdown("".join(accumulated_tool))
    return None

  return callback_func, accumulated_text, accumulated_tool


async def handle_query(query, text_placeholder, tool_placeholder, timeout_seconds=60):
  """
  Processes user questions and generates responses.

  This function passes the user's question to the agent and streams the response in real-time.
  Returns a timeout error if the response is not completed within the specified time.

  Args:
      query: Text of the question entered by the user
      text_placeholder: Streamlit component to display text responses
      tool_placeholder: Streamlit component to display tool call information
      timeout_seconds: Response generation time limit (seconds)

  Returns:
      response: Agent's response object
      final_text: Final text response
      final_tool: Final tool call information
  """
  try:
    if st.session_state.agent:
      streaming_callback, accumulated_text_obj, accumulated_tool_obj = (
          create_stream_callback(text_placeholder, tool_placeholder)
      )
      try:
        response = await asyncio.wait_for(
            stream_graph(
                st.session_state.agent,
                {"messages": [HumanMessage(content=query)]},
                callback=streaming_callback,
                config=RunnableConfig(
                    recursion_limit=st.session_state.recursion_limit,
                    thread_id=st.session_state.thread_id,
                ),
            ),
            timeout=timeout_seconds,
        )
      except asyncio.TimeoutError:
        error_msg = f"⏱️ Request time exceeded {timeout_seconds} seconds. Please try again later."
        return {"error": error_msg}, error_msg, ""

      final_text = "".join(accumulated_text_obj)
      final_tool = "".join(accumulated_tool_obj)
      return response, final_text, final_tool
    else:
      return (
          {"error": "🚫 Agent has not been initialized."},
          "🚫 Agent has not been initialized.",
          "",
      )
  except Exception as e:
    import traceback

    error_msg = f"❌ Error occurred during query processing: {str(e)}\n{traceback.format_exc()}"
    return {"error": error_msg}, error_msg, ""


async def setup_session(mcp_server_address):
  """
  Initializes MCP session and agent.

  Args:
      mcp_server_address: MCP server address

  Returns:
      bool: Initialization success status
  """
  with st.spinner("🔄 Connecting to MCP server..."):
    await close_mcp_client()

    if mcp_server_address is None:
      raise ValueError("MCP server address must be provided explicitly.")

    client = MultiServerMCPClient(
        {
            "mcp_server": {
                "url": mcp_server_address,
                "transport": "sse",
            }
        }
    )
    await client.__aenter__()
    tools = client.get_tools()
    st.session_state.tools = tools  # Store tools in session state
    st.session_state.mcp_client = client

    model = AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        temperature=0.1,
        max_tokens=4096,
    )

    agent = create_react_agent(
        model,
        tools,
        checkpointer=MemorySaver(),
        prompt=SYSTEM_PROMPT,
    )
    st.session_state.agent = agent
    st.session_state.session_initialized = True
    return True

with st.sidebar:
  st.subheader("📊 MCP")
  tool_names = []
  if "tools" in st.session_state and st.session_state.tools:
    tool_names = [tool.name for tool in st.session_state.tools]
    st.write(
        f"🛠️ Tools Count: {len(st.session_state.tools)}"
    )
    st.markdown(
        "\n".join(f"- {name}" for name in tool_names),
    )

  if "mcp_server_address" not in st.session_state:
    st.session_state.mcp_server_address = ""
  mcp_server_address = st.text_input(
      "MCP Server Address:",
      value=st.session_state.mcp_server_address,
      help="Enter the MCP server address for MCP connection.",
      key="mcp_server_address_input",
      disabled=st.session_state.session_initialized  # <-- disable if initialized
  )
  st.session_state.mcp_server_address = mcp_server_address

  if "connected" not in st.session_state:
    st.session_state.connected = False

  connect_button_label = "Connect" if not st.session_state.connected else "Disconnect"
  connect_button_color = "primary" if not st.session_state.connected else "secondary"
  if st.button(connect_button_label, use_container_width=True, type=connect_button_color):
    if not st.session_state.connected:
      st.session_state.event_loop.run_until_complete(
          setup_session(mcp_server_address))
      st.session_state.connected = True
      st.success("✅ Connected to MCP server.")
      st.session_state.session_initialized = True
      st.rerun()
    else:
      st.session_state.event_loop.run_until_complete(close_mcp_client())
      st.session_state.connected = False
      st.session_state.session_initialized = False
      st.session_state.tools = []
      st.success("✅ Disconnected from MCP server.")
      st.rerun()

  st.divider()
with st.sidebar:
  st.subheader("⚙️ Chat Settings")

  has_azure_openai = (
      os.getenv("AZURE_OPENAI_API_KEY")
      and os.getenv("AZURE_OPENAI_ENDPOINT")
      and os.getenv("AZURE_OPENAI_DEPLOYMENT")
  )

  if not has_azure_openai or AzureChatOpenAI is None:
    st.warning(
        "⚠️ Azure OpenAI environment variables are not configured. Please add AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT to your .env file."
    )

  st.session_state.timeout_seconds = st.slider(
      "⏱️ Response generation time limit (seconds)",
      min_value=60,
      max_value=300,
      value=st.session_state.timeout_seconds,
      step=10,
      help="Set the maximum time for the agent to generate a response. Complex tasks may require more time.",
  )

  st.session_state.recursion_limit = st.slider(
      "⏱️ Recursion call limit (count)",
      min_value=10,
      max_value=200,
      value=st.session_state.recursion_limit,
      step=10,
      help="Set the recursion call limit. Setting too high a value may cause memory issues.",
  )

  if st.button("Reset Conversation", use_container_width=True, type="primary"):
    st.session_state.thread_id = uuid.uuid4()
    st.session_state.history = []
    st.success("✅ Conversation has been reset.")
    st.rerun()

if not st.session_state.session_initialized:
  st.info(
      "MCP server and agent are not initialized. Please initialize the session."
  )

render_history()

user_query = st.chat_input("💬 Enter your question")
if user_query:
  if st.session_state.session_initialized:
    st.chat_message("user", avatar="🧑‍💻").markdown(user_query)
    with st.chat_message("assistant", avatar="🤖"):
      tool_placeholder = st.empty()
      text_placeholder = st.empty()
      resp, final_text, final_tool = (
          st.session_state.event_loop.run_until_complete(
              handle_query(
                  user_query,
                  text_placeholder,
                  tool_placeholder,
                  st.session_state.timeout_seconds,
              )
          )
      )
    if "error" in resp:
      st.error(resp["error"])
    else:
      st.session_state.history.append({"role": "user", "content": user_query})
      st.session_state.history.append(
          {"role": "assistant", "content": final_text}
      )
      if final_tool.strip():
        st.session_state.history.append(
            {"role": "assistant_tool", "content": final_tool}
        )
      st.rerun()
  else:
    st.warning(
        "⚠️ MCP server and agent are not initialized. Please initialize the session."
    )
