"""
Discovery module for finding MCP servers and resources.
"""
import ast
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

logger = logging.getLogger(__name__)

class FileScanner:
    """
    Scanner for discovering MCP servers and configurations in a project.
    """

    def __init__(self):
        """Initialize the FileScanner."""
        pass

    def scan_directory(self, directory_path: Path) -> List[Path]:
        """
        Recursively finds all Python files in the directory.
        
        Args:
            directory_path: Root directory to scan
            
        Returns:
            List of Path objects for Python files found
        """
        python_files = []
        try:
            directory = Path(directory_path)
            if not directory.exists():
                logger.error(f"Directory not found: {directory}")
                return []

            for path in directory.rglob("*.py"):
                # Skip hidden directories/files and common ignores
                if any(part.startswith('.') for part in path.parts):
                    continue
                if any(part in ['build', 'dist', 'venv', 'env', '__pycache__'] for part in path.parts):
                    continue
                    
                python_files.append(path)
                
        except Exception as e:
            logger.error(f"Error scanning directory {directory_path}: {e}")
            
        return python_files

    def scan_all_source_files(self, directory_path: Path, max_files: int = 50) -> List[Path]:
        """
        Recursively finds all Python, TypeScript, and JavaScript files.
        
        Args:
            directory_path: Root directory to scan
            max_files: Maximum number of files to return (to avoid overwhelming the system)
            
        Returns:
            List of Path objects for source files found
        """
        source_files = []
        extensions = ['*.py', '*.ts', '*.js', '*.mjs']
        
        try:
            directory = Path(directory_path)
            if not directory.exists():
                logger.error(f"Directory not found: {directory}")
                return []

            for ext in extensions:
                for path in directory.rglob(ext):
                    # Skip hidden directories/files and common ignores
                    if any(part.startswith('.') for part in path.parts):
                        continue
                    if any(part in ['build', 'dist', 'venv', 'env', '__pycache__', 'node_modules'] for part in path.parts):
                        continue
                    
                    # Skip test files and config files to focus on source code
                    if path.name.endswith('.test.ts') or path.name.endswith('.test.js') or path.name.endswith('.test.py'):
                        continue
                    if path.name in ['jest.config.js', 'webpack.config.js', 'rollup.config.js']:
                        continue
                        
                    source_files.append(path)
                    
                    # Limit to max_files to avoid overwhelming the system
                    if len(source_files) >= max_files:
                        logger.warning(f"Reached max file limit of {max_files}. Some files may not be scanned.")
                        return source_files
                
        except Exception as e:
            logger.error(f"Error scanning directory {directory_path}: {e}")
            
        return source_files

    def find_mcp_decorators(self, file_path: Path) -> List[str]:
        """
        Searches for @mcp.tool or @mcp.server patterns in a file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of detected decorator strings
        """
        found_decorators = []
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    for decorator in node.decorator_list:
                        # Handle simple names (@tool) and attribute access (@mcp.tool)
                        deco_name = ""
                        if isinstance(decorator, ast.Name):
                            deco_name = decorator.id
                        elif isinstance(decorator, ast.Attribute):
                            # reconstructing "mcp.tool" from AST
                            parts = []
                            curr = decorator
                            while isinstance(curr, ast.Attribute):
                                parts.append(curr.attr)
                                curr = curr.value
                            if isinstance(curr, ast.Name):
                                parts.append(curr.id)
                            deco_name = ".".join(reversed(parts))
                        elif isinstance(decorator, ast.Call):
                            # Handle decorators with arguments e.g. @mcp.tool(...)
                            if isinstance(decorator.func, ast.Name):
                                deco_name = decorator.func.id
                            elif isinstance(decorator.func, ast.Attribute):
                                parts = []
                                curr = decorator.func
                                while isinstance(curr, ast.Attribute):
                                    parts.append(curr.attr)
                                    curr = curr.value
                                if isinstance(curr, ast.Name):
                                    parts.append(curr.id)
                                deco_name = ".".join(reversed(parts))

                        if "mcp.tool" in deco_name or "mcp.server" in deco_name or "Server" in deco_name: 
                             # Broad check for mcp related decorators or simple "Server" class if relevant
                             # The requirement specifically mentions @mcp.tool or @mcp.server
                             # But sticking strictly to requirement:
                             pass
                        
                        # Regex fallback for text-based matching if AST is complex 
                        # but we want robust finding. 
                        # Let's check specifically for the requested patterns
                        if deco_name in ["mcp.tool", "mcp.server"] or \
                           deco_name.endswith(".tool") or deco_name.endswith(".server"):
                             found_decorators.append(deco_name)

        except Exception as e:
            logger.warning(f"Error parsing decorators in {file_path}: {e}")
            
        return found_decorators

    def find_config_files(self, directory_path: Path) -> List[Path]:
        """
        Looks for mcp.json or package.json with MCP configs.
        
        Args:
            directory_path: Root directory to scan
            
        Returns:
            List of Path objects for config files
        """
        config_files = []
        try:
            root = Path(directory_path)
            
            # Check for mcp.json
            for path in root.rglob("mcp.json"):
                config_files.append(path)
                
            # Check for package.json with mcp config
            for path in root.rglob("package.json"):
                if "node_modules" in path.parts:
                    continue
                try:
                    content = json.loads(path.read_text(encoding='utf-8'))
                    # Check for likely MCP configuration keys OR sdk dependency
                    is_mcp = False
                    if "mcp" in content or "mcpServers" in content:
                        is_mcp = True
                    
                    if not is_mcp:
                        dependencies = content.get("dependencies", {})
                        dev_dependencies = content.get("devDependencies", {})
                        if "@modelcontextprotocol/sdk" in dependencies or "@modelcontextprotocol/sdk" in dev_dependencies:
                            is_mcp = True

                    if is_mcp:
                        config_files.append(path)
                except Exception:
                    continue

            # Check for Cargo.toml (Rust MCP Servers)
            for path in root.rglob("Cargo.toml"):
                if "target" in path.parts:
                    continue
                # We can assume if it's in a folder being scanned as an MCP, it might be one.
                # Or checks for dependencies like 'mcp-sdk' (hypothetical) or similar if we wanted to be stricter.
                # For now, just detecting existence is good for "Potential Rust Server".
                config_files.append(path)
                    
        except Exception as e:
            logger.error(f"Error looking for config files in {directory_path}: {e}")
            
        return config_files

    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """
        Parses Python file to extract server metadata.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Dictionary with extracted metadata
        """
        metadata = {
            "name": file_path.name, # Default to filename
            "description": None,
            "entry_point": str(file_path),
            "decorators": []
        }
        
        try:
            content = file_path.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            # Extract docstring from module
            module_doc = ast.get_docstring(tree)
            if module_doc:
                metadata["description"] = module_doc.strip().split('\n')[0] # First line
            
            # Look for Server class or specific setup
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Heuristic: if class name contains "Server", use it as name
                    if "Server" in node.name:
                        metadata["name"] = node.name
                        class_doc = ast.get_docstring(node)
                        if class_doc and not metadata["description"]:
                            metadata["description"] = class_doc.strip().split('\n')[0]
            
            # Get decorators found
            metadata["decorators"] = self.find_mcp_decorators(file_path)
            
        except Exception as e:
            logger.warning(f"Error extracting metadata from {file_path}: {e}")
            
        return metadata

    def discover_servers(self, root_path: str) -> List[Dict[str, Any]]:
        """
        Main method that returns list of discovered server dictionaries.
        
        Args:
            root_path: Directory to start discovery from
            
        Returns:
            List of dictionaries representing discovered servers/tools
        """
        discovered = []
        path_obj = Path(root_path)
        
        # 1. Scan for Python files
        py_files = self.scan_directory(path_obj)
        
        for py_file in py_files:
            decorators = self.find_mcp_decorators(py_file)
            if decorators:
                # This file likely contains MCP definitions
                meta = self.extract_metadata(py_file)
                discovered.append({
                    "type": "python-server" if any("server" in d for d in decorators) else "python-tool",
                    "path": str(py_file),
                    "metadata": meta
                })
        
        # 2. Scan for Config files
        config_files = self.find_config_files(path_obj)
        for cfg in config_files:
            type_label = "config"
            name = cfg.name
            desc = "MCP Configuration File"
            
            if cfg.name == "Cargo.toml":
                type_label = "rust-server"
                desc = "Rust MCP Server (No static analysis available)"
            elif cfg.name == "package.json":
                type_label = "node-server"
                desc = "Node.js MCP Server (No static analysis available)"

            discovered.append({
                "type": type_label,
                "path": str(cfg),
                "metadata": {
                    "name": name,
                    "description": desc
                }
            })
            
        return discovered

    def discover_all_files(self, root_path: str, max_files: int = 50) -> List[Dict[str, Any]]:
        """
        Discovers ALL source files for comprehensive security scanning.
        
        Args:
            root_path: Directory to start discovery from
            max_files: Maximum number of files to scan
            
        Returns:
            List of dictionaries representing all discovered source files
        """
        discovered = []
        path_obj = Path(root_path)
        
        # Scan for all source files (.py, .ts, .js, .mjs)
        all_files = self.scan_all_source_files(path_obj, max_files=max_files)
        
        for source_file in all_files:
            # Determine file type
            ext = source_file.suffix
            if ext == '.py':
                file_type = "python-file"
                desc = "Python source file"
            elif ext in ['.ts', '.mts']:
                file_type = "typescript-file"
                desc = "TypeScript source file"
            elif ext in ['.js', '.mjs']:
                file_type = "javascript-file"
                desc = "JavaScript source file"
            else:
                file_type = "source-file"
                desc = "Source file"
            
            # Try to get basic metadata
            metadata = {
                "name": source_file.name,
                "description": desc,
                "entry_point": str(source_file)
            }
            
            # For Python files, try to extract decorators
            if ext == '.py':
                try:
                    decorators = self.find_mcp_decorators(source_file)
                    if decorators:
                        metadata["decorators"] = decorators
                        # If it has MCP decorators, upgrade the type
                        if any("server" in d for d in decorators):
                            file_type = "python-server"
                            desc = "Python MCP Server"
                        elif any("tool" in d for d in decorators):
                            file_type = "python-tool"
                            desc = "Python MCP Tool"
                        metadata["description"] = desc
                except Exception as e:
                    logger.debug(f"Could not extract decorators from {source_file}: {e}")
            
            discovered.append({
                "type": file_type,
                "path": str(source_file),
                "metadata": metadata
            })
        
        logger.info(f"Discovered {len(discovered)} source files for analysis")
        return discovered
