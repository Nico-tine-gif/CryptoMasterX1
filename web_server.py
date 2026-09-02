#!/usr/bin/env python3
import os
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class CryptoWebHandler(BaseHTTPRequestHandler):
    crypto_dir = os.path.expanduser("~/CryptoMasterX1")
    command_path = os.path.join(crypto_dir, "command.txt")
    response_path = os.path.join(crypto_dir, "response.txt")
    log_path = os.path.join(crypto_dir, "auto.log")
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.get_html().encode('utf-8'))
            
        elif parsed.path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = self.get_status()
            self.wfile.write(json.dumps(status).encode('utf-8'))
            
        elif parsed.path == '/api/log':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            log = self.get_log()
            self.wfile.write(log.encode('utf-8'))
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        
        if parsed.path == '/api/command':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            command = data.get('command', '')
            
            response = self.send_command(command)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'response': response}).encode('utf-8'))
    
    def get_html(self):
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CryptoMasterX1 - Web Interface</title>
            <style>
                * { margin: 0; padding: 0; box-sizing: border-box; }
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: #0a0e27;
                    color: #00ff88;
                    padding: 16px;
                    min-height: 100vh;
                }
                .container { max-width: 800px; margin: 0 auto; }
                .header {
                    background: linear-gradient(135deg, #1a1f3a 0%, #0a0e27 100%);
                    padding: 20px;
                    border-radius: 12px;
                    border: 1px solid #00ff88;
                    margin-bottom: 20px;
                    text-align: center;
                }
                .header h1 {
                    font-size: 24px;
                    color: #00ff88;
                    text-shadow: 0 0 20px rgba(0,255,136,0.3);
                }
                .header .status {
                    font-size: 14px;
                    margin-top: 8px;
                    color: #66ffaa;
                }
                .terminal {
                    background: #0a0e27;
                    border: 1px solid #00ff88;
                    border-radius: 12px;
                    padding: 16px;
                    min-height: 300px;
                    max-height: 400px;
                    overflow-y: auto;
                    font-family: 'Courier New', monospace;
                    font-size: 13px;
                    line-height: 1.6;
                    margin-bottom: 16px;
                }
                .terminal .prompt { color: #00ff88; }
                .terminal .response { color: #88ffcc; }
                .terminal .error { color: #ff4466; }
                .input-area {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 12px;
                }
                .input-area input {
                    flex: 1;
                    padding: 12px 16px;
                    background: #1a1f3a;
                    border: 1px solid #00ff88;
                    border-radius: 8px;
                    color: #00ff88;
                    font-size: 16px;
                    outline: none;
                }
                .input-area input::placeholder { color: #446688; }
                .input-area input:focus {
                    border-color: #66ffaa;
                    box-shadow: 0 0 20px rgba(0,255,136,0.1);
                }
                .input-area button {
                    padding: 12px 24px;
                    background: #00ff88;
                    color: #0a0e27;
                    border: none;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s;
                }
                .input-area button:hover {
                    background: #66ffaa;
                    transform: scale(1.02);
                }
                .buttons {
                    display: flex;
                    gap: 8px;
                    flex-wrap: wrap;
                }
                .buttons button {
                    padding: 8px 16px;
                    background: transparent;
                    border: 1px solid #00ff88;
                    color: #00ff88;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 13px;
                    transition: all 0.3s;
                }
                .buttons button:hover {
                    background: #00ff88;
                    color: #0a0e27;
                }
                .log-view {
                    margin-top: 16px;
                    background: #0a0e27;
                    border: 1px solid #446688;
                    border-radius: 8px;
                    padding: 12px;
                    max-height: 200px;
                    overflow-y: auto;
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                    color: #88bbdd;
                }
                .log-view .log-entry {
                    padding: 2px 0;
                    border-bottom: 1px solid #112233;
                }
                .log-view .timestamp {
                    color: #446688;
                    margin-right: 8px;
                }
                .clear-btn {
                    background: #ff4466 !important;
                    color: white !important;
                    border-color: #ff4466 !important;
                }
                .clear-btn:hover {
                    background: #ff6688 !important;
                    color: white !important;
                }
                @media (max-width: 480px) {
                    .input-area { flex-direction: column; }
                    .header h1 { font-size: 20px; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 CryptoMasterX1</h1>
                    <div class="status" id="status">Connecting...</div>
                </div>
                
                <div class="terminal" id="terminal">
                    <div class="prompt">$ Welcome to CryptoMasterX1</div>
                    <div class="prompt">$ Type a command to begin</div>
                </div>
                
                <div class="input-area">
                    <input type="text" id="cmdInput" placeholder="Enter command (status, price, balance, help)" />
                    <button onclick="sendCommand()">Send</button>
                </div>
                
                <div class="buttons">
                    <button onclick="sendCommandWith('status')">📊 Status</button>
                    <button onclick="sendCommandWith('price')">💰 Price</button>
                    <button onclick="sendCommandWith('balance')">🏦 Balance</button>
                    <button onclick="sendCommandWith('help')">❓ Help</button>
                    <button onclick="clearTerminal()" class="clear-btn">🗑️ Clear</button>
                    <button onclick="refreshLog()">📋 Refresh Log</button>
                </div>
                
                <div class="log-view" id="logView">
                    <div>Logs will appear here...</div>
                </div>
            </div>
            
            <script>
                const terminal = document.getElementById('terminal');
                const cmdInput = document.getElementById('cmdInput');
                const logView = document.getElementById('logView');
                
                setInterval(updateStatus, 5000);
                setInterval(refreshLog, 10000);
                
                cmdInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') sendCommand();
                });
                
                function sendCommand() {
                    const cmd = cmdInput.value.trim();
                    if (!cmd) return;
                    
                    cmdInput.value = '';
                    addToTerminal('$ ' + cmd, 'prompt');
                    
                    fetch('/api/command', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({command: cmd})
                    })
                    .then(response => response.json())
                    .then(data => {
                        addToTerminal(data.response, 'response');
                    })
                    .catch(error => {
                        addToTerminal('Error: ' + error, 'error');
                    });
                }
                
                function sendCommandWith(cmd) {
                    cmdInput.value = cmd;
                    sendCommand();
                }
                
                function addToTerminal(text, className = '') {
                    const div = document.createElement('div');
                    div.className = className;
                    div.textContent = text;
                    terminal.appendChild(div);
                    terminal.scrollTop = terminal.scrollHeight;
                }
                
                function clearTerminal() {
                    terminal.innerHTML = '';
                    addToTerminal('$ Terminal cleared', 'prompt');
                }
                
                function updateStatus() {
                    fetch('/api/status')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('status').textContent = data.status || 'Connected';
                        })
                        .catch(() => {
                            document.getElementById('status').textContent = '⚠️ Disconnected';
                        });
                }
                
                function refreshLog() {
                    fetch('/api/log')
                        .then(response => response.text())
                        .then(data => {
                            const lines = data.split('\\n').filter(line => line.trim());
                            logView.innerHTML = lines.slice(-20).map(line => {
                                const parts = line.match(/^\[(.+?)\]/);
                                if (parts) {
                                    const timestamp = parts[1];
                                    const message = line.replace(/^\[.+?\]\s*/, '');
                                    return '<div class="log-entry"><span class="timestamp">[' + timestamp + ']</span> ' + message + '</div>';
                                }
                                return '<div class="log-entry">' + line + '</div>';
                            }).join('');
                        })
                        .catch(() => {});
                }
                
                setTimeout(updateStatus, 1000);
                setTimeout(refreshLog, 2000);
            </script>
        </body>
        </html>
        """
    
    def get_status(self):
        status = {"status": "Running", "timestamp": time.time()}
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        status['last_log'] = lines[-1].strip()
            except:
                pass
        return status
    
    def get_log(self):
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r') as f:
                    return f.read()
            except:
                return "Error reading log"
        return "No log file found"
    
    def send_command(self, command):
        try:
            open(self.response_path, 'w').close()
            
            with open(self.command_path, 'w') as f:
                f.write(command)
            
            time.sleep(0.5)
            
            if os.path.exists(self.response_path):
                with open(self.response_path, 'r') as f:
                    response = f.read().strip()
                return response if response else "No response"
            else:
                return "No response file found"
                
        except Exception as e:
            return f"Error: {str(e)}"

def run_server():
    port = 8080
    server = HTTPServer(('0.0.0.0', port), CryptoWebHandler)
    print("\n" + "="*50)
    print("🚀 CryptoMasterX1 Web Server Running!")
    print("="*50)
    print(f"📱 Local: http://localhost:{port}")
    print(f"🌐 Phone: http://127.0.0.1:{port}")
    print("="*50)
    print("\n💡 To access from another device, find your IP with:")
    print("   ifconfig | grep inet")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == '__main__':
    run_server()
