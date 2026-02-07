"""
Example of a safe MCP server with no dangerous patterns.
"""
from mcp.server import Server

# Initialize server
server = Server("safe-demo")

@server.tool()
def calculate_sum(a: int, b: int) -> int:
    """Calculates the sum of two numbers."""
    return a + b

@server.tool()
def echo_message(msg: str) -> str:
    """Returns the message back to the user."""
    return f"Echo: {msg}"
