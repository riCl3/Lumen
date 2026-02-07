"""
Formatter module for nicely formatted CLI and JSON output.
"""
import json
from typing import Dict, Any, List
from colorama import init, Fore, Style

# Initialize colorama
init(autoreset=True)

class Formatter:
    """
    Handles formatting of scan results for various outputs.
    """

    @staticmethod
    def _get_color(risk_level: str) -> str:
        """Helper to get color code for risk level."""
        if risk_level == "SAFE":
            return Fore.GREEN
        elif risk_level == "MEDIUM":
            return Fore.YELLOW
        elif risk_level == "HIGH":
            return Fore.RED
        return Fore.WHITE

    @staticmethod
    def format_console_output(manifest: Dict[str, Any]) -> str:
        """
        Creates a readable CLI summary table.
        
        Args:
            manifest: The complete scan result dictionary
            
        Returns:
            Formatted string for console output
        """
        lines = []
        scan_date = manifest.get("scan_date", "Unknown")
        
        # Header
        lines.append(f"\n{Style.BRIGHT}MCP SCAN REPORT{Style.RESET_ALL} ({scan_date})")
        lines.append("=" * 80)
        
        # Table Header
        # Columns: Server Name (30) | Risk (10) | Score (8) | Patterns (8)
        header = f"{'Server Name':<30} | {'Risk':<10} | {'Score':<8} | {'Patterns':<8}"
        lines.append(f"{Style.BRIGHT}{header}{Style.RESET_ALL}")
        lines.append("-" * 80)
        
        servers = manifest.get("servers", [])
        if not servers:
            lines.append("No servers found.")
        else:
            for server in servers:
                name = server.get("name", "Unknown")[:29] # Truncate if too long
                risk_data = server.get("risk_analysis", {})
                level = risk_data.get("risk_level", "UNKNOWN")
                score = risk_data.get("risk_score", 0)
                pattern_count = len(risk_data.get("breakdown", []))
                
                color = Formatter._get_color(level)
                
                row = f"{name:<30} | {color}{level:<10}{Style.RESET_ALL} | {score:<8} | {pattern_count:<8}"
                lines.append(row)
                
        lines.append("-" * 80)
        
        # Summary Stats
        stats = manifest.get("summary_statistics", {})
        lines.append(f"{Style.BRIGHT}Summary:{Style.RESET_ALL}")
        lines.append(f"  Total Servers: {manifest.get('total_servers_found', 0)}")
        lines.append(f"  {Fore.GREEN}SAFE:   {stats.get('safe_count', 0)}{Style.RESET_ALL}")
        lines.append(f"  {Fore.YELLOW}MEDIUM: {stats.get('medium_count', 0)}{Style.RESET_ALL}")
        lines.append(f"  {Fore.RED}HIGH:   {stats.get('high_count', 0)}{Style.RESET_ALL}")
        lines.append("=" * 80)
        
        return "\n".join(lines)

    @staticmethod
    def format_json_output(manifest: Dict[str, Any]) -> str:
        """
        Ensures consistent JSON structure formatting.
        """
        return json.dumps(manifest, indent=2, sort_keys=True)

    @staticmethod
    def format_server_details(server_data: Dict[str, Any]) -> str:
        """
        Detailed single-server view with all patterns and file info.
        """
        lines = []
        name = server_data.get("name", "Unknown")
        path = server_data.get("path", "Unknown")
        risk_data = server_data.get("risk_analysis", {})
        level = risk_data.get("risk_level", "UNKNOWN")
        score = risk_data.get("risk_score", 0)
        breakdown = risk_data.get("breakdown", [])
        
        color = Formatter._get_color(level)
        
        lines.append(f"\n{Style.BRIGHT}Server Details: {name}{Style.RESET_ALL}")
        lines.append(f"File: {path}")
        lines.append(f"Risk Level: {color}{level}{Style.RESET_ALL} (Score: {score})")
        
        if breakdown:
            lines.append(f"\n{Style.BRIGHT}Dangerous Patterns Detected:{Style.RESET_ALL}")
            for item in breakdown:
                category = item.get("category", "UNKNOWN")
                desc = item.get("description", "")
                line = item.get("line", 0)
                item_score = item.get("score", 0)
                
                lines.append(f"  {Fore.RED}x{Style.RESET_ALL} Line {line:<4} [{category}] {desc} ({item_score} pts)")
                
            # Basic recommendations based on categories found
            lines.append(f"\n{Style.BRIGHT}Recommendations:{Style.RESET_ALL}")
            categories = {item.get("category") for item in breakdown}
            if "DANGEROUS_IMPORTS" in categories:
                lines.append("  - Review use of system modules (os, subprocess). Use safer alternatives if possible.")
            if "DYNAMIC_EXECUTION" in categories:
                lines.append("  - Avoid dynamic execution (eval, exec) as it poses severe security risks.")
            if "NETWORK_OPERATIONS" in categories:
                lines.append("  - Verify that network calls are restricted to trusted endpoints.")
            if "FILE_OPERATIONS" in categories:
                lines.append("  - Ensure file operations do not allow arbitrary path access.")
        else:
            lines.append(f"\n{Fore.GREEN}No dangerous patterns detected.{Style.RESET_ALL}")
            
        lines.append("-" * 60)
        return "\n".join(lines)
