import socket, threading, select, base64
from http.server import HTTPServer, BaseHTTPRequestHandler

LISTEN = "0.0.0.0"
PORT = 8080
USER = "user"
PASS = "arvan2024sync"
BUF = 8192


def relay(src, dst):
    try:
        while True:
            r, _, _ = select.select([src, dst], [], [], 120)
            if not r:
                break
            for s in r:
                data = s.recv(BUF)
                if not data:
                    return
                (dst if s is src else src).sendall(data)
    except Exception:
        pass
    finally:
        try:
            src.close()
        except Exception:
            pass
        try:
            dst.close()
        except Exception:
            pass


def check_auth(headers):
    auth = headers.get("Proxy-Authorization", "")
    if not auth:
        return False
    try:
        scheme, token = auth.split(" ", 1)
        if scheme.lower() != "basic":
            return False
        decoded = base64.b64decode(token).decode()
        return decoded == f"{USER}:{PASS}"
    except Exception:
        return False


class ProxyHandler(BaseHTTPRequestHandler):
    server_version = "nginx"
    sys_version = ""

    def log_message(self, format, *args):
        pass

    def do_CONNECT(self):
        if not check_auth(self.headers):
            self.send_response(407)
            self.send_header("Proxy-Authenticate", 'Basic realm="p"')
            self.end_headers()
            return
        host_port = self.path
        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
            port = int(port)
        else:
            host = host_port
            port = 443
        try:
            remote = socket.create_connection((host, port), timeout=10)
        except Exception:
            self.send_response(502)
            self.end_headers()
            return
        self.send_response(200, "OK")
        self.end_headers()
        client = self.connection
        t = threading.Thread(target=relay, args=(client, remote), daemon=True)
        t.start()
        t.join()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK\n")

    do_HEAD = do_GET


def main():
    server = HTTPServer((LISTEN, PORT), ProxyHandler)
    server.daemon_threads = True
    print(f"Listening on {LISTEN}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
