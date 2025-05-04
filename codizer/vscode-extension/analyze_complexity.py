#!/usr/bin/env python3
"""
Analyze Python code for time and space complexity.
This script parses Python code, extracts functions and methods,
and estimates their time and space complexity.
"""

import ast
import json
import sys
import os
from typing import Dict, List, Tuple, Any, Optional


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor that analyzes code complexity."""
    
    def __init__(self):
        self.functions = {}
        self.current_function = None
        self.loop_depth = 0
        self.conditional_depth = 0
        
    def visit_FunctionDef(self, node):
        """Visit a function definition."""
        prev_function = self.current_function
        function_info = {
            'name': node.name,
            'line_start': node.lineno,
            'line_end': self._get_last_line(node),
            'loops': [],
            'calls': [],
            'conditionals': [],
            'time_complexity': 'O(1)',  # Default
            'space_complexity': 'O(1)',  # Default
            'has_recursion': False
        }
        
        self.current_function = function_info
        
        # Process the function body
        self.generic_visit(node)
        
        # Calculate complexity based on collected data
        self._calculate_complexity()
        
        # Add to functions dictionary
        self.functions[node.name] = self.current_function
        self.current_function = prev_function
    
    visit_AsyncFunctionDef = visit_FunctionDef  # Handle async functions too
    
    def visit_ClassDef(self, node):
        """Visit a class definition to extract methods."""
        self.generic_visit(node)
    
    def visit_For(self, node):
        """Visit a for loop."""
        if self.current_function:
            self.loop_depth += 1
            loop_info = {
                'line': node.lineno,
                'depth': self.loop_depth,
                'nested_in': self.loop_depth - 1 if self.loop_depth > 0 else None
            }
            self.current_function['loops'].append(loop_info)
            self.generic_visit(node)
            self.loop_depth -= 1
    
    visit_While = visit_For  # Handle while loops similarly
    
    def visit_ListComp(self, node):
        """Visit a list comprehension (counts as a loop)."""
        if self.current_function:
            loop_info = {
                'line': node.lineno,
                'depth': 1,
                'nested_in': None,
                'type': 'comprehension'
            }
            self.current_function['loops'].append(loop_info)
        self.generic_visit(node)
    
    visit_DictComp = visit_ListComp  # Dict comprehensions are similar
    visit_SetComp = visit_ListComp   # Set comprehensions are similar
    
    def visit_If(self, node):
        """Visit an if statement."""
        if self.current_function:
            self.conditional_depth += 1
            conditional_info = {
                'line': node.lineno,
                'depth': self.conditional_depth
            }
            self.current_function['conditionals'].append(conditional_info)
            self.generic_visit(node)
            self.conditional_depth -= 1
    
    def visit_Call(self, node):
        """Visit a function call."""
        if self.current_function:
            func_name = self._get_call_name(node)
            if func_name:
                # Check for recursive calls
                if func_name == self.current_function['name']:
                    self.current_function['has_recursion'] = True
                
                call_info = {
                    'line': node.lineno,
                    'name': func_name
                }
                self.current_function['calls'].append(call_info)
        self.generic_visit(node)
    
    def _get_call_name(self, node):
        """Extract the name of a function being called."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None
    
    def _get_last_line(self, node):
        """Find the last line of a node."""
        last_line = node.lineno
        for child in ast.iter_child_nodes(node):
            if hasattr(child, 'lineno'):
                last_line = max(last_line, child.lineno)
            # Recursively check children
            child_last_line = self._get_last_line(child)
            last_line = max(last_line, child_last_line)
        return last_line
    
    def _calculate_complexity(self):
        """Calculate time and space complexity based on collected data."""
        if not self.current_function:
            return
        
        # Time complexity analysis
        if self.current_function['has_recursion']:
            self.current_function['time_complexity'] = 'O(2^n)'  # Simplistic approximation
        elif not self.current_function['loops']:
            self.current_function['time_complexity'] = 'O(1)'
        else:
            # Find max nested loop depth
            max_depth = 0
            for loop in self.current_function['loops']:
                max_depth = max(max_depth, loop['depth'])
            
            if max_depth == 1:
                self.current_function['time_complexity'] = 'O(n)'
            elif max_depth == 2:
                self.current_function['time_complexity'] = 'O(n²)'
            elif max_depth == 3:
                self.current_function['time_complexity'] = 'O(n³)'
            else:
                self.current_function['time_complexity'] = f'O(n^{max_depth})'
        
        # Space complexity analysis - simplified
        self.current_function['space_complexity'] = 'O(n)'  # Default assumption


def analyze_file(file_path: str) -> Dict[str, Any]:
    """
    Analyze a Python file for complexity.
    
    Args:
        file_path: Path to the Python file
        
    Returns:
        Dictionary with analysis results
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    try:
        tree = ast.parse(code)
        visitor = ComplexityVisitor()
        visitor.visit(tree)
        
        # Overall complexity is the maximum of all functions
        overall_time = 'O(1)'
        overall_space = 'O(1)'
        complexities = {
            'O(1)': 0,
            'O(n)': 1,
            'O(n²)': 2,
            'O(n³)': 3,
            'O(2^n)': 4,
            'O(n!)': 5
        }
        
        for func in visitor.functions.values():
            time_complexity = func['time_complexity']
            space_complexity = func['space_complexity']
            
            # Update overall complexities (take the "worst" one)
            if time_complexity in complexities:
                if complexities.get(time_complexity, 0) > complexities.get(overall_time, 0):
                    overall_time = time_complexity
            
            if space_complexity in complexities:
                if complexities.get(space_complexity, 0) > complexities.get(overall_space, 0):
                    overall_space = space_complexity
        
        result = {
            'functions': visitor.functions,
            'overall_time_complexity': overall_time,
            'overall_space_complexity': overall_space
        }
        return result
    
    except SyntaxError as e:
        return {
            'error': f"Syntax error: {str(e)}",
            'functions': {},
            'overall_time_complexity': 'Unknown',
            'overall_space_complexity': 'Unknown'
        }


def main():
    """Main entry point for script."""
    if len(sys.argv) != 2:
        print("Usage: python analyze_complexity.py <python_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist.")
        sys.exit(1)
    
    if not file_path.endswith('.py'):
        print("Error: File must be a Python file (.py extension)")
        sys.exit(1)
    
    analysis = analyze_file(file_path)
    
    # Save to a JSON file with the same name but .complexity.json extension
    output_path = f"{file_path}.complexity.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"Analysis complete. Results saved to {output_path}")
    
    # Print a summary
    print("\nSummary:")
    print(f"Overall Time Complexity: {analysis['overall_time_complexity']}")
    print(f"Overall Space Complexity: {analysis['overall_space_complexity']}")
    print(f"Functions analyzed: {len(analysis['functions'])}")
    
    for name, func in analysis['functions'].items():
        print(f"\n{name}:")
        print(f"  Time Complexity: {func['time_complexity']}")
        print(f"  Space Complexity: {func['space_complexity']}")
        print(f"  Lines: {func['line_start']}-{func['line_end']}")


if __name__ == "__main__":
    main() 