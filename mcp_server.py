"""
a simple implementation of a MCP server without the ufficial mcp library
You can use it inside VSCode following this guide:
https://code.visualstudio.com/docs/copilot/chat/mcp-servers
"""

import json
import sys
import logging
from typing import Dict, Any, List, Optional


# Set up logging to stderr (stdout is reserved for MCP communication)
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stderr
)
logger = logging.getLogger(__name__)


class SimpleMCPServer:
    def __init__(self):
        self.server_name = "simple-mcp-server"
        self.server_version = "1.0.0"
        self.capabilities = {"tools": {}}

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle incoming JSON-RPC request"""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            logger.debug(f"Handling method: {method}")

            if method == "initialize":
                return self.initialize(params, request_id)
            elif method == "tools/list":
                return self.list_tools(params, request_id)
            elif method == "tools/call":
                return self.call_tool(params, request_id)
            else:
                return self.error_response(request_id, -32601, f"Method not found: {method}")

        except Exception as e:
            logger.error(f"Error handling request: {e}")
            return self.error_response(request.get("id"), -32603, str(e))

    def initialize(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Handle MCP initialize request"""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": self.capabilities,
                "serverInfo": {"name": self.server_name, "version": self.server_version},
            },
        }

    def list_tools(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """List available tools"""
        tools = [
            {
                "name": "echo",
                "description": "Echo back the input text",
                "inputSchema": {
                    "type": "object",
                    "properties": {"text": {"type": "string", "description": "Text to echo back"}},
                    "required": ["text"],
                },
            },
            {
                "name": "calculator",
                "description": "Perform basic arithmetic operations",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "enum": ["add", "subtract", "multiply", "divide"],
                            "description": "The arithmetic operation to perform",
                        },
                        "a": {"type": "number", "description": "First number"},
                        "b": {"type": "number", "description": "Second number"},
                    },
                    "required": ["operation", "a", "b"],
                },
            },
        ]

        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}

    def call_tool(self, params: Dict[str, Any], request_id: Any) -> Dict[str, Any]:
        """Execute a tool call"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "echo":
                result = self.tool_echo(arguments)
            elif tool_name == "calculator":
                result = self.tool_calculator(arguments)
            else:
                return self.error_response(request_id, -32602, f"Unknown tool: {tool_name}")

            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": result}]},
            }

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return self.error_response(request_id, -32603, f"Tool execution error: {str(e)}")

    def tool_echo(self, arguments: Dict[str, Any]) -> str:
        """Echo tool implementation"""
        text = arguments.get("text", "")
        return f"Echo: {text}"

    def tool_calculator(self, arguments: Dict[str, Any]) -> str:
        """Calculator tool implementation"""
        operation = arguments.get("operation")
        a = arguments.get("a")
        b = arguments.get("b")

        if operation == "add":
            result = a + b
        elif operation == "subtract":
            result = a - b
        elif operation == "multiply":
            result = a * b
        elif operation == "divide":
            if b == 0:
                raise ValueError("Division by zero")
            result = a / b
        else:
            raise ValueError(f"Unknown operation: {operation}")

        return f"Result: {a} {operation} {b} = {result}"

    def error_response(self, request_id: Any, code: int, message: str) -> Dict[str, Any]:
        """Create JSON-RPC error response"""
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}

    def run(self):
        """Main server loop"""
        logger.info(f"Starting {self.server_name} v{self.server_version}")

        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue

                try:
                    request = json.loads(line)
                    logger.debug(f"Received request: {request}")

                    response = self.handle_request(request)
                    if response:
                        response_json = json.dumps(response)
                        print(response_json, flush=True)
                        logger.debug(f"Sent response: {response_json}")

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    error_resp = self.error_response(None, -32700, "Parse error")
                    print(json.dumps(error_resp), flush=True)

        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
        except Exception as e:
            logger.error(f"Server error: {e}")
            raise


if __name__ == "__main__":
    server = SimpleMCPServer()
    server.run()
