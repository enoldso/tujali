"""
Simple HTTP server to serve the USSD simulator HTML page
"""

import argparse
import http.server
import socketserver
import os
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class USSDSimulatorHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Simple HTTP request handler with GET and HEAD commands"""
    
    def log_message(self, format, *args):
        """Log messages with formatting"""
        logging.info("%s - %s", self.client_address[0], format % args)
    
    def end_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

def serve_simulator(port=8000):
    """
    Serve the USSD simulator HTML page on the specified port
    
    Args:
        port (int): Port number to serve on
    """
    handler = USSDSimulatorHTTPRequestHandler
    
    with socketserver.TCPServer(("", port), handler) as httpd:
        logging.info("Serving USSD simulator at http://0.0.0.0:%s/ussd_simulator.html", port)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("\nServer stopped.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Serve the USSD simulator web interface')
    parser.add_argument('--port', type=int, default=8000, help='Port to serve on (default: 8000)')
    
    args = parser.parse_args()
    serve_simulator(args.port)