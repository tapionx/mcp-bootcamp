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
        """Handle MCP request and return raw result (no JSON-RPC wrapper)"""
        method = request.get("method")
        params = request.get("params", {})

        # no ID -> it's a "notification"
        if request.get("id") is None:
            return self.ask_roots(method, params)

        if request.get("id") == "42":
            # we are cheating here, MCP should be stateful
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

    def handle_request_with_response(self, request: Dict) -> Dict:
        """Handle MCP request and return full JSON-RPC response"""
        try:
            result = self.handle_request(request)
            if not result:
                return {}  # Skip empty responses (notifications)

            if "id" in result:
                return result
            response = {"jsonrpc": "2.0", "result": result}
            if "id" in request:
                response["id"] = request["id"]
            return response
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": request.get("id"),
            }
            return error_response

    def send_notification_to_client(self, method: str, params: Dict) -> None:
        """Send notification to client via stdio (only for stdio server)"""

    def ask_roots(self, method: str, params: Dict) -> None:
        return {
            "jsonrpc": "2.0",
            "id": "42",
            "method": "roots/list",
            "params": {},
        }

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

        return {"contents": [{"uri": uri, "mimeType": "application/json", "text": content}]}

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
                result = f"Error parsing dates. Please use YYYY-MM-DD format. Error: {e}"

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
                "messages": [{"role": "user", "content": {"type": "text", "text": prompt_text}}],
            }
        else:
            return {"error": f"Unknown prompt: {prompt_name}"}

    def handle_roots_list(self) -> Dict:
        return {"roots": [{"uri": f"file://{os.getcwd()}", "name": "Current Directory"}]}

    def handle_raw_request(self, raw_data: str) -> Dict:
        """Handle raw JSON string request and return full JSON-RPC response with all error handling"""
        try:
            request = json.loads(raw_data)
            return self.handle_request_with_response(request)
        except json.JSONDecodeError:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
                "id": None,
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": None,
            }


def run_stdio_server():
    server = MCPServer()
    logger.info("Starting MCP server")
    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break

            response = server.handle_raw_request(line.strip())
            if response:  # Only print non-empty responses
                print(json.dumps(response), flush=True)

    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    run_stdio_server()
