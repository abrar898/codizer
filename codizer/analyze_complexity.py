import sys
import os
import re
import json

# Import the ComplexityAnalyzer from our Django app
sys.path.append(os.path.join(os.path.dirname(__file__), 'python_backend'))
from analyzer.complexity_analyzer import ComplexityAnalyzer

def analyze_file(file_path):
    """Analyze a Python file for time and space complexity, line by line."""
    print(f"\n\033[1m🔍 Analyzing file: {file_path}\033[0m")
    print("-" * 80)
    
    # Initialize the analyzer
    analyzer = ComplexityAnalyzer()
    
    # Read the file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Store the lines for context analysis
    lines = content.split('\n')
    
    # Analyze the entire file first
    overall_result = analyzer.analyze_code(content, 'python')
    
    # Create a lookup table for line complexities
    line_complexities = {}
    line_hover_data = {}
    
    # First analyze all functions
    function_blocks = {}
    current_function = None
    function_start = 0
    indentation = 0
    
    # Process each line 
    for i, line in enumerate(lines, 1):
        # Check for function definition
        if re.match(r'^\s*def\s+\w+\s*\(', line):
            function_name = re.search(r'def\s+(\w+)', line).group(1)
            current_function = function_name
            function_start = i
            indentation = len(line) - len(line.lstrip())
            function_blocks[current_function] = [line]
        
        # Add lines to current function
        elif current_function and line.strip() and (len(line) - len(line.lstrip()) > indentation or not line.strip()):
            function_blocks[current_function].append(line)
        
        # End of function
        elif current_function and line.strip() and len(line) - len(line.lstrip()) <= indentation:
            # Analyze the function
            func_code = '\n'.join(function_blocks[current_function])
            result = analyzer.analyze_code(func_code, 'python')
            
            # Store complexity for all lines in this function
            for j in range(function_start, i):
                line_complexities[j] = {
                    'time': result['time_complexity'],
                    'space': result['space_complexity'],
                    'function': current_function
                }
            
            # Start a new function or reset
            current_function = None
            
            # Check if this line is a new function
            if re.match(r'^\s*def\s+\w+\s*\(', line):
                function_name = re.search(r'def\s+(\w+)', line).group(1)
                current_function = function_name
                function_start = i
                indentation = len(line) - len(line.lstrip())
                function_blocks[current_function] = [line]
    
    # If there's a function still being processed
    if current_function:
        func_code = '\n'.join(function_blocks[current_function])
        result = analyzer.analyze_code(func_code, 'python')
        
        # Store complexity for all lines in this function
        for j in range(function_start, len(lines) + 1):
            line_complexities[j] = {
                'time': result['time_complexity'],
                'space': result['space_complexity'],
                'function': current_function
            }
    
    # Now analyze individual lines for hover
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
            
        # Get context (lines above and below)
        context = {
            'lines_above': lines[max(0, i-10):i-1],
            'lines_below': lines[i:min(len(lines), i+10)]
        }
        
        # Analyze the single line with context
        line_result = analyzer.analyze_single_line(line, context)
        
        # Store the result for hover
        line_hover_data[i] = {
            'time': line_result['time_complexity'],
            'space': line_result['space_complexity'],
            'line': line.strip()
        }
    
    # Now process blocks (loops, conditionals)
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
            
        # For loops, while loops, if statements, collect the block
        if re.match(r'^\s*(for|while|if)\s+', line):
            indentation = len(line) - len(line.lstrip())
            block = [line]
            block_start = i + 1
            j = i + 1
            
            # Collect all lines in this block
            while j < len(lines) and (not lines[j].strip() or len(lines[j]) - len(lines[j].lstrip()) > indentation):
                block.append(lines[j])
                j += 1
                
            # Analyze the block
            block_code = '\n'.join(block)
            result = analyzer.analyze_code(block_code, 'python')
            
            # Store complexity for all lines in this block (overrides function complexity)
            for k in range(i+1, min(j+1, len(lines)+1)):
                line_complexities[k] = {
                    'time': result['time_complexity'],
                    'space': result['space_complexity'],
                    'block': True
                }
            
            i = j
        else:
            i += 1
    
    # Generate the output
    output_data = {
        'file': file_path,
        'overall': overall_result,
        'lines': line_hover_data,
        'functions': {}
    }
    
    # Collect function information
    for i, line_info in line_complexities.items():
        if 'function' in line_info:
            func_name = line_info['function']
            if func_name not in output_data['functions']:
                output_data['functions'][func_name] = {
                    'time': line_info['time'],
                    'space': line_info['space']
                }
    
    # Print summary information
    print(f"\033[1;36m📊 Overall complexity:\033[0m")
    print(f"  \033[1;33m⏱️  Time Complexity: {overall_result['time_complexity']}\033[0m")
    print(f"  \033[1;34m🧠 Space Complexity: {overall_result['space_complexity']}\033[0m")
    print("-" * 80)
    
    # Print function analysis
    print(f"\033[1;35m📝 Function Analysis:\033[0m")
    for func_name, func_info in output_data['functions'].items():
        print(f"\033[1m🔹 Function \033[1;32m'{func_name}'\033[0m\033[1m:\033[0m")
        print(f"  \033[1;33m⏱️  Time: {func_info['time']}\033[0m")
        print(f"  \033[1;34m🧠 Space: {func_info['space']}\033[0m")
    
    print("-" * 80)
    print(f"\033[1;35m📝 Line-by-Line Analysis:\033[0m")
    
    # Print each line with its complexity
    for i, line in enumerate(lines, 1):
        # Format line number with leading zeros
        line_num = f"{i:3d}"
        
        # Clean any control characters
        cleaned_line = line.replace('\r', '').replace('\n', '')
        
        if i in line_hover_data:
            hover_info = line_hover_data[i]
            time_str = f"\033[1;33m⏱️  Time: {hover_info['time']}\033[0m"
            space_str = f"\033[1;34m🧠 Space: {hover_info['space']}\033[0m"
            
            # Only show for non-trivial complexities or if it's a significant line
            if (hover_info['time'] != 'O(1)' or 
                hover_info['space'] != 'O(1)' or 
                re.search(r'^\s*(def|for|while|if|return)', line)):
                print(f"{line_num} | {cleaned_line}")
                print(f"    | {time_str} {space_str}")
            else:
                print(f"{line_num} | {cleaned_line}")
        else:
            print(f"{line_num} | {cleaned_line}")
    
    # Save the complexity data to a JSON file for the VS Code extension
    output_file = os.path.join(os.path.dirname(file_path), f"{os.path.basename(file_path)}.complexity.json")
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print("-" * 80)
    print(f"\033[1;36m📊 Overall complexity: Time: {overall_result['time_complexity']}, Space: {overall_result['space_complexity']}\033[0m")
    print(f"Complexity data saved to: {output_file}")

if __name__ == "__main__":
    # Allow specifying a file as argument or use default
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = 'main.py' 
    
    analyze_file(file_path) 