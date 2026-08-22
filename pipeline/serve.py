"""Dev server that refuses to cache.

The browser holds ES modules in a module map that a normal reload does not
clear, so edits appear not to take effect. Sending no-store on everything
makes each reload fetch the real files.
"""
import http.server, socketserver, sys

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def log_message(self, *a):
        pass

port = int(sys.argv[1]) if len(sys.argv) > 1 else 5173
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', port), Handler) as httpd:
    print(f'serving on http://127.0.0.1:{port}')
    httpd.serve_forever()
