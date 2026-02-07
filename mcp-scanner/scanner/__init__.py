"""
MCP Scanner Package Initialization.

Exports main components and provides a high-level pipeline class.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from .discovery import FileScanner
from .analyzer import StaticAnalyzer
from .manifest import ManifestGenerator
from .llm import LLMAnalyzer

# Set up logging if not already configured
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger(__name__)

class ScannerPipeline:
    """
    Orchestrates the full MCP scanning workflow.
    """

    def __init__(self):
        """Initialize pipeline components."""
        self.scanner = FileScanner()
        self.analyzer = StaticAnalyzer()
        self.llm_analyzer = LLMAnalyzer()
        self.manifest_gen = ManifestGenerator()

    def run_scan(self, directory_path: str, output_file: str) -> str:
        """
        Runs the complete scan pipeline.

        Args:
            directory_path: Root directory to scan
            output_file: Path to save the JSON manifest

        Returns:
            Summary string of the scan results
        """
        try:
            root_path = Path(directory_path)
            if not root_path.exists():
                logger.error(f"Directory not found: {directory_path}")
                return "Error: Directory not found."

            logger.info(f"Starting scan of {root_path}")

            # 1. Discovery - Use comprehensive file discovery
            discovered_items = self.scanner.discover_all_files(directory_path, max_files=50)
            
            if not discovered_items:
                logger.warning("No source files found.")
                # Still generate manifest to record the scan
                self.manifest_gen.save_to_file(output_file)
                return "Scan complete. No source files found."

            logger.info(f"Discovered {len(discovered_items)} source files.")

            # 2. Analysis
            # Track which files we've already analyzed to prevent duplicates
            analyzed_paths = set()
            
            for item in discovered_items:
                try:
                    path_str = item.get("path")
                    if not path_str:
                         continue

                    file_path = Path(path_str)
                    if not file_path.exists():
                         logger.error(f"File not found during analysis: {path_str}")
                         continue

                    # Skip if we've already analyzed this path
                    if str(file_path) in analyzed_paths:
                        logger.warning(f"Skipping duplicate: {file_path}")
                        continue
                    
                    analyzed_paths.add(str(file_path))
                    
                    # Read content (try utf-8)
                    content = ""
                    try:
                        content = file_path.read_text(encoding='utf-8')
                    except UnicodeDecodeError:
                        logger.warning(f"Could not read {path_str} as text. Skipping analysis.")
                        continue
                    except Exception as e:
                        logger.warning(f"Could not read {file_path}: {e}")
                        continue

                    # Run LLM Analysis
                    logger.info(f"Running LLM analysis on {file_path.name}")
                    analysis = self.llm_analyzer.analyze_code(content, str(file_path))
                    
                    # Ensure risk_level is set based on risk_score if missing
                    if "risk_level" not in analysis or not analysis.get("risk_level"):
                        score = analysis.get("risk_score", 0)
                        if score == 0:
                            analysis["risk_level"] = "SAFE"
                        elif score <= 3:
                            analysis["risk_level"] = "LOW" 
                        elif score <= 6:
                            analysis["risk_level"] = "MEDIUM"
                        elif score <= 8:
                            analysis["risk_level"] = "HIGH"
                        else:
                            analysis["risk_level"] = "CRITICAL"
                    
                    self.manifest_gen.add_server_analysis(item, analysis)
                        
                except Exception as e:
                    logger.error(f"Error analyzing item {item.get('path', 'unknown')}: {e}")
                    # Capture error in manifest for this item if possible, or skip
                    # Adding a placeholder error entry to manifest
                    self.manifest_gen.add_server_analysis(item, {
                        "risk_score": 0,
                        "risk_level": "ERROR",
                        "breakdown": [{"description": f"Analysis failed: {str(e)}"}]
                    })

            # 3. Generate and Save Manifest
            self.manifest_gen.save_to_file(output_file)
            logger.info(f"Scan results saved to {output_file}")
            
            return self.manifest_gen.get_summary()

        except PermissionError:
            logger.error(f"Permission denied accessing {directory_path}")
            return "Error: Permission denied."
        except Exception as e:
            logger.exception(f"Unexpected error during scan pipeline: {e}")
            return f"Error: Scan failed - {str(e)}"

# Convenience export
__all__ = ['ScannerPipeline', 'FileScanner', 'StaticAnalyzer', 'ManifestGenerator']
