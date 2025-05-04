const vscode = require('vscode');
const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('Complexity Analyzer is now active');

    // Register the command to analyze the current file
    let analyzeCommand = vscode.commands.registerCommand('complexity-analyzer.analyze', function () {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showErrorMessage('No active editor found');
            return;
        }

        const document = editor.document;
        if (document.languageId !== 'python') {
            vscode.window.showErrorMessage('Only Python files are supported currently');
            return;
        }

        // Save the file before analysis
        document.save().then(() => {
            const filePath = document.fileName;
            const pythonScriptPath = path.join(__dirname, '..', '..', 'analyze_complexity.py');
            
            // Show progress
            vscode.window.withProgress({
                location: vscode.ProgressLocation.Notification,
                title: "Analyzing complexity",
                cancellable: true
            }, (progress, token) => {
                return new Promise(resolve => {
                    progress.report({ increment: 0, message: "Starting analysis..." });
                    
                    // Run the Python script to analyze complexity
                    const command = `python "${pythonScriptPath}" "${filePath}"`;
                    
                    exec(command, (error, stdout, stderr) => {
                        if (error) {
                            vscode.window.showErrorMessage(`Analysis failed: ${error.message}`);
                            console.error(`Error: ${error.message}`);
                            resolve();
                            return;
                        }
                        
                        if (stderr) {
                            console.error(`Stderr: ${stderr}`);
                        }
                        
                        progress.report({ increment: 100, message: "Analysis complete" });
                        vscode.window.showInformationMessage('Complexity analysis complete');
                        resolve();
                        
                        // Create a new terminal and show the output
                        const terminal = vscode.window.createTerminal('Complexity Analysis');
                        terminal.show();
                        terminal.sendText(`echo "${stdout.replace(/"/g, '\\"').replace(/\n/g, '\\n')}"`);
                    });
                });
            });
        });
    });

    // Register a hover provider for Python files
    let hoverProvider = vscode.languages.registerHoverProvider('python', {
        provideHover(document, position, token) {
            // Generate the complexity data filename
            const filePath = document.fileName;
            const complexityFilePath = `${filePath}.complexity.json`;
            
            // Check if complexity data exists
            if (!fs.existsSync(complexityFilePath)) {
                return null;
            }
            
            try {
                // Read the complexity data
                const data = JSON.parse(fs.readFileSync(complexityFilePath, 'utf8'));
                const lineNumber = position.line + 1; // VSCode is 0-indexed, our data is 1-indexed
                
                // Check if we have complexity data for this line
                if (data.lines && data.lines[lineNumber]) {
                    const lineData = data.lines[lineNumber];
                    
                    // Create markdown content for hover
                    const markdownContent = new vscode.MarkdownString();
                    markdownContent.isTrusted = true;
                    
                    // Add time and space complexity
                    markdownContent.appendMarkdown(`**Time Complexity:** ${lineData.time}\n\n`);
                    markdownContent.appendMarkdown(`**Space Complexity:** ${lineData.space}`);
                    
                    // Add function information if available
                    const functionInfo = getFunctionForLine(data, lineNumber);
                    if (functionInfo) {
                        markdownContent.appendMarkdown(`\n\n**Function:** ${functionInfo.name}`);
                        markdownContent.appendMarkdown(`\n\n**Function Time Complexity:** ${functionInfo.time}`);
                        markdownContent.appendMarkdown(`\n\n**Function Space Complexity:** ${functionInfo.space}`);
                    }
                    
                    // Add overall information
                    markdownContent.appendMarkdown(`\n\n---\n\n**Overall Time Complexity:** ${data.overall.time_complexity}`);
                    markdownContent.appendMarkdown(`\n\n**Overall Space Complexity:** ${data.overall.space_complexity}`);
                    
                    return new vscode.Hover(markdownContent);
                }
            } catch (error) {
                console.error(`Error providing hover: ${error.message}`);
            }
            
            return null;
        }
    });

    // Helper function to get function info for a line
    function getFunctionForLine(data, lineNumber) {
        // Check if we have this info directly in line_complexities
        for (const line in data.line_complexities) {
            if (parseInt(line) === lineNumber && data.line_complexities[line].function) {
                const funcName = data.line_complexities[line].function;
                return {
                    name: funcName,
                    time: data.functions[funcName].time,
                    space: data.functions[funcName].space
                };
            }
        }
        
        // Otherwise check if the line is within a function range
        for (const funcName in data.functions) {
            if (data.functions[funcName].start_line <= lineNumber && 
                data.functions[funcName].end_line >= lineNumber) {
                return {
                    name: funcName,
                    time: data.functions[funcName].time,
                    space: data.functions[funcName].space
                };
            }
        }
        
        return null;
    }

    // Add status bar item to show overall complexity
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'complexity-analyzer.analyze';
    context.subscriptions.push(statusBarItem);
    
    // Update status bar when active editor changes
    function updateStatusBar() {
        const editor = vscode.window.activeTextEditor;
        if (!editor || editor.document.languageId !== 'python') {
            statusBarItem.hide();
            return;
        }
        
        const filePath = editor.document.fileName;
        const complexityFilePath = `${filePath}.complexity.json`;
        
        if (fs.existsSync(complexityFilePath)) {
            try {
                const data = JSON.parse(fs.readFileSync(complexityFilePath, 'utf8'));
                statusBarItem.text = `$(clock) ${data.overall.time_complexity} | $(database) ${data.overall.space_complexity}`;
                statusBarItem.tooltip = 'Click to re-analyze complexity';
                statusBarItem.show();
            } catch (error) {
                statusBarItem.hide();
            }
        } else {
            statusBarItem.text = '$(search) Analyze Complexity';
            statusBarItem.tooltip = 'Click to analyze complexity';
            statusBarItem.show();
        }
    }
    
    // Register event listeners
    context.subscriptions.push(
        vscode.window.onDidChangeActiveTextEditor(updateStatusBar),
        vscode.workspace.onDidSaveTextDocument(document => {
            if (document.languageId === 'python') {
                updateStatusBar();
            }
        })
    );
    
    // Update status bar on activation
    updateStatusBar();

    context.subscriptions.push(analyzeCommand, hoverProvider, statusBarItem);
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
}; 