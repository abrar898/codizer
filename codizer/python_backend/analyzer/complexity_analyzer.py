import ast
import ast2json
import re
from big_o import big_o, complexities

class ComplexityAnalyzer:
    def __init__(self):
        self.time_complexity_patterns = {
            'O(1)': [
                r'^\s*return\s+', 
                r'^\s*\w+\s*=\s*\w+\s*', 
                r'^\s*print\s*\(',
                r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*[+\-*/]?=\s*\d+\s*$',  # Simple assignments: x = 5
                r'^\s*if\s+.+:\s*$',  # Simple if statements without loops
                r'^\s*constant_time\s*\(',  # Function name indicator
                r'^#\s*Time\s*Complexity:\s*O\(1\)',  # Manual annotation
            ],
            'O(log n)': [
                r'while.*\/=\s*2', 
                r'while.*\*=\s*2',
                r'binary_search',
                r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[a-zA-Z_][a-zA-Z0-9_]*\s*//\s*2',  # x = n // 2
                r'mid\s*=\s*\(.+\)\s*//\s*2',  # mid = (left + right) // 2
                r'^#\s*Time\s*Complexity:\s*O\(log\s*n\)',  # Manual annotation
            ],
            'O(n)': [
                r'^\s*for\s+\w+\s+in\s+\w+:', 
                r'^\s*for\s+\w+\s+in\s+range\(.+\):',
                r'^\s*while\s+\w+\s*[<>=!]=?\s*\w+:',
                r'linear_search',
                r'\.count\(', 
                r'\.index\(',
                r'^#\s*Time\s*Complexity:\s*O\(n\)',  # Manual annotation
                r'^#\s*O\(n\)',  # Simplified annotation
            ],
            'O(n log n)': [
                r'\.sort\(\)', 
                r'sorted\(',
                r'merge_sort',
                r'quick_sort',
                r'heap_sort',
                r'^#\s*Time\s*Complexity:\s*O\(n\s*log\s*n\)',  # Manual annotation
            ],
            'O(n^2)': [
                r'^\s*for\s+\w+\s+in\s+\w+:.*for\s+\w+\s+in\s+\w+:',
                r'^\s*for\s+\w+\s+in\s+range\(.+\):.*for\s+\w+\s+in\s+range\(.+\):',
                r'bubble_sort',
                r'insertion_sort',
                r'selection_sort',
                r'^#\s*Time\s*Complexity:\s*O\(n\^2\)',  # Manual annotation
                r'^#\s*O\(n\^2\)',  # Simplified annotation
            ],
            'O(n^3)': [
                r'^\s*for\s+\w+\s+in\s+\w+:.*for\s+\w+\s+in\s+\w+:.*for\s+\w+\s+in\s+\w+:',
                r'^\s*for\s+\w+\s+in\s+range\(.+\):.*for\s+\w+\s+in\s+range\(.+\):.*for\s+\w+\s+in\s+range\(.+\):',
                r'triple_nested_loop',
                r'^#\s*Time\s*Complexity:\s*O\(n\^3\)',  # Manual annotation
            ],
            'O(n^4)': [
                r'^\s*for\s+\w+\s+in\s+\w+:.*for\s+\w+\s+in\s+\w+:.*for\s+\w+\s+in\s+\w+:.*for\s+\w+\s+in\s+\w+:',
                r'^\s*for\s+\w+\s+in\s+range\(.+\):.*for\s+\w+\s+in\s+range\(.+\):.*for\s+\w+\s+in\s+range\(.+\):.*for\s+\w+\s+in\s+range\(.+\):',
                r'^#\s*Time\s*Complexity:\s*O\(n\^4\)',  # Manual annotation
            ],
            'O(2^n)': [
                r'fibonacci',
                r'def\s+(\w+).*?\(\s*.*?\s*\).*?\1\s*\(',  # Recursive function calling itself
                r'^#\s*Time\s*Complexity:\s*O\(2\^n\)',  # Manual annotation
            ]
        }
        
        # Common space complexity indicators
        self.space_complexity_patterns = {
            'O(1)': [
                r'^\s*\w+\s*=\s*\d+\s*$', 
                r'^\s*return\s+',
                r'^\s*[a-zA-Z_][a-zA-Z0-9_]*\s*[+\-*/]?=\s*\d+\s*$',  # Simple assignments: x = 5
                r'^#\s*Space\s*Complexity:\s*O\(1\)',  # Manual annotation
            ],
            'O(log n)': [
                r'binary_search',  # Binary search typically uses O(log n) stack space
                r'^#\s*Space\s*Complexity:\s*O\(log\s*n\)',  # Manual annotation
            ],
            'O(n)': [
                r'\w+\s*=\s*\[\]', 
                r'\w+\s*=\s*list\(', 
                r'\w+\s*=\s*dict\(', 
                r'\w+\s*=\s*set\(',
                r'append\(',
                r'extend\(',
                r'result\s*=\s*\[\]',  # Common pattern in merge sort
                r'\[\s*for\s+\w+\s+in\s+range\(\w+\)\s*\]',  # List comprehensions
                r'\[\s*for\s+\w+\s+in\s+\w+\s*\]',
                r'^#\s*Space\s*Complexity:\s*O\(n\)',  # Manual annotation
            ],
            'O(n^2)': [
                r'\[\s*\[\s*.*\]\s*for', 
                r'for.*:\s*\w+\s*=\s*\[\]',
                r'\[\s*\[\s*for\s+\w+\s+in\s+range\(\w+\)\s*\]\s*for\s+\w+\s+in\s+range\(\w+\)\s*\]',  # 2D list comprehensions
                r'^#\s*Space\s*Complexity:\s*O\(n\^2\)',  # Manual annotation
            ],
            'O(n^3)': [
                r'\[\s*\[\s*\[\s*for\s+\w+\s+in\s+range\(\w+\)\s*\]\s*for\s+\w+\s+in\s+range\(\w+\)\s*\]\s*for\s+\w+\s+in\s+range\(\w+\)\s*\]',  # 3D list comprehensions
                r'^#\s*Space\s*Complexity:\s*O\(n\^3\)',  # Manual annotation
            ],
        }

    def analyze_python_code(self, code):
        result = {
            'time_complexity': 'O(1)',  # Default
            'space_complexity': 'O(1)'  # Default
        }
        
        # First check for explicit complexity annotations in comments
        lines = code.split('\n')
        for line in lines:
            # Look for explicit time complexity annotations
            time_match = re.search(r'#\s*Time\s*Complexity:\s*(O\([^)]+\))', line)
            if time_match:
                result['time_complexity'] = time_match.group(1)
                
            # Look for explicit space complexity annotations
            space_match = re.search(r'#\s*Space\s*Complexity:\s*(O\([^)]+\))', line)
            if space_match:
                result['space_complexity'] = space_match.group(1)
        
        # If we found explicit annotations, return them
        if (result['time_complexity'] != 'O(1)' or result['space_complexity'] != 'O(1)') and \
           ('Time Complexity:' in code or 'Space Complexity:' in code):
            return result
        
        # Count the maximum nesting depth for loops
        loop_depth = 0
        max_loop_depth = 0
        
        # Count the nesting of for loops in code
        # Starting indentation level
        base_indent = None
        current_indent = 0
        indent_levels = []
        
        for line in lines:
            if not line.strip():
                continue
                
            # Calculate indentation level
            indent = len(line) - len(line.lstrip())
            
            # Initialize base indent if not set
            if base_indent is None and line.strip():
                base_indent = indent
                current_indent = 0
                indent_levels = [indent]
            elif line.strip():
                # Adjust indentation level
                if indent > indent_levels[-1]:
                    indent_levels.append(indent)
                    current_indent += 1
                elif indent < indent_levels[-1]:
                    while indent_levels and indent < indent_levels[-1]:
                        indent_levels.pop()
                        current_indent -= 1
                    if not indent_levels:
                        indent_levels = [indent]
                        current_indent = 0
            
            # Check if line has a loop
            if re.search(r'^\s*for\s+\w+\s+in\s+', line) or re.search(r'^\s*while\s+', line):
                loop_depth = current_indent + 1  # +1 because we're counting the loops themselves
                max_loop_depth = max(max_loop_depth, loop_depth)
        
        # Check for algorithm name indicators in function names or comments
        if 'merge_sort' in code:
            result['time_complexity'] = 'O(n log n)'
            result['space_complexity'] = 'O(n)'
        elif 'bubble_sort' in code or 'insertion_sort' in code or 'selection_sort' in code:
            result['time_complexity'] = 'O(n^2)'
            result['space_complexity'] = 'O(1)'
        elif 'linear_search' in code:
            result['time_complexity'] = 'O(n)'
            result['space_complexity'] = 'O(1)'
        elif 'binary_search' in code:
            result['time_complexity'] = 'O(log n)'
            result['space_complexity'] = 'O(1)'
        elif 'triple_nested_loop' in code:
            result['time_complexity'] = 'O(n^3)'
            result['space_complexity'] = 'O(1)'
        elif 'constant_time' in code:
            result['time_complexity'] = 'O(1)'
            result['space_complexity'] = 'O(1)'
        
        # Count actual loop nesting by direct pattern matching
        code_no_whitespace = re.sub(r'\s+', ' ', code)
        
        # Count nested loops by pattern matching for better accuracy
        nested_loops_count = 0
        if re.search(r'for.*for.*for.*for.*for', code_no_whitespace, re.DOTALL):
            nested_loops_count = 5
        elif re.search(r'for.*for.*for.*for', code_no_whitespace, re.DOTALL):
            nested_loops_count = 4
        elif re.search(r'for.*for.*for', code_no_whitespace, re.DOTALL):
            nested_loops_count = 3
        elif re.search(r'for.*for', code_no_whitespace, re.DOTALL):
            nested_loops_count = 2
        elif re.search(r'for', code_no_whitespace, re.DOTALL):
            nested_loops_count = 1
            
        # Use the maximum value between the two methods
        max_loop_depth = max(max_loop_depth, nested_loops_count)
        
        # Determine complexity based on loop nesting depth
        if max_loop_depth == 1:
            result['time_complexity'] = 'O(n)'
        elif max_loop_depth == 2:
            result['time_complexity'] = 'O(n^2)'
        elif max_loop_depth == 3:
            result['time_complexity'] = 'O(n^3)'
        elif max_loop_depth >= 4:
            result['time_complexity'] = f'O(n^{max_loop_depth})'
        
        # Check for patterns that indicate time complexity
        for complexity, patterns in self.time_complexity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code, re.MULTILINE):
                    # Only update if the new complexity is higher than the current one
                    if self._is_higher_complexity(complexity, result['time_complexity']):
                        result['time_complexity'] = complexity
                        break
        
        # Check for patterns that indicate space complexity
        for complexity, patterns in self.space_complexity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, code, re.MULTILINE):
                    # Only update if the new complexity is higher than the current one
                    if self._is_higher_complexity(complexity, result['space_complexity']):
                        result['space_complexity'] = complexity
                        break
        
        # If we detect recursive calls, check for exponential complexity
        if re.search(r'def\s+(\w+).*?\(\s*.*?\s*\).*?\1\s*\(', code, re.DOTALL) and not "memo" in code and not "cache" in code:
            # Simple recursion detection, might be exponential
            if result['time_complexity'] == 'O(1)':
                result['time_complexity'] = 'O(2^n)'  # Default for recursion
            elif max_loop_depth == 0:
                # If no loops but recursion, it's likely exponential
                result['time_complexity'] = 'O(2^n)'
        
        # Try to parse the code and analyze AST for more complex cases
        try:
            tree = ast.parse(code)
            
            # Check for binary search patterns in AST
            is_binary_search = False
            if (re.search(r'mid\s*=\s*\(.+\)\s*//\s*2', code, re.MULTILINE) and 
                re.search(r'if\s+.+\s*==\s*.+:', code, re.MULTILINE) and
                (re.search(r'while\s+.+\s*<=\s*.+:', code, re.MULTILINE) or 
                 re.search(r'binary_search', code, re.MULTILINE))):
                
                is_binary_search = True
                # Mark the entire code as logarithmic if it's a binary search
                result['time_complexity'] = 'O(log n)'
            
            # If this is binary search, override the complexity of any loops inside
            if is_binary_search or 'binary_search' in code:
                result['time_complexity'] = 'O(log n)'
                
        except Exception as e:
            # print(f"Error in AST analysis: {e}")
            pass
        
        return result
    
    def analyze_single_line(self, line, context=None):
        """Analyze a single line of code with optional context"""
        # Default complexity for single line
        result = {
            'time_complexity': 'O(1)',
            'space_complexity': 'O(1)'
        }
        
        # If context is provided, use it to help determine complexity
        if context:
            # Check if this line is part of a loop or specific structure
            context_above = '\n'.join(context.get('lines_above', []))
            context_below = '\n'.join(context.get('lines_below', []))
            
            # Check indentation to see if we're inside a loop
            indent = len(line) - len(line.lstrip())
            
            # Check if we're in a for loop from the context above
            loop_count = 0
            lines_above = context.get('lines_above', [])
            loop_depths = []
            
            # Determine loop nesting from context
            for ctx_line in reversed(lines_above):
                ctx_indent = len(ctx_line) - len(ctx_line.lstrip())
                if ctx_indent < indent and re.search(r'^\s*for\s+', ctx_line):
                    loop_count += 1
                    loop_depths.append(ctx_indent)
            
            # Update complexity based on loop nesting
            if loop_count == 1:
                result['time_complexity'] = 'O(n)'
            elif loop_count == 2:
                result['time_complexity'] = 'O(n^2)'
            elif loop_count == 3:
                result['time_complexity'] = 'O(n^3)'
            elif loop_count >= 4:
                result['time_complexity'] = f'O(n^{loop_count})'
        
        # Direct pattern matching for the single line
        for complexity, patterns in self.time_complexity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line, re.MULTILINE):
                    # Only update if the new complexity is higher
                    if self._is_higher_complexity(complexity, result['time_complexity']):
                        result['time_complexity'] = complexity
        
        # Check space complexity for the single line
        for complexity, patterns in self.space_complexity_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line, re.MULTILINE):
                    # Only update if the new complexity is higher
                    if self._is_higher_complexity(complexity, result['space_complexity']):
                        result['space_complexity'] = complexity
        
        # Check for special cases on the line
        if re.search(r'^\s*mid\s*=', line) or re.search(r'binary_search', line):
            result['time_complexity'] = 'O(log n)'
        
        return result
    
    def _is_higher_complexity(self, complexity1, complexity2):
        """Compare two complexity notations and return True if complexity1 is higher"""
        # Define order of complexity from lowest to highest
        complexity_order = [
            'O(1)', 
            'O(log n)', 
            'O(n)', 
            'O(n log n)', 
            'O(n^2)', 
            'O(n^3)', 
            'O(n^4)',
            'O(n^5)',
            'O(2^n)'
        ]
        
        # Handle custom n^x notation
        if complexity1.startswith('O(n^') and complexity1 not in complexity_order:
            power1 = int(complexity1.replace('O(n^', '').replace(')', ''))
            idx1 = min(power1 + 2, len(complexity_order) - 1)  # +2 to account for O(1) and O(log n)
        else:
            try:
                idx1 = complexity_order.index(complexity1)
            except ValueError:
                idx1 = 0  # Default to lowest if not found
        
        if complexity2.startswith('O(n^') and complexity2 not in complexity_order:
            power2 = int(complexity2.replace('O(n^', '').replace(')', ''))
            idx2 = min(power2 + 2, len(complexity_order) - 1)
        else:
            try:
                idx2 = complexity_order.index(complexity2)
            except ValueError:
                idx2 = 0
        
        return idx1 > idx2
        
    def analyze_code(self, code, language):
        """
        Analyze code for time and space complexity
        """
        if language.lower() == 'python':
            return self.analyze_python_code(code)
        
        # Default response for unsupported languages
        return {
            'time_complexity': 'Cannot determine',
            'space_complexity': 'Cannot determine'
        } 