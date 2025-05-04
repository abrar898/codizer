import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import * as cp from 'child_process';

let statusBarItem: vscode.StatusBarItem;
let outputChannel: vscode.OutputChannel;
let extensionContext: vscode.ExtensionContext;
let decorationTypes: Map<string, vscode.TextEditorDecorationType> = new Map();
let inlineDecorations: vscode.DecorationOptions[] = [];
let throttleTimer: NodeJS.Timeout | null = null;

export function activate(context: vscode.ExtensionContext) {
    console.log('Code Complexity Analyzer is now active!');

    // Store context for later use
    extensionContext = context;

    // Create output channel for verbose logs
    outputChannel = vscode.window.createOutputChannel('Code Complexity Analyzer');

    // Create status bar item
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'complexityAnalyzer.showDetails';
    updateStatusBar();
    statusBarItem.show();

    // Create decoration types for different complexities
    initializeDecorationTypes();

    // Register the status bar toggling in configuration
    context.subscriptions.push(vscode.workspace.onDidChangeConfiguration(e => {
        if (e.affectsConfiguration('complexityAnalyzer.showInStatusBar')) {
            updateStatusBar();
        }
    }));

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('complexityAnalyzer.analyzeFile', analyzeCurrentFile),
        vscode.commands.registerCommand('complexityAnalyzer.showDetails', showComplexityDetails),
        statusBarItem,
        outputChannel
    );

    // Add document change listener for real-time analysis
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument(event => {
            if (event.document.languageId === 'python') {
                // Throttle real-time analysis to avoid performance issues
                if (throttleTimer) {
                    clearTimeout(throttleTimer);
                }
                throttleTimer = setTimeout(() => {
                    analyzeCodeRealTime(event.document);
                }, 1000); // Analyze after 1 second of inactivity
            }
        })
    );

    // Analyze current file when active text editor changes
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(editor => {
            if (editor && editor.document.languageId === 'python') {
                analyzeCurrentFile();
                analyzeCodeRealTime(editor.document);
            } else {
                statusBarItem.text = '';
                statusBarItem.hide();
            }
        })
    );

    // Initial analysis of active file
    if (vscode.window.activeTextEditor && 
        vscode.window.activeTextEditor.document.languageId === 'python') {
        analyzeCurrentFile();
        analyzeCodeRealTime(vscode.window.activeTextEditor.document);
    }
}

function initializeDecorationTypes() {
    // Create decoration types for different complexity levels
    decorationTypes.set('O(1)', vscode.window.createTextEditorDecorationType({
        after: {
            margin: '0 0 0 10px',
            contentText: '🟢 O(1)',
            color: '#2ecc71'
        },
        rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
    }));
    
    decorationTypes.set('O(log n)', vscode.window.createTextEditorDecorationType({
        after: {
            margin: '0 0 0 10px',
            contentText: '🟢 O(log n)',
            color: '#27ae60'
        },
        rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
    }));
    
    decorationTypes.set('O(n)', vscode.window.createTextEditorDecorationType({
        after: {
            margin: '0 0 0 10px',
            contentText: '🟡 O(n)',
            color: '#f39c12'
        },
        rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
    }));
    
    decorationTypes.set('O(n log n)', vscode.window.createTextEditorDecorationType({
        after: {
            margin: '0 0 0 10px',
            contentText: '🟠 O(n log n)',
            color: '#e67e22'
        },
        rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
    }));
    
    decorationTypes.set('O(n²)', vscode.window.createTextEditorDecorationType({
        after: {
            margin: '0 0 0 10px',
            contentText: '🔴 O(n²)',
            color: '#e74c3c'
        },
        rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
    }));
    
    decorationTypes.set('O(n^2)', vscode.window.createTextEditorDecorationType({
        after: {
            margin: '0 0 0 10px',
            contentText: '🔴 O(n²)',
            color: '#e74c3c'
        },
        rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
    }));
    
    decorationTypes.set('O(n^3)', vscode.window.createTextEditorDecorationType({
        after: {
            margin: '0 0 0 10px',
            contentText: '🔴 O(n³)',
            color: '#c0392b'
        },
        rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
    }));
    
    decorationTypes.set('O(2^n)', vscode.window.createTextEditorDecorationType({
        after: {
            margin: '0 0 0 10px',
            contentText: '⚫ O(2^n)',
            color: '#9b59b6'
        },
        rangeBehavior: vscode.DecorationRangeBehavior.ClosedClosed
    }));
}

