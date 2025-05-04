# Codizer - Real-time Code Complexity Analyzer

Codizer is a VS Code extension that analyzes your code in real-time to determine its time and space complexity. As you write code, Codizer provides immediate feedback on the algorithmic efficiency of your code.

## Features

- **Real-time Analysis:** Instantly see the time and space complexity of your code as you type
- **Line-by-line Analysis:** Click on a specific line to see its individual complexity
- **Multiple Language Support:** Currently supports Python, with more languages coming soon
- **Algorithm Recognition:** Automatically detects common algorithms like merge sort, bubble sort, and search algorithms
- **Comment Annotations:** Recognizes explicit time and space complexity annotations in comments

## What's New in 0.0.2

- **Improved Algorithm Detection:** More accurate identification of common algorithms
- **Better Nested Loop Analysis:** Correctly identifies complexity in complex nested structures
- **Explicit Annotation Support:** Add comments like `# Time Complexity: O(n log n)` for precise control
- **Fixed Merge Sort Detection:** Correctly identifies O(n log n) for merge sort implementations
- **Enhanced Space Complexity Analysis:** More accurate calculation of memory usage

## Requirements

- Python 3.8 or higher
- Django and Django REST Framework (installed automatically)

## Extension Setup

1. Clone this repository
2. Make sure you have Node.js and npm installed
3. Run `npm install` in the extension directory
4. Make sure you have Python installed and in your PATH
5. The extension will start the Django backend server automatically

## Backend Server Setup (Manual)

If you need to start the backend server manually:

1. Navigate to the `python_backend` directory
2. Activate the virtual environment:
   - On Windows: `.\venv\Scripts\activate`
   - On macOS/Linux: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the server: `python manage.py runserver`

## Usage

After installing the extension:

1. Open any Python file in VS Code
2. The extension will automatically analyze your code and display its time and space complexity in the status bar
3. As you type or move your cursor, the complexity display updates in real-time
4. Click on the complexity display in the status bar for more detailed information

### Using Explicit Annotations

You can explicitly specify complexity with comments:

```python
# Time Complexity: O(n log n)
# Space Complexity: O(n)
def merge_sort(arr):
    # Implementation...
```

## Extension Settings

* `codizer.showStatusBar`: Show/hide the complexity info in the status bar
* `codizer.analyzeOnType`: Enable/disable real-time analysis while typing

## How It Works

Codizer uses a combination of pattern recognition, Abstract Syntax Tree (AST) analysis, and algorithm classification to determine the time and space complexity of code. The VS Code extension sends your code to a Django backend server, which performs the analysis and returns the results.

## Limitations

- The complexity analysis is an estimation based on common patterns and may not be accurate for all code
- Currently only supports Python with limited complexity detection patterns
- May not accurately analyze complex algorithms or custom data structures

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
