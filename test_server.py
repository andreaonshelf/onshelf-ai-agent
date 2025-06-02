from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

os.chdir('/Users/andreavillani/Desktop/onshelf/Tech/extract.planogram')

httpd = HTTPServer(('localhost', 8001), SimpleHTTPRequestHandler)
print("Test server running on http://localhost:8001")
httpd.serve_forever()