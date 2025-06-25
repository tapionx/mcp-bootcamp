"""
Simple MCP server using Anthropic's MCP library.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptMessage,
    Resource,
    TextContent,
    Tool,
)

# Set up logging to stderr (stdout is reserved for MCP communication)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

# Create the server instance
server = Server("minimal-mcp")


@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="time://current",
            name="Current Time",
            description="Current date and time",
            mimeType="application/json",
        )
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a specific resource."""
    if uri == "time://current":
        now = datetime.now()
        time_data = {
            "current_time": now.isoformat(),
            "timestamp": int(now.timestamp()),
            "readable": now.strftime("%Y-%m-%d %H:%M:%S"),
        }
        return json.dumps(time_data, indent=2)
    else:
        raise ValueError(f"Unknown resource URI: {uri}")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="days_between",
            description="Calculate the number of days between two dates",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format",
                    },
                },
                "required": ["start_date", "end_date"],
            },
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "days_between":
        start_date_str = arguments.get("start_date", "")
        end_date_str = arguments.get("end_date", "")

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

            difference = end_date - start_date
            days = difference.days
            result = f"There are {days} days between {start_date_str} and {end_date_str}."
        except ValueError as e:
            result = f"Error parsing dates. Please use YYYY-MM-DD format. Error: {e}"

        return [TextContent(type="text", text=result)]
    else:
        raise ValueError(f"Unknown tool: {name}")


@server.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available prompts."""
    return [
        Prompt(
            name="quote-of-the-day",
            description="Generate a quote of the day impersonating a character from a movie",
            arguments=[
                {
                    "name": "movie",
                    "description": "Name of the movie to quote from",
                    "required": True,
                },
                {
                    "name": "character",
                    "description": "Name of the character to impersonate",
                    "required": True,
                },
            ],
        )
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict) -> GetPromptResult:
    """Get a specific prompt."""
    if name == "quote-of-the-day":
        movie = arguments.get("movie", "Unknown Movie")
        character = arguments.get("character", "Unknown Character")
        prompt_text = f"Print a short and inspiring quote from {movie} by {character}. Don't add anything else."

        return GetPromptResult(
            description="Quote of the day prompt",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=prompt_text),
                )
            ],
        )
    else:
        raise ValueError(f"Unknown prompt: {name}")


async def main():
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