async function analyzeCodeRealTime(document: vscode.TextDocument) {
    const editor = vscode.window.activeTextEditor;
    if (!editor || editor.document !== document) {
        return;
    }

    // Check if real-time analysis is enabled
    const realTimeAnalysisEnabled = vscode.workspace.getConfiguration('complexityAnalyzer').get('realTimeAnalysis');
    if (!realTimeAnalysisEnabled) {
        return;
    }

    // Get document text
    const text = document.getText();
    
    // Extract function definitions with regex
    const functionRegex = /def\s+(\w+)\s*\(([^)]*)\).*?:/g;
    const forLoopRegex = /for\s+\w+\s+in\s+/g;
    const whileLoopRegex = /while\s+/g;
    const nestedLoopRegex = /for.*for|while.*for|for.*while|while.*while/g;
    const tripleNestedLoopRegex = /for.*for.*for|while.*while.*while|for.*while.*for/g;
    
    // Clear all existing decorations
    decorationTypes.forEach(decorationType => {
        editor.setDecorations(decorationType, []);
    });
    
    // Don't proceed if inline annotations are disabled
    const showInlineComplexity = vscode.workspace.getConfiguration('complexityAnalyzer').get('showInlineComplexity');
    if (!showInlineComplexity) {
        return;
    }
    
    // Reset decorations collection
    const decorationsMap: Map<string, vscode.Range[]> = new Map();
    decorationTypes.forEach((_, key) => {
        decorationsMap.set(key, []);
    });
    
    // Simple heuristics for complexity
    let match;
    
    // Check for function definitions
    while ((match = functionRegex.exec(text)) !== null) {
        const funcStartPos = document.positionAt(match.index);
        const line = document.lineAt(funcStartPos.line);
        
        // Look for patterns in function body to determine complexity
        const funcEndLine = findFunctionEndLine(document, funcStartPos.line);
        if (funcEndLine === -1) continue;
        
        const functionBody = document.getText(new vscode.Range(
            funcStartPos.line, 0,
            funcEndLine, document.lineAt(funcEndLine).text.length
        ));
        
        let complexity = 'O(1)'; // Default
        
        // Check for nested loops (most expensive operations first)
        if (tripleNestedLoopRegex.test(functionBody)) {
            complexity = 'O(n^3)';
        } else if (nestedLoopRegex.test(functionBody)) {
            complexity = 'O(n^2)';
        } else if (forLoopRegex.test(functionBody) || whileLoopRegex.test(functionBody)) {
            complexity = 'O(n)';
        } else if (functionBody.includes('sort') || functionBody.includes('sorted')) {
            complexity = 'O(n log n)';
        } else if (functionBody.includes('binary_search') || 
                  (functionBody.includes('mid') && functionBody.includes('//'))) {
            complexity = 'O(log n)';
        }
        
        // Check for recursive calls which could indicate exponential complexity
        if (new RegExp(`${match[1]}\\s*\\(`).test(functionBody)) {
            complexity = 'O(2^n)';
        }
        
        // Add range to the correct complexity decoration group
        if (decorationsMap.has(complexity)) {
            const ranges = decorationsMap.get(complexity) || [];
            ranges.push(line.range);
            decorationsMap.set(complexity, ranges);
        }
    }
    
    // Apply all decorations
    decorationsMap.forEach((ranges, complexityKey) => {
        if (decorationTypes.has(complexityKey)) {
            editor.setDecorations(decorationTypes.get(complexityKey)!, ranges);
        }
    });
}

function findFunctionEndLine(document: vscode.TextDocument, startLine: number): number {
    const startIndent = document.lineAt(startLine).firstNonWhitespaceCharacterIndex;
    
    for (let i = startLine + 1; i < document.lineCount; i++) {
        const line = document.lineAt(i);
        if (line.text.trim().length === 0) continue;
        
        const currentIndent = line.firstNonWhitespaceCharacterIndex;
        if (currentIndent <= startIndent) {
            return i - 1;
        }
    }
    
    return document.lineCount - 1;
}

