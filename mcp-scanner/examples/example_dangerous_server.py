"""
Example of a dangerous MCP server using system calls.
"""
import os
import subprocess
from mcp.server import Server

server = Server("danger-demo")

@server.tool()
def execute_system_command(cmd: str) -> str:
    """
    Executes a shell command. 
    WARNING: High risk!
    """
    os.system(cmd)
    return "Executed"

@server.tool()
def run_subprocess(cmd: str):
    """Runs a subprocess."""
    subprocess.call(cmd, shell=True)
