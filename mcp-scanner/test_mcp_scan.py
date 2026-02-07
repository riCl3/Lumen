"""
Test scanning the mcp-shodan directory
"""
import sys
import os
from scanner import ScannerPipeline

# Test scanning mcp-shodan
pipeline = ScannerPipeline()

print("=" * 60)
print("Testing LLM-based code analysis on MCP-Shodan...")
print("=" * 60)

# The path from the dashboard default
test_dir = r"D:\AlignProject\Hackathon\Lumen\mcp-shodan"
output_file = "test_mcp_scan.json"

if not os.path.exists(test_dir):
    print(f"ERROR: Directory not found: {test_dir}")
    print("Please update the path in this script.")
    sys.exit(1)

print(f"\nScanning directory: {test_dir}")
print(f"Output file: {output_file}\n")

try:
    summary = pipeline.run_scan(test_dir, output_file)
    print("\n" + "=" * 60)
    print("SCAN COMPLETE!")
    print("=" * 60)
    print(summary)
    print(f"\nCheck {output_file} for detailed LLM analysis results.")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
