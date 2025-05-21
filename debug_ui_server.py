#!/usr/bin/env python3
"""
Debug UI Server

A simple HTTP server to view the debugging sessions for the answer processor.
"""

import os
import re
import json
import http.server
import socketserver
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import webbrowser
import threading
import time

DEBUG_DIR = "debug_sessions"

# Create debug_sessions directory if it doesn't exist
os.makedirs(DEBUG_DIR, exist_ok=True)

class DebugUIHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for the debug UI."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        # Route requests
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self._generate_index_page().encode())
        elif self.path.startswith('/sessions/'):
            session_id = self.path[10:]
            if session_id:
                self._serve_debug_session(session_id)
            else:
                self._list_sessions()
        elif self.path.startswith('/api/sessions'):
            self._api_list_sessions()
        else:
            # Serve files from the debug_sessions directory
            if self.path.startswith('/debug_sessions/'):
                # Strip the /debug_sessions/ prefix
                file_path = self.path[15:]
                self._serve_static_file(os.path.join(DEBUG_DIR, file_path))
            else:
                # Default 404
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>404 Not Found</h1>')
    
    def _generate_index_page(self) -> str:
        """Generate the index page HTML."""
        sessions = self._get_debug_sessions()
        
        html = """<!DOCTYPE html>
        <html>
        <head>
            <title>Answer Processing Debug UI</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .session-list { margin-top: 20px; }
                .session-card { 
                    border: 1px solid #ddd; 
                    border-radius: 5px; 
                    padding: 15px; 
                    margin-bottom: 15px; 
                    background-color: #f9f9f9;
                }
                .session-card h3 { margin-top: 0; }
                .session-meta { color: #666; font-size: 0.9em; }
                .session-text { margin: 10px 0; }
                .session-text strong { color: #333; }
                .session-actions { margin-top: 10px; }
                .btn { 
                    display: inline-block; 
                    padding: 6px 12px; 
                    background-color: #4CAF50; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 4px;
                }
                .refresh-btn {
                    margin-left: 10px;
                    background-color: #2196F3;
                }
            </style>
        </head>
        <body>
            <h1>Answer Processing Debug UI</h1>
            <p>View debug sessions from the improved answer processor.</p>
            
            <button class="btn refresh-btn" onclick="window.location.reload()">Refresh</button>
            
            <div class="session-list">
        """
        
        if not sessions:
            html += """
                <div class="session-card">
                    <h3>No Debug Sessions Found</h3>
                    <p>Run the improved answer processor to generate debug sessions.</p>
                </div>
            """
        else:
            # Sort sessions by timestamp (newest first)
            sessions.sort(key=lambda s: s.get('timestamp', ''), reverse=True)
            
            for session in sessions:
                session_id = session.get('session_id', 'unknown')
                question = session.get('question', 'Unknown question')
                timestamp = session.get('timestamp', 'Unknown time')
                steps_count = len(session.get('steps', []))
                
                html += f"""
                <div class="session-card">
                    <h3>Session: {session_id}</h3>
                    <div class="session-meta">Created: {timestamp} | Steps: {steps_count}</div>
                    <div class="session-text"><strong>Question:</strong> {question}</div>
                    <div class="session-actions">
                        <a href="/debug_sessions/{session_id}.html" class="btn" target="_blank">View Debug Session</a>
                    </div>
                </div>
                """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _get_debug_sessions(self) -> List[Dict[str, Any]]:
        """Get all debug sessions from the debug_sessions directory."""
        sessions = []
        
        for file_path in Path(DEBUG_DIR).glob('*.json'):
            try:
                with open(file_path, 'r') as f:
                    session_data = json.load(f)
                    sessions.append(session_data)
            except Exception as e:
                print(f"Error loading session file {file_path}: {e}")
        
        return sessions
    
    def _serve_debug_session(self, session_id: str):
        """Serve a specific debug session."""
        html_path = os.path.join(DEBUG_DIR, f"{session_id}.html")
        
        if os.path.exists(html_path):
            # Serve the HTML file
            self._serve_static_file(html_path)
        else:
            # Check for JSON file
            json_path = os.path.join(DEBUG_DIR, f"{session_id}.json")
            if os.path.exists(json_path):
                # Generate HTML from JSON
                try:
                    with open(json_path, 'r') as f:
                        session_data = json.load(f)
                    
                    # Generate HTML
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    
                    # Simple debug view
                    html = f"""
                    <html>
                    <head>
                        <title>Debug Session {session_id}</title>
                        <style>
                            body {{ font-family: monospace; margin: 20px; }}
                            pre {{ background-color: #f5f5f5; padding: 10px; }}
                        </style>
                    </head>
                    <body>
                        <h1>Debug Session {session_id}</h1>
                        <pre>{json.dumps(session_data, indent=2)}</pre>
                    </body>
                    </html>
                    """
                    
                    self.wfile.write(html.encode())
                    
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(f'<h1>Error loading session</h1><p>{str(e)}</p>'.encode())
            else:
                # 404
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<h1>Debug session not found</h1>')
    
    def _list_sessions(self):
        """List all available debug sessions."""
        sessions = self._get_debug_sessions()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <html>
        <head>
            <title>Debug Sessions</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                .session-list { margin-top: 20px; }
                .session-item { 
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                }
                .session-item:hover {
                    background-color: #f5f5f5;
                }
                a { color: #2196F3; text-decoration: none; }
                a:hover { text-decoration: underline; }
            </style>
        </head>
        <body>
            <h1>Debug Sessions</h1>
            <div class="session-list">
        """
        
        if not sessions:
            html += "<p>No debug sessions found.</p>"
        else:
            # Sort sessions by timestamp (newest first)
            sessions.sort(key=lambda s: s.get('timestamp', ''), reverse=True)
            
            for session in sessions:
                session_id = session.get('session_id', 'unknown')
                question = session.get('question', 'Unknown question')
                timestamp = session.get('timestamp', 'Unknown time')
                
                html += f"""
                <div class="session-item">
                    <a href="/sessions/{session_id}">{session_id}</a> - 
                    <span>{timestamp}</span> - 
                    <span>{question[:50]}</span>
                </div>
                """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
    
    def _api_list_sessions(self):
        """API endpoint to list sessions as JSON."""
        sessions = self._get_debug_sessions()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        # Send minimal session info
        session_list = [{
            'id': session.get('session_id', 'unknown'),
            'question': session.get('question', 'Unknown question'),
            'timestamp': session.get('timestamp', 'Unknown time'),
            'steps_count': len(session.get('steps', []))
        } for session in sessions]
        
        self.wfile.write(json.dumps(session_list).encode())
    
    def _serve_static_file(self, file_path: str):
        """Serve a static file."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            
            # Set content type based on file extension
            if file_path.endswith('.html'):
                self.send_header('Content-type', 'text/html')
            elif file_path.endswith('.json'):
                self.send_header('Content-type', 'application/json')
            elif file_path.endswith('.css'):
                self.send_header('Content-type', 'text/css')
            elif file_path.endswith('.js'):
                self.send_header('Content-type', 'application/javascript')
            else:
                self.send_header('Content-type', 'application/octet-stream')
            
            self.end_headers()
            self.wfile.write(content)
            
        except FileNotFoundError:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>404 Not Found</h1>')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f'<h1>Internal Server Error</h1><p>{str(e)}</p>'.encode())

def open_browser(port):
    """Open the browser after a short delay."""
    time.sleep(1)
    webbrowser.open(f'http://localhost:{port}')

def main():
    """Main function to run the server."""
    parser = argparse.ArgumentParser(description='Debug UI Server')
    parser.add_argument('--port', type=int, default=8000, help='Port to run the server on')
    parser.add_argument('--no-browser', action='store_true', help='Don\'t open the browser automatically')
    args = parser.parse_args()
    
    port = args.port
    
    # Use ThreadingTCPServer for better performance
    with socketserver.ThreadingTCPServer(("", port), DebugUIHandler) as httpd:
        print(f"Debug UI server running at http://localhost:{port}")
        
        # Open browser if not disabled
        if not args.no_browser:
            threading.Thread(target=open_browser, args=(port,)).start()
        
        # Serve until interrupted
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

if __name__ == '__main__':
    main() 