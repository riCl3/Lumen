"""
Analyzer module for processing discovered MCP data.
"""
import ast
import re
import logging
from typing import Dict, List, Any, Tuple, Union
try:
    from . import config
except ImportError:
    # Fallback for standalone usage or testing
    import scanner.config as config

logger = logging.getLogger(__name__)

class StaticAnalyzer:
    """
    Static analyzer for Python code to detect risky patterns and operations.
    """

    def __init__(self, config_module=config):
        """
        Initialize the analyzer with configuration.
        
        Args:
            config_module: Module containing risk definitions
        """
        self.config = config_module
        
        # Compile regex patterns for dangerous imports and dynamic execution
        self.dangerous_import_patterns = [
            (name, re.compile(rf'\b{name}\b')) 
            for name in getattr(self.config, 'DANGEROUS_IMPORTS', [])
        ]
        self.dynamic_execution_patterns = [
             (name, re.compile(rf'\b{name}\b')) 
             for name in getattr(self.config, 'DYNAMIC_EXECUTION', [])
        ]

    def scan_imports(self, tree: ast.AST) -> List[str]:
        """
        Extract all import statements using AST.
        
        Args:
            tree: AST of the source code
            
        Returns:
            List of imported module names
        """
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
        return list(set(imports))

    def detect_patterns(self, source_code: str, patterns: List[Tuple[str, Any]]) -> List[Tuple[str, int]]:
        """
        Search for patterns using regex.
        
        Args:
            source_code: Raw source code string
            patterns: List of (name, regex_pattern) tuples
            
        Returns:
            List of (pattern_name, line_number) tuples
        """
        findings = []
        lines = source_code.splitlines()
        
        for name, pattern in patterns:
            for i, line in enumerate(lines):
                if pattern.search(line):
                     # Basic comment detection
                    if line.strip().startswith('#'):
                        continue
                    findings.append((name, i + 1))
        return findings

    def detect_dangerous_imports(self, source_code: str) -> List[Tuple[str, int]]:
        return self.detect_patterns(source_code, self.dangerous_import_patterns)

    def detect_dynamic_execution(self, source_code: str) -> List[Tuple[str, int]]:
        return self.detect_patterns(source_code, self.dynamic_execution_patterns)

    def find_file_operations(self, tree: ast.AST) -> List[Tuple[str, int]]:
        """
        Detect file read/write operations using AST.
        """
        findings = []
        file_ops = set(getattr(self.config, 'FILE_OPERATIONS', []))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = None
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    name = node.func.attr
                
                if name and name in file_ops:
                    findings.append((name, node.lineno))
                    
        return findings

    def find_network_calls(self, tree: ast.AST) -> List[Tuple[str, int]]:
        """
        Detect network operations using AST.
        """
        findings = []
        net_ops = set(getattr(self.config, 'NETWORK_OPERATIONS', []))
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = None
                # Check for calls like requests.get()
                if isinstance(node.func, ast.Attribute):
                    # Check if the object being called is a known network module (e.g. requests)
                    if isinstance(node.func.value, ast.Name) and node.func.value.id in net_ops:
                        findings.append((f"{node.func.value.id}.{node.func.attr}", node.lineno))
                    # Or if the method itself is in the list
                    elif node.func.attr in net_ops:
                        findings.append((node.func.attr, node.lineno))
                elif isinstance(node.func, ast.Name):
                     if node.func.id in net_ops:
                        findings.append((node.func.id, node.lineno))

        return findings

    def get_pattern_details(self, category: str, item: str, score: int) -> str:
        """
        Returns human-readable explanation for a risk pattern.
        """
        explanations = {
            "DANGEROUS_IMPORTS": f"Import/Usage of system module '{item}' (+{score})",
            "DYNAMIC_EXECUTION": f"Dynamic execution using '{item}' (+{score})",
            "FILE_OPERATIONS": f"File operation '{item}' detected (+{score})",
            "NETWORK_OPERATIONS": f"Network call '{item}' detected (+{score})"
        }
        return explanations.get(category, f"Detected {item} in {category} (+{score})")

    def calculate_risk_score(self, findings: Dict[str, List]) -> Tuple[int, List[Dict[str, Any]]]:
        """
        Sum up risk points and return detailed breakdown.
        
        Returns:
            Tuple of (total_score, breakdown_list)
        """
        total_score = 0
        breakdown = []
        weights = getattr(self.config, 'RISK_WEIGHTS', {})
        
        categories = [
            ('DANGEROUS_IMPORTS', findings.get('dangerous_imports', [])),
            ('DYNAMIC_EXECUTION', findings.get('dynamic_execution', [])),
            ('FILE_OPERATIONS', findings.get('file_operations', [])),
            ('NETWORK_OPERATIONS', findings.get('network_calls', []))
        ]

        for category, items in categories:
            weight = weights.get(category, 0)
            for item in items:
                # Item matches structure (name, line) from detection methods
                name = item[0]
                line = item[1] if len(item) > 1 else 0
                
                total_score += weight
                breakdown.append({
                    "category": category,
                    "item": name,
                    "line": line,
                    "score": weight,
                    "description": self.get_pattern_details(category, name, weight)
                })
        
        return total_score, breakdown

    def determine_risk_level(self, score: int) -> str:
        """Map score to SAFE/MEDIUM/HIGH."""
        levels = getattr(self.config, 'RISK_LEVELS', {})
        for level, (min_s, max_s) in levels.items():
            if min_s <= score <= max_s:
                return level
        return "HIGH" if score > 100 else "SAFE"

    def scan_code(self, file_content: str) -> Dict[str, Any]:
        """Orchestrates all checks."""
        try:
            tree = ast.parse(file_content)
        except SyntaxError:
            return {
                "risk_score": 0,
                "risk_level": "UNKNOWN",
                "error": "SyntaxError parsing file",
                "breakdown": []
            }

        imports = self.scan_imports(tree)
        
        dangerous_imports = self.detect_dangerous_imports(file_content)
        dynamic_exec = self.detect_dynamic_execution(file_content)
        file_ops = self.find_file_operations(tree)
        net_calls = self.find_network_calls(tree)
        
        all_findings = {
            "dangerous_imports": dangerous_imports,
            "dynamic_execution": dynamic_exec,
            "file_operations": file_ops,
            "network_calls": net_calls
        }
        
        score, breakdown = self.calculate_risk_score(all_findings)
        level = self.determine_risk_level(score)
        
        # Aggregate line numbers for easy API/UI access if needed, though breakdown has them
        return {
            "risk_score": score,
            "risk_level": level,
            "breakdown": breakdown,
            "imports": imports,
            "summary": {
                "dangerous_imports": len(dangerous_imports),
                "dynamic_execution": len(dynamic_exec),
                "file_operations": len(file_ops),
                "network_calls": len(net_calls)
            }
        }
