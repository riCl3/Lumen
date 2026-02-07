"""
Configuration management for MCP Scanner.

Defines risk categories, operations, and scoring thresholds for scanning.
"""

# -----------------------------------------------------------------------------
# Risk Categories
# -----------------------------------------------------------------------------

# Modules that are considered risky if imported
DANGEROUS_IMPORTS = [
    "os",           # Operating system interfaces
    "subprocess",   # Subprocess management
]

# Dynamic execution functions
DYNAMIC_EXECUTION = [
    "eval",         # Dynamic evaluation
    "exec",         # Dynamic execution
    "__import__"    # Dynamic importing
]

# Functions that modify or access the filesystem
FILE_OPERATIONS = [
    "open",     # Opening files
    "write",    # Writing to files
    "read",     # Reading from files
    "remove",   # Deleting files
    "rmdir"     # Removing directories
]

# Functions involved in network communication
NETWORK_OPERATIONS = [
    "requests", # HTTP requests lib
    "urllib",   # URL handling module
    "socket",   # Low-level networking
    "http"      # HTTP protocol client
]

# -----------------------------------------------------------------------------
# Scoring System
# -----------------------------------------------------------------------------

# Points assigned for each occurrence or usage of a risky item
RISK_WEIGHTS = {
    "DANGEROUS_IMPORTS": 20,  # High risk: Importing system modules
    "FILE_OPERATIONS": 15,    # Medium-High risk: File system interaction
    "NETWORK_OPERATIONS": 15, # Medium-High risk: Network usage
    "DYNAMIC_EXECUTION": 10   # Medium risk: Dynamic code execution
}

# -----------------------------------------------------------------------------
# Risk Levels
# -----------------------------------------------------------------------------

# Thresholds for classifying the overall risk score
# Format: (min_score, max_score)
RISK_LEVELS = {
    "SAFE": (0, 30),
    "MEDIUM": (31, 60),
    "HIGH": (61, 100)
}
