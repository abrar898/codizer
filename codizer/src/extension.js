"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
// The module 'vscode' contains the VS Code extensibility API
// Import the module and reference it with the alias vscode in your code below
const vscode = __importStar(require("vscode"));
const http = __importStar(require("http"));
const path = __importStar(require("path"));
const child_process = __importStar(require("child_process"));
// Initialize Django server process
let serverProcess = null;
// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
function activate(context) {
    // Use the console to output diagnostic information (console.log) and errors (console.error)
    // This line of code will only be executed once when your extension is activated
    console.log('Congratulations, your extension "codizer" is now active!');
    // Start Django server
    startDjangoServer(context.extensionPath);
    // Register code analyzer command
    const analyzeDisposable = vscode.commands.registerCommand('codizer.analyzeComplexity', async () => {
        await analyzeCurrentDocument();
    });
    // Show complexity on document change
    const changeDisposable = vscode.workspace.onDidChangeTextDocument((event) => {
        if (event.document === vscode.window.activeTextEditor?.document) {
            analyzeCurrentDocument();
        }
    });
    // Show complexity on active editor change
    const selectionDisposable = vscode.window.onDidChangeTextEditorSelection((event) => {
        analyzeCurrentLine(event.textEditor);
    });
    // Register status bar item
    const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.command = 'codizer.analyzeComplexity';
    context.subscriptions.push(analyzeDisposable, changeDisposable, selectionDisposable, statusBarItem);
    // Analyze code on startup if a document is open
    if (vscode.window.activeTextEditor) {
        analyzeCurrentDocument();
    }
    // Update status bar to show complexity for currently selected line
    async function analyzeCurrentLine(editor) {
        const document = editor.document;
        const selection = editor.selection;
        if (selection.isEmpty) {
            // Get the current line
            const lineNumber = selection.active.line;
            const line = document.lineAt(lineNumber).text;
            if (line.trim().length > 0) {
                // Analyze just this line
                const language = document.languageId;
                const result = await analyzeCode(line, language);
                // Update status bar
                statusBarItem.text = `Time: ${result.time_complexity} | Space: ${result.space_complexity}`;
                statusBarItem.show();
            }
        }
    }
    // Analyze the current document
    async function analyzeCurrentDocument() {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            return;
        }
        const document = editor.document;
        const language = document.languageId;
        const code = document.getText();
        if (code.trim().length === 0) {
            return;
        }
        try {
            const result = await analyzeCode(code, language);
            // Show complexity in status bar
            statusBarItem.text = `Overall - Time: ${result.time_complexity} | Space: ${result.space_complexity}`;
            statusBarItem.show();
            // Optionally show in an information message
            // vscode.window.showInformationMessage(`Time complexity: ${result.time_complexity}, Space complexity: ${result.space_complexity}`);
        }
        catch (error) {
            console.error('Error analyzing code:', error);
            statusBarItem.hide();
        }
    }
    // Send code to backend for analysis
    async function analyzeCode(code, language) {
        return new Promise((resolve, reject) => {
            // Default result if analysis fails
            const defaultResult = {
                time_complexity: 'Unknown',
                space_complexity: 'Unknown'
            };
            try {
                const postData = JSON.stringify({
                    code: code,
                    language: language
                });
                const options = {
                    hostname: 'localhost',
                    port: 8000,
                    path: '/api/analyze/',
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Content-Length': Buffer.byteLength(postData)
                    }
                };
                const req = http.request(options, (res) => {
                    let data = '';
                    res.on('data', (chunk) => {
                        data += chunk;
                    });
                    res.on('end', () => {
                        if (res.statusCode !== 200) {
                            console.error(`HTTP Error: ${res.statusCode}`);
                            resolve(defaultResult);
                            return;
                        }
                        try {
                            const result = JSON.parse(data);
                            resolve(result);
                        }
                        catch (e) {
                            console.error('Error parsing response:', e);
                            resolve(defaultResult);
                        }
                    });
                });
                req.on('error', (error) => {
                    console.error('Error sending request:', error);
                    resolve(defaultResult);
                });
                req.write(postData);
                req.end();
            }
            catch (error) {
                console.error('Error in analysis:', error);
                resolve(defaultResult);
            }
        });
    }
}
function startDjangoServer(extensionPath) {
    // Path to the Django project
    const pythonBackendPath = path.join(extensionPath, '..', 'python_backend');
    // Check if Python is available
    try {
        const pythonPath = process.platform === 'win32' ?
            path.join(pythonBackendPath, 'venv', 'Scripts', 'python.exe') :
            path.join(pythonBackendPath, 'venv', 'bin', 'python');
        // Start Django server
        serverProcess = child_process.spawn(pythonPath, [path.join(pythonBackendPath, 'manage.py'), 'runserver'], { cwd: pythonBackendPath });
        // Handle server output
        serverProcess.stdout?.on('data', (data) => {
            console.log(`Django Server: ${data}`);
        });
        serverProcess.stderr?.on('data', (data) => {
            console.error(`Django Server Error: ${data}`);
        });
        console.log('Django server started!');
    }
    catch (error) {
        console.error('Failed to start Django server:', error);
        vscode.window.showErrorMessage('Failed to start Django server. Make sure Python is installed with required packages.');
    }
}
// This method is called when your extension is deactivated
function deactivate() {
    // Stop the Django server
    if (serverProcess) {
        serverProcess.kill();
        console.log('Django server stopped');
    }
}
//# sourceMappingURL=extension.js.map