function updateStatusBar() {
    const showInStatusBar = vscode.workspace.getConfiguration('complexityAnalyzer').get('showInStatusBar');
    
    if (showInStatusBar) {
        statusBarItem.show();
    } else {
        statusBarItem.hide();
    }
}

async function analyzeCurrentFile() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        return;
    }

    const document = editor.document;
    if (document.languageId !== 'python') {
        vscode.window.showInformationMessage('Complexity analysis is only available for Python files.');
        return;
    }

    // Save the document if needed
    if (document.isDirty) {
        await document.save();
    }

    const filePath = document.uri.fsPath;
    outputChannel.appendLine(`Analyzing file: ${filePath}`);

    try {
        const results = await runPythonAnalysis(filePath);
        if (results.error) {
            vscode.window.showErrorMessage(`Error analyzing file: ${results.message}`);
            outputChannel.appendLine(`Error: ${results.message}`);
            return;
        }

        // Update status bar
        const showInStatusBar = vscode.workspace.getConfiguration('complexityAnalyzer').get('showInStatusBar');
        if (showInStatusBar) {
            statusBarItem.text = `$(symbol-property) CC: ${results.avg_complexity}`;
            statusBarItem.tooltip = 'Click to view detailed complexity analysis';
            statusBarItem.show();
        }

        // Store results in temporary file
        const tempFile = path.join(extensionContext.globalStorageUri.fsPath, `${path.basename(filePath)}.json`);
        try {
            // Ensure directory exists
            if (!fs.existsSync(path.dirname(tempFile))) {
                fs.mkdirSync(path.dirname(tempFile), { recursive: true });
            }
            fs.writeFileSync(tempFile, JSON.stringify(results, null, 2));
        } catch (err) {
            outputChannel.appendLine(`Error saving results: ${err}`);
        }

        outputChannel.appendLine(`Analysis complete: Avg. Complexity: ${results.avg_complexity}`);
    } catch (err) {
        vscode.window.showErrorMessage(`Error running complexity analysis: ${err}`);
        outputChannel.appendLine(`Error: ${err}`);
    }
}

interface AnalysisResult {
    error?: boolean;
    message?: string;
    avg_complexity: number;
    lines_of_code: number;
    num_functions: number;
    num_classes: number;
    file_name: string;
    functions: {
        [key: string]: {
            lineno: number;
            cyclomatic_complexity: number;
            time_complexity: string;
            space_complexity: string;
        }
    };
}

// Execute the Python script to analyze complexity
async function runPythonAnalysis(filePath: string): Promise<AnalysisResult> {
    return new Promise((resolve, reject) => {
        // Get Python path from configuration
        const pythonPath = vscode.workspace.getConfiguration('complexityAnalyzer').get<string>('pythonPath') || 'python';
        
        // Path to the analysis script
        const scriptPath = path.join(__dirname, '..', 'src', 'analyze_complexity.py');
        
        let stdout = '';
        let stderr = '';
        
        // Execute using spawn from child_process
        const childProcess = cp.spawn(
            pythonPath, 
            [scriptPath, filePath],
            { shell: true }
        );
        
        childProcess.stdout.on('data', (data: Buffer) => {
            stdout += data.toString();
        });
        
        childProcess.stderr.on('data', (data: Buffer) => {
            stderr += data.toString();
        });
        
        childProcess.on('close', (code: number) => {
            if (code !== 0) {
                outputChannel.appendLine(`Python process exited with code ${code}`);
                outputChannel.appendLine(`Error: ${stderr}`);
                reject(new Error(stderr || `Process exited with code ${code}`));
                return;
            }
            
            try {
                const results = JSON.parse(stdout);
                resolve(results);
            } catch (err: any) {
                outputChannel.appendLine(`Error parsing JSON: ${err}`);
                outputChannel.appendLine(`Raw output: ${stdout}`);
                reject(new Error('Failed to parse analysis results'));
            }
        });
        
        childProcess.on('error', (err: Error) => {
            reject(err);
        });
    });
}

