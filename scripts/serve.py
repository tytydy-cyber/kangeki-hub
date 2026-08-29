import http.server
import os

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "site"))


# Plain SimpleHTTPRequestHandler sends no Cache-Control header. This site
# registers a Service Worker (sw.js) for PWA offline support, which caches
# aggressively — without this, an edit can keep serving the stale cached
# version during local dev even after a hard reload. GitHub Pages serves
# the deployed site with its own headers, untouched by this file.
class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


http.server.test(HandlerClass=NoCacheHandler, port=8766)
