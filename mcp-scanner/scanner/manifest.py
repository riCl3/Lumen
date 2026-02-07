"""
Manifest module for handling MCP manifest files.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ManifestGenerator:
    """
    Generates and manages the MCP manifest file.
    """

    def __init__(self):
        """Initialize empty manifest structure."""
        self.servers = []
        self.stats = {
            "safe_count": 0,
            "medium_count": 0,
            "high_count": 0
        }

    def add_server_analysis(self, server_info: Dict[str, Any], analysis_results: Dict[str, Any]):
        """
        Combines discovery + analysis data.
        
        Args:
            server_info: dict from discovery (path, type, metadata)
            analysis_results: dict from static analyzer (risk analysis)
        """
        # Merge the data
        server_entry = {
            "name": server_info.get("metadata", {}).get("name", "Unknown"),
            "path": server_info.get("path"),
            "type": server_info.get("type"),
            "description": server_info.get("metadata", {}).get("description"),
            "risk_analysis": analysis_results
        }
        
        self.servers.append(server_entry)
        
        # Update stats
        risk_level = analysis_results.get("risk_level", "UNKNOWN")
        if risk_level == "SAFE":
            self.stats["safe_count"] += 1
        elif risk_level == "MEDIUM":
            self.stats["medium_count"] += 1
        elif risk_level == "HIGH":
            self.stats["high_count"] += 1

    def compile_findings(self):
        """
        Aggregates all server data. 
        """
        # Data is aggregated incrementally in add_server_analysis
        pass

    def generate_manifest(self) -> Dict[str, Any]:
        """
        Creates final JSON structure.
        
        Returns:
            Dictionary containing the complete manifest
        """
        return {
            "scan_date": datetime.now(timezone.utc).isoformat(),
            "total_servers_found": len(self.servers),
            "summary_statistics": self.stats,
            "servers": self.servers
        }

    def save_to_file(self, output_path: str):
        """
        Writes JSON to disk with pretty formatting.
        
        Args:
            output_path: Destination path for the JSON file
        """
        try:
            manifest_data = self.generate_manifest()
            path = Path(output_path)
            
            # Ensure parent exists
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2)
                
            logger.info(f"Manifest saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save manifest to {output_path}: {e}")
            raise

    def get_summary(self) -> str:
        """
        Returns quick text summary for CLI display.
        """
        manifest = self.generate_manifest()
        stats = manifest["summary_statistics"]
        
        summary = [
            f"Scan Complete: {manifest['scan_date']}",
            f"Total Servers/Tools Found: {manifest['total_servers_found']}",
            "-" * 20,
            f"Risk Summary:",
            f"  SAFE:   {stats['safe_count']}",
            f"  MEDIUM: {stats['medium_count']}",
            f"  HIGH:   {stats['high_count']}",
            "-" * 20
        ]
        return "\n".join(summary)
