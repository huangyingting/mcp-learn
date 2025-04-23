from atomic_agents.lib.factories.mcp_tool_factory import fetch_mcp_tools
from rich.console import Console
from rich.table import Table
import openai
import os
import instructor
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory
from typing import Union, Type, Dict
from dataclasses import dataclass
from dotenv import load_dotenv
import os

load_dotenv()

@dataclass
class MCPConfig:
  """Configuration for the MCP Agent system using SSE transport."""
  mcp_server_url: str = "http://localhost:8000"


config = MCPConfig()
console = Console()
client = instructor.from_openai(
    openai.AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )
)


class FinalResponseSchema(BaseIOSchema):
  """Schema for providing a final text response to the user."""
  response_text: str = Field(...,
                             description="The final text response to the user's query")


tools = fetch_mcp_tools(
    mcp_endpoint=config.mcp_server_url,
    use_stdio=False,
)
if not tools:
  raise RuntimeError(
      "No MCP tools found. Please ensure the MCP server is running and accessible.")

tool_schema_to_class_map: Dict[Type[BaseIOSchema], Type[BaseAgent]] = {
    ToolClass.input_schema: ToolClass for ToolClass in tools if hasattr(ToolClass, "input_schema")
}
tool_input_schemas = tuple(tool_schema_to_class_map.keys())
available_schemas = tool_input_schemas + (FinalResponseSchema,)
ActionUnion = Union[available_schemas]
class MCPOrchestratorInputSchema(BaseIOSchema):
  """Input schema for the MCP Orchestrator Agent."""

  query: str = Field(..., description="The user's query to analyze.")


class OrchestratorOutputSchema(BaseIOSchema):
  """Output schema for the orchestrator. Contains reasoning and the chosen action."""

  reasoning: str = Field(
      ..., description="Detailed explanation of why this action was chosen and how it will address the user's query."
  )
  action: ActionUnion = Field(  # type: ignore[reportInvalidTypeForm]
      ..., description="The chosen action: either a tool's input schema instance or a final response schema instance."
  )

def main():
  try:
    console.print(
        "[bold green]Initializing MCP Agent System (SSE mode)...[/bold green]")
    table = Table(title="Available MCP Tools", box=None)
    table.add_column("Tool Name", style="cyan")
    table.add_column("Input Schema", style="yellow")
    table.add_column("Description", style="magenta")
    for ToolClass in tools:
      schema_name = ToolClass.input_schema.__name__ if hasattr(
          ToolClass, "input_schema") else "N/A"
      table.add_row(ToolClass.mcp_tool_name,
                    schema_name, ToolClass.__doc__ or "")
    console.print(table)
    console.print("[dim]• Creating orchestrator agent...[/dim]")
    memory = AgentMemory()
    orchestrator_agent = BaseAgent(
        BaseAgentConfig(
            client=client,
            model=config.openai_model,
            memory=memory,
            system_prompt_generator=SystemPromptGenerator(
                background=[
                    "You are an MCP Orchestrator Agent, designed to chat with users and",
                    "determine the best way to handle their queries using the available tools.",
                ],
                steps=[
                    "1. Use the reasoning field to determine if one or more successive tool calls could be used to handle the user's query.",
                    "2. If so, choose the appropriate tool(s) one at a time and extract all necessary parameters from the query.",
                    "3. If a single tool can not be used to handle the user's query, think about how to break down the query into "
                    "smaller tasks and route them to the appropriate tool(s).",
                    "4. If no sequence of tools could be used, or if you are finished processing the user's query, provide a final "
                    "response to the user.",
                ],
                output_instructions=[
                    "1. Always provide a detailed explanation of your decision-making process in the 'reasoning' field.",
                    "2. Choose exactly one action schema (either a tool input or FinalResponseSchema).",
                    "3. Ensure all required parameters for the chosen tool are properly extracted and validated.",
                    "4. Maintain a professional and helpful tone in all responses.",
                    "5. Break down complex queries into sequential tool calls before giving the final answer via `FinalResponseSchema`.",
                ],
            ),
            input_schema=MCPOrchestratorInputSchema,
            output_schema=OrchestratorOutputSchema,
        )
    )
    console.print("[green]Successfully created orchestrator agent.[/green]")
    console.print(
        "[bold green]MCP Agent Interactive Chat (SSE mode). Type 'exit' or 'quit' to leave.[/bold green]")
    while True:
      query = console.input("[bold yellow]You:[/bold yellow] ").strip()
      if query.lower() in {"exit", "quit"}:
        console.print("[bold red]Exiting chat. Goodbye![/bold red]")
        break
      if not query:
        continue
      try:
        orchestrator_output = orchestrator_agent.run(
            MCPOrchestratorInputSchema(query=query))
        action_instance = orchestrator_output.action
        reasoning = orchestrator_output.reasoning
        console.print(f"[cyan]Orchestrator reasoning:[/cyan] {reasoning}")

        while not isinstance(action_instance, FinalResponseSchema):
          schema_type = type(action_instance)
          ToolClass = tool_schema_to_class_map.get(schema_type)
          if not ToolClass:
            raise ValueError(
                f"Unknown schema type '" f"{schema_type.__name__}" f"' returned by orchestrator")

          tool_name = ToolClass.mcp_tool_name
          console.print(f"[blue]Executing tool:[/blue] {tool_name}")
          console.print(
              f"[dim]Parameters:[/dim] " f"{action_instance.model_dump()}")

          tool_instance = ToolClass()
          tool_output = tool_instance.run(action_instance)
          console.print(
              f"[bold green]Result:[/bold green] {tool_output.result}")

          result_message = MCPOrchestratorInputSchema(
              query=(
                  f"Tool {tool_name} executed with result: " f"{tool_output.result}")
          )
          orchestrator_agent.memory.add_message("system", result_message)

          orchestrator_output = orchestrator_agent.run()
          action_instance = orchestrator_output.action
          reasoning = orchestrator_output.reasoning
          console.print(f"[cyan]Orchestrator reasoning:[/cyan] {reasoning}")

        console.print(
            f"[bold blue]Agent:[/bold blue] {action_instance.response_text}")

      except Exception as e:
        console.print(f"[red]Error processing query:[/red] {str(e)}")
        console.print_exception()
  except Exception as e:
    console.print(f"[bold red]Fatal error:[/bold red] {str(e)}")
    console.print_exception()


if __name__ == "__main__":
  main()
