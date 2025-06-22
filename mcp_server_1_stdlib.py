"""
Simple MCP server using standard library.

Server features:
    TOOLS: "how many days are left until Christmas?"
    RESOURCES: add "current time" as a resource and ask "is it time to go to sleep?"
    PROMPTS: /mcp.<name>.quote-of-the-day

Client features:
    ROOTS: check logs for the Client response to the roots/list request
    SAMPLING: the Server needs an LLM to generate a response (#TODO)

Not yet supported by VSCode:
    ELICITATION: ask Client for parameters
"""

import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict

# Set up logging to stderr (stdout is reserved for MCP communication)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


class MCPServer:

    def handle_request(self, request: Dict) -> Dict:
        method = request.get("method")
        params = request.get("params", {})

        # Handle notifications (no response required)
        if request.get("id") is None:
            self.handle_notification(method, params)
            return {}  # No response for notifications

        if request.get("id") == "roots_request_1":
            return {}
        if method == "initialize":
            return self.handle_initialize(params)
        elif method == "resources/list":
            return self.handle_resources_list()
        elif method == "resources/read":
            return self.handle_resources_read(params)
        elif method == "tools/list":
            return self.handle_tools_list()
        elif method == "tools/call":
            return self.handle_tools_call(params)
        elif method == "prompts/list":
            return self.handle_prompts_list()
        elif method == "prompts/get":
            return self.handle_prompts_get(params)
        else:
            return {"error": f"Unknown method: {method}"}

    def handle_notification(self, method: str, params: Dict) -> None:
        # for demo purposes, we send Client a request to list roots
        roots_request = {
            "jsonrpc": "2.0",
            "id": "roots_request_1",
            "method": "roots/list",
            "params": {}
        }        
        print(json.dumps(roots_request), flush=True)

    def handle_initialize(self, params: Dict) -> Dict:
        return {
            "protocolVersion": "2025-03-26",
            "capabilities": {
                "resources": {},
                "tools": {},
                "prompts": {},
                "roots": {"listChanged": True},
            },
            "serverInfo": {"name": "minimal-mcp", "version": "1.0.0"},
        }

    def handle_resources_list(self) -> Dict:
        return {
            "resources": [
                {
                    "uri": "time://current",
                    "name": "Current Time",
                    "description": "Current date and time",
                    "mimeType": "application/json",
                }
            ]
        }

    def handle_resources_read(self, params: Dict) -> Dict:
        uri = params.get("uri")

        if uri == "time://current":
            now = datetime.now()
            time_data = {
                "current_time": now.isoformat(),
                "timestamp": int(now.timestamp()),
                "readable": now.strftime("%Y-%m-%d %H:%M:%S"),
            }
            content = json.dumps(time_data, indent=2)
        else:
            return {"error": f"Unknown resource URI: {uri}"}

        return {
            "contents": [{"uri": uri, "mimeType": "application/json", "text": content}]
        }

    def handle_tools_list(self) -> Dict:
        return {
            "tools": [
                {
                    "name": "days_between",
                    "description": "Calculate the number of days between two dates",
                    "inputSchema": {
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
                }
            ]
        }

    def handle_tools_call(self, params: Dict) -> Dict:
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name == "days_between":
            start_date_str = arguments.get("start_date", "")
            end_date_str = arguments.get("end_date", "")

            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

                difference = end_date - start_date
                days = difference.days
                result = f"There are {days} days between {start_date_str} and {end_date_str}."
            except ValueError as e:
                result = (
                    f"Error parsing dates. Please use YYYY-MM-DD format. Error: {e}"
                )

            return {"content": [{"type": "text", "text": result}]}
        else:
            return {"error": f"Unknown tool: {tool_name}"}

    def handle_prompts_list(self) -> Dict:
        return {
            "prompts": [
                {
                    "name": "quote-of-the-day",
                    "description": "Generate a quote of the day impersonating a character from a movie",
                    "arguments": [
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
                }
            ]
        }

    def handle_prompts_get(self, params: Dict) -> Dict:
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})

        if prompt_name == "quote-of-the-day":
            movie = arguments.get("movie", "Unknown Movie")
            character = arguments.get("character", "Unknown Character")
            prompt_text = f"Print a short and inspiring quote from {movie} by {character}. Don't add anything else."

            return {
                "description": "Quote of the day prompt",
                "messages": [
                    {"role": "user", "content": {"type": "text", "text": prompt_text}}
                ],
            }
        else:
            return {"error": f"Unknown prompt: {prompt_name}"}

    def handle_roots_list(self) -> Dict:
        return {
            "roots": [{"uri": f"file://{os.getcwd()}", "name": "Current Directory"}]
        }


def run_stdio_server():
    server = MCPServer()
    logger.info("Starting MCP server")
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            try:
                request = json.loads(line.strip())
                # VSCode already logs requests and responses
                # logger.debug(f"REQUEST <<< {request}")
                result = server.handle_request(request)
                if not result:
                    continue  # Skip empty responses (notifications)
                response = {"jsonrpc": "2.0", "result": result}
                if "id" in request:
                    response["id"] = request["id"]

                print(json.dumps(response), flush=True)
                # logger.debug(f"RESPONSE >>> {response}")

            except json.JSONDecodeError as e:
                error_response = {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                    "id": None,
                }
                print(json.dumps(error_response), flush=True)
                logger.error(f"Invalid JSON received: {e}")

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    run_stdio_server()
