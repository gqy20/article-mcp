#!/usr/bin/env node

const { spawn } = require('child_process');
const path = require('path');

// Get command line arguments
const args = process.argv.slice(2);

// Default to 'server' command if no args provided
const command = args.length > 0 ? args : ['server'];

// Try to run with uvx first, fallback to python
function runWithUvx() {
    const uvxProcess = spawn('uvx', ['article-mcp@latest', ...command], {
        stdio: 'inherit',
        env: {
            ...process.env,
            PYTHONUNBUFFERED: '1'
        }
    });

    uvxProcess.on('error', (error) => {
        console.error('uvx failed, trying with git clone method...');
        runWithGitClone();
    });

    uvxProcess.on('exit', (code) => {
        process.exit(code);
    });
}

function runWithGitClone() {
    // Alternative: clone and run from source
    const { execSync } = require('child_process');
    
    try {
        // Clone the repository to a temp directory
        const tempDir = path.join(require('os').tmpdir(), 'article-mcp-' + Date.now());
        execSync(`git clone https://github.com/gqy20/article-mcp.git "${tempDir}"`, { stdio: 'inherit' });
        
        // Run the server
        const pythonProcess = spawn('python', [path.join(tempDir, 'main.py'), ...command], {
            stdio: 'inherit',
            env: {
                ...process.env,
                PYTHONUNBUFFERED: '1'
            },
            cwd: tempDir
        });

        pythonProcess.on('exit', (code) => {
            // Cleanup temp directory
            try {
                require('fs').rmSync(tempDir, { recursive: true, force: true });
            } catch (e) {
                // Ignore cleanup errors
            }
            process.exit(code);
        });
    } catch (error) {
        console.error('Failed to run Article MCP server:', error.message);
        process.exit(1);
    }
}

// Start with uvx method
runWithUvx(); 