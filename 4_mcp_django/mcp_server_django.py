import json
import sys

import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# Minimal Django settings
settings.configure(
    DEBUG=True,
    SECRET_KEY="minimal-mcp-server-key",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
    USE_TZ=True,
)

django.setup()


# MCP Server implementation
@csrf_exempt
@require_http_methods(["POST"])
def mcp_endpoint(request):
    """Single MCP server endpoint handling all MCP protocol messages"""
    try:
        data = json.loads(request.body)
        method = data.get("method")

        if method == "initialize":
            return JsonResponse(
                {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "minimal-django-mcp", "version": "1.0.0"},
                    },
                }
            )

        elif method == "tools/list":
            return JsonResponse(
                {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "hello",
                                "description": "Says hello",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "Name to greet"}
                                    },
                                },
                            }
                        ]
                    },
                }
            )

        elif method == "tools/call":
            tool_name = data.get("params", {}).get("name")
            if tool_name == "hello":
                name = data.get("params", {}).get("arguments", {}).get("name", "World")
                return JsonResponse(
                    {
                        "jsonrpc": "2.0",
                        "id": data.get("id"),
                        "result": {"content": [{"type": "text", "text": f"Hello, {name}!"}]},
                    }
                )

        # Default response for unsupported methods
        return JsonResponse(
            {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "error": {"code": -32601, "message": "Method not found"},
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}})
    except Exception as e:
        return JsonResponse(
            {"jsonrpc": "2.0", "error": {"code": -32603, "message": f"Internal error: {str(e)}"}}
        )


# URL configuration
urlpatterns = [
    path("mcp/", mcp_endpoint, name="mcp_endpoint"),
]

# WSGI application
application = get_wsgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
