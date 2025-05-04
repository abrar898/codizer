#!/usr/bin/env python
import sys
import json
import ast
import os
import re
from typing import Dict, List, Tuple, Any, Optional

# Add debug log to help troubleshoot
print("Python complexity analyzer starting...")
sys.stderr.write("Debug: Script called with arguments: {}\n".format(sys.argv))

class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor that analyzes code complexity in Python files."""
    
    def __init__(self):
        self.functions = {}
        self.classes = {}
        self.current_function = None
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        prev_function = self.current_function
        self.current_function = node.name
        
        # Calculate cyclomatic complexity
        complexity = 1  # Base complexity is 1
        
        # Count branches
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.comprehension)):
                complexity += 1
            elif isinstance(child, ast.BoolOp) and isinstance(child.op, ast.And):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.BoolOp) and isinstance(child.op, ast.Or):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.Break):
                complexity += 1
            elif isinstance(child, ast.Continue):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        
        # Analyze function source code for time and space complexity clues
        source_lines = []
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            source_lines = astroid_source[node.lineno-1:node.end_lineno]
        
        time_complexity = self.infer_time_complexity(node, source_lines)
        space_complexity = self.infer_space_complexity(node, source_lines)
        
        full_name = f"{self.current_class}.{node.name}" if self.current_class else node.name
        
        self.functions[full_name] = {
            "name": node.name,
            "class": self.current_class,
            "lineno": node.lineno,
            "end_lineno": getattr(node, 'end_lineno', node.lineno),
            "cyclomatic_complexity": complexity,
            "time_complexity": time_complexity,
            "space_complexity": space_complexity,
            "args": [arg.arg for arg in node.args.args],
            "returns": self.get_return_annotation(node)
        }
        
        # Visit children
        self.generic_visit(node)
        self.current_function = prev_function
    
    def visit_ClassDef(self, node):
        prev_class = self.current_class
        self.current_class = node.name
        
        self.classes[node.name] = {
            "name": node.name,
            "lineno": node.lineno,
            "end_lineno": getattr(node, 'end_lineno', node.lineno),
            "methods": [],
            "bases": [base.id if isinstance(base, ast.Name) else "..." for base in node.bases]
        }
        
        # Visit children
        self.generic_visit(node)
        
        # Update class methods
        if self.current_class:
            for func_name, func_data in self.functions.items():
                if func_data["class"] == self.current_class:
                    self.classes[self.current_class]["methods"].append(func_name)
        
        self.current_class = prev_class
    
    def get_return_annotation(self, node):
        """Extract return type annotation if available."""
        if node.returns:
            if isinstance(node.returns, ast.Name):
                return node.returns.id
            elif isinstance(node.returns, ast.Subscript):
                # Handle simple generic types like List[int]
                if isinstance(node.returns.value, ast.Name):
                    return f"{node.returns.value.id}[...]"
                return "complex_type"
            return "..."
        return None
    
    def infer_time_complexity(self, node, source_lines: List[str]) -> str:
        """Infer time complexity based on code patterns."""
        source_code = "\n".join(source_lines)
        
        # Look for nested loops
        nested_loops = 0
        max_nested = 0
        
        for child in ast.walk(node):
            if isinstance(child, (ast.For, ast.While)):
                nested_loops += 1
                max_nested = max(max_nested, nested_loops)
            elif isinstance(child, ast.FunctionDef):
                if child != node:  # Skip the original function
                    nested_loops = 0
        
        # Look for recursion
        calls_self = False
        for child in ast.walk(node):
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id == node.name:
                    calls_self = True
                    break
        
        # Check for sorting or known algorithms
        has_sort = "sort" in source_code.lower() or "sorted" in source_code.lower()
        
        # Determine complexity
        if calls_self and ("if" in source_code.lower() or "while" in source_code.lower()):
            return "O(2^n)"  # Recursive with branching
        elif calls_self:
            return "O(n!)"  # Simple recursion, could be factorial
        elif max_nested >= 3:
            return f"O(n^{max_nested})"
        elif max_nested == 2:
            return "O(n²)"
        elif max_nested == 1:
            return "O(n)"
        elif has_sort:
            return "O(n log n)"
        else:
            return "O(1)"  # Default to constant time
    
    def infer_space_complexity(self, node, source_lines: List[str]) -> str:
        """Infer space complexity based on code patterns."""
        source_code = "\n".join(source_lines)
        
        # Check for list/dict/set comprehensions
        has_comprehension = False
        creates_new_list = False
        recursive_calls = 0
        
        for child in ast.walk(node):
            if isinstance(child, ast.ListComp) or isinstance(child, ast.DictComp) or isinstance(child, ast.SetComp):
                has_comprehension = True
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id in ('list', 'dict', 'set'):
                    creates_new_list = True
                if child.func.id == node.name:
                    recursive_calls += 1
        
        # Determine complexity
        if recursive_calls > 0:
            return "O(n)"  # Recursive function typically uses stack space
        elif has_comprehension or creates_new_list:
            return "O(n)"  # Creates data structures proportional to input
        else:
            return "O(1)"  # Default to constant space

def analyze_file(file_path: str) -> Dict[str, Any]:
    """Analyze Python file for complexity metrics."""
    global astroid_source
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
            astroid_source = source_code.splitlines()
        
        # Parse the AST
        tree = ast.parse(source_code)
        
        # Visit the AST
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        # Get file-level metrics
        lines_of_code = len(astroid_source)
        
        # Calculate average complexity
        total_complexity = sum(f["cyclomatic_complexity"] for f in visitor.functions.values())
        avg_complexity = total_complexity / len(visitor.functions) if visitor.functions else 0
        
        return {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "lines_of_code": lines_of_code,
            "num_functions": len(visitor.functions),
            "num_classes": len(visitor.classes),
            "avg_complexity": round(avg_complexity, 2),
            "functions": visitor.functions,
            "classes": visitor.classes,
        }
    except Exception as e:
        return {
            "error": True,
            "message": str(e),
            "file_path": file_path
        }

def save_results(results: Dict[str, Any], file_path: str) -> str:
    """Save analysis results to a JSON file next to the original file."""
    output_path = os.path.splitext(file_path)[0] + ".complexity.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    return output_path

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_complexity.py <python_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(json.dumps({"error": True, "message": f"File not found: {file_path}"}))
        sys.exit(1)
    
    results = analyze_file(file_path)
    output_path = save_results(results, file_path)
    
    # Print results as JSON for the extension to parse
    print(json.dumps(results))

if __name__ == "__main__":
    main() 