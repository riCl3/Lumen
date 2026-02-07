# MCP Scanner

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A powerful security scanning tool for **Model Context Protocol (MCP)** servers. It automatically discovers MCP servers in your codebase, analyzes them for dangerous patterns (like system calls and network requests), and generates detailed risk reports.

## 🚀 Key Features

- **Auto-Discovery**: Recursively finds `@mcp.server` and `@mcp.tool` definitions.
- **Static Analysis**: Detects dangerous imports (`os`, `subprocess`) and risky operations (`eval`, `exec`).
- **Risk Scoring**: Assigns risk scores and categories (SAFE, MEDIUM, HIGH) to each server.
- **Detailed Reporting**: Generates JSON manifests and beautiful CLI reports.
- **Configurable**: Customize risk weights and patterns via `scanner/config.py`.

---

## 📦 Installation

This tool uses modern Python tooling (`uv` recommended) but works with standard pip.

### Using UV (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-scanner.git
cd mcp-scanner

# Initialize and sync dependencies
uv sync
```

### Using Pip

```bash
pip install -r requirements.txt
```

---

## 🛠️ Usage

### 1. Run a Scan

Scan a directory for MCP servers and vulnerabilities:

```bash
# Using UV
uv run python -m scanner.cli scan /path/to/your/project

# Standard Python
python -m scanner.cli scan /path/to/your/project
```

**Output:**

- `scan_results.json`: Detailed machine-readable report.
- Console output: Color-coded summary of findings.

### 2. View Reports

Display the last scan result in a human-readable format:

```bash
uv run python -m scanner.cli report
```

### 3. Custom Output

Specify a custom output file for the JSON report:

```bash
uv run python -m scanner.cli scan . -o my_report.json
```

---

## 📊 Risk Scoring System

The scanner assigns points based on detected patterns. The total score determines the **Risk Level**.

| Category | Points | Description |
|----------|--------|-------------|
| **Dangerous Imports** | +20 | Importing `os`, `subprocess`, etc. |
| **Network Ops** | +15 | Using `requests`, `urllib`, `socket`. |
| **File Ops** | +15 | Reading/Writing files (`open`, `write`). |
| **Dynamic Exec** | +10 | Using `eval()`, `exec()`, or `__import__`. |

**Risk Levels:**

- 🟢 **SAFE** (0-30 pts): No major risks detected.
- 🟡 **MEDIUM** (31-60 pts): Some potential risks (e.g., network calls).
- 🔴 **HIGH** (61+ pts): High-risk patterns found (system calls, shell execution).

---

## 🏗️ Architecture

```mermaid
graph TD
    User[User] --> CLI[CLI (cli.py)]
    CLI --> Pipeline[Scanner Pipeline]
    
    subgraph Core Components
        Pipeline --> Discovery[File Scanner]
        Pipeline --> Analyzer[Static Analyzer]
        Pipeline --> Manifest[Manifest Gen]
    end
    
    Discovery -->|Finds Files| Analyzer
    Analyzer -->|Risk Scores| Manifest
    Manifest -->|JSON| Output[scan_results.json]
    Output -->|Read by| Report[Report Viewer]
    
    subgraph Config
        Config[config.py] --> Analyzer
    end
```

---

## 📂 Project Structure

```text
mcp-scanner/
├── scanner/
│   ├── __init__.py      # Scanner Pipeline
│   ├── cli.py           # CLI Entry Point
│   ├── discovery.py     # File Discovery Logic
│   ├── analyzer.py      # Static Analysis Engine
│   ├── manifest.py      # JSON Report Generator
│   ├── formatter.py     # Output Formatting
│   └── config.py        # Risk Definitions
├── examples/            # Demo Files
│   ├── example_safe.py
│   └── example_danger.py
├── tests/               # Unit Tests
└── requirements.txt     # Dependencies
```

## 📝 Example Output

```text
MCP SCAN REPORT (2025-10-24T12:00:00+00:00)
================================================================================
Server Name                    | Risk       | Score    | Patterns
--------------------------------------------------------------------------------
safe-demo                      | SAFE       | 0        | 0       
danger-demo                    | HIGH       | 70       | 3       
--------------------------------------------------------------------------------
Summary:
  Total Servers: 2
  SAFE:   1
  MEDIUM: 0
  HIGH:   1
================================================================================
```

---

## 🤝 Contributing

Contributions are welcome! Please run tests before submitting:

```bash
uv run python test_scanner.py
```
