#!/usr/bin/env python3
"""Dependency-free static serving for this site's dist/ only (no API or accounts)."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, '.mjs': 'text/javascript; charset=utf-8'}

    def list_directory(self, path):
        self.send_error(404, 'Not found')

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self' https://api.github.com https://raw.githubusercontent.com; frame-ancestors 'none'; base-uri 'none'; form-action 'none'; object-src 'none'")
        super().end_headers()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=8182)
    parser.add_argument('--directory', type=Path, default=Path(__file__).resolve().parents[1] / 'dist')
    args = parser.parse_args()
    directory = args.directory.resolve(strict=True)
    if not (directory / 'index.html').is_file():
        parser.error('The directory must contain the built website index.html')
    server = ThreadingHTTPServer((args.host, args.port), functools.partial(Handler, directory=str(directory)))
    print(f'Static study website: http://{args.host}:{args.port}/ ({directory})', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
