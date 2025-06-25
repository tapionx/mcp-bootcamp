"""
Simple MCP server using Django 

uv run gunicorn --config src/gunicorn.conf.py src.mcp_server_django:application
"""
import sys

import django
from django.conf import settings
from django.core.wsgi import get_wsgi_application
from django.http import JsonResponse
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .mcp_server_stdlib import MCPServer

# Minimal Django settings
settings.configure(
    DEBUG=True,
    SECRET_KEY="minimal-mcp-server-key",
    ROOT_URLCONF=__name__,
    ALLOWED_HOSTS=["*"],
    USE_TZ=True,
)

django.setup()

# Create MCP server instance
mcp_server = MCPServer()


# MCP Server implementation
@csrf_exempt
@require_http_methods(["POST"])
def mcp_endpoint(request):
    """Single MCP server endpoint handling all MCP protocol messages"""
    raw_data = request.body.decode('utf-8')
    response = mcp_server.handle_raw_request(raw_data)
    
    # Return empty response for notifications
    if not response:
        return JsonResponse({})
        
    return JsonResponse(response)


# URL configuration
urlpatterns = [
    path("mcp/", mcp_endpoint, name="mcp_endpoint"),
]

# WSGI application
application = get_wsgi_application()

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
