"""
Quick test to verify LLM + Scanner integration works
"""
import sys
from scanner import ScannerPipeline

# Test scanning the scanner directory itself
pipeline = ScannerPipeline()

print("=" * 60)
print("Testing LLM-based code analysis...")
print("=" * 60)

# Scan a small directory (the scanner package itself)
test_dir = "scanner"
output_file = "test_scan_results.json"

print(f"\nScanning directory: {test_dir}")
print(f"Output file: {output_file}\n")

try:
    summary = pipeline.run_scan(test_dir, output_file)
    print("\n" + "=" * 60)
    print("SCAN COMPLETE!")
    print("=" * 60)
    print(summary)
    print("\nCheck test_scan_results.json for detailed results.")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