async function showComplexityDetails() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showInformationMessage('No active editor to analyze.');
        return;
    }

    const document = editor.document;
    if (document.languageId !== 'python') {
        vscode.window.showInformationMessage('Complexity analysis is only available for Python files.');
        return;
    }

    // Try to get cached results or run analysis
    const filePath = document.uri.fsPath;
    const tempFile = path.join(extensionContext.globalStorageUri.fsPath, `${path.basename(filePath)}.json`);
    
    let results: AnalysisResult;
    try {
        if (fs.existsSync(tempFile)) {
            const rawData = fs.readFileSync(tempFile, 'utf8');
            results = JSON.parse(rawData);
        } else {
            results = await runPythonAnalysis(filePath);
        }
    } catch (err) {
        vscode.window.showErrorMessage(`Error retrieving analysis results: ${err}`);
        return;
    }

    // Create and show webview
    const panel = vscode.window.createWebviewPanel(
        'complexityDetails',
        'Code Complexity Analysis',
        vscode.ViewColumn.Beside,
        {
            enableScripts: true
        }
    );

    // Generate the HTML content
    panel.webview.html = getWebviewContent(results, document);
}

function getWebviewContent(results: AnalysisResult, document: vscode.TextDocument): string {
    const functionRows = Object.entries(results.functions).map(([name, data]) => {
        return `
            <tr>
                <td>${name}</td>
                <td>${data.lineno}</td>
                <td>${data.cyclomatic_complexity}</td>
                <td>${data.time_complexity}</td>
                <td>${data.space_complexity}</td>
            </tr>
        `;
    }).join('');

    return `
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Code Complexity Analysis</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 20px;
                    color: var(--vscode-foreground);
                    background-color: var(--vscode-editor-background);
                }
                h1, h2 {
                    color: var(--vscode-editor-foreground);
                }
                .summary {
                    background-color: var(--vscode-panel-background);
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid var(--vscode-panel-border);
                }
                th {
                    background-color: var(--vscode-tab-activeBackground);
                }
                tr:hover {
                    background-color: var(--vscode-list-hoverBackground);
                }
                .complexity-high {
                    color: #e74c3c;
                }
                .complexity-medium {
                    color: #f39c12;
                }
                .complexity-low {
                    color: #2ecc71;
                }
                .legend {
                    display: flex;
                    margin-top: 15px;
                }
                .legend-item {
                    margin-right: 20px;
                    display: flex;
                    align-items: center;
                }
                .legend-color {
                    width: 15px;
                    height: 15px;
                    margin-right: 5px;
                    display: inline-block;
                }
            </style>
        </head>
        <body>
            <h1>Code Complexity Analysis: ${results.file_name}</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <p>Lines of Code: ${results.lines_of_code}</p>
                <p>Number of Functions: ${results.num_functions}</p>
                <p>Number of Classes: ${results.num_classes}</p>
                <p>Average Cyclomatic Complexity: ${results.avg_complexity}</p>
            </div>
            
            <h2>Function Analysis</h2>
            <table>
                <thead>
                    <tr>
                        <th>Function</th>
                        <th>Line</th>
                        <th>Cyclomatic Complexity</th>
                        <th>Time Complexity</th>
                        <th>Space Complexity</th>
                    </tr>
                </thead>
                <tbody>
                    ${functionRows}
                </tbody>
            </table>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #2ecc71;"></div>
                    <span>Low Complexity (1-5)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #f39c12;"></div>
                    <span>Medium Complexity (6-10)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #e74c3c;"></div>
                    <span>High Complexity (>10)</span>
                </div>
            </div>
            
            <script>
                // Apply color coding based on complexity
                document.querySelectorAll('tbody tr').forEach(row => {
                    const complexityCell = row.cells[2];
                    const complexity = parseInt(complexityCell.textContent);
                    
                    if (complexity > 10) {
                        complexityCell.className = 'complexity-high';
                    } else if (complexity > 5) {
                        complexityCell.className = 'complexity-medium';
                    } else {
                        complexityCell.className = 'complexity-low';
                    }
                });
            </script>
        </body>
        </html>
    `;
}

export function deactivate() {
    // Clean up resources
    if (statusBarItem) {
        statusBarItem.dispose();
    }
    if (outputChannel) {
        outputChannel.dispose();
    }
} 