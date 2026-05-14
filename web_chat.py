from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
import base64
import hashlib
import json
import os
import sys

try:
    from cryptography.hazmat.primitives.asymmetric.x25519 import (
        X25519PrivateKey,
        X25519PublicKey,
    )
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("Missing dependency: cryptography")
    print("Install it with: python -m pip install cryptography")
    sys.exit(1)


ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8765"))


class CryptoSession:
    def __init__(self):
        self.reset()

    def reset(self):
        self.private_key = X25519PrivateKey.generate()
        self.public_key = self.private_key.public_key()
        self.peer_public_b64 = None
        self.aesgcm = None

        public_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        self.public_b64 = base64.b64encode(public_bytes).decode("ascii")

    @property
    def active(self):
        return self.aesgcm is not None

    def status(self):
        return {
            "publicKey": self.public_b64,
            "sessionActive": self.active,
            "peerPublicKey": self.peer_public_b64,
        }

    def start(self, peer_public_b64):
        cleaned = "".join(peer_public_b64.split())
        if not cleaned:
            raise ValueError("Paste the other person's public key first.")

        try:
            peer_public_bytes = base64.b64decode(cleaned, validate=True)
        except ValueError as exc:
            raise ValueError("The peer public key is not valid Base64.") from exc

        if len(peer_public_bytes) != 32:
            raise ValueError("An X25519 public key must decode to exactly 32 bytes.")

        peer_public_key = X25519PublicKey.from_public_bytes(peer_public_bytes)
        shared_secret = self.private_key.exchange(peer_public_key)
        aes_key = hashlib.sha256(shared_secret).digest()

        self.aesgcm = AESGCM(aes_key)
        self.peer_public_b64 = cleaned

        return self.status()

    def require_active(self):
        if not self.active:
            raise RuntimeError("Start a session before sending or receiving messages.")

    def encrypt(self, message):
        self.require_active()
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, message.encode("utf-8"), None)
        encrypted = base64.b64encode(nonce + ciphertext).decode("ascii")
        return encrypted

    def decrypt(self, encrypted_b64):
        self.require_active()
        cleaned = "".join(encrypted_b64.split())
        if not cleaned:
            raise ValueError("Paste an encrypted message first.")

        try:
            encrypted_bytes = base64.b64decode(cleaned, validate=True)
        except ValueError as exc:
            raise ValueError("The encrypted message is not valid Base64.") from exc

        if len(encrypted_bytes) < 29:
            raise ValueError("The encrypted message is too short.")

        nonce = encrypted_bytes[:12]
        ciphertext = encrypted_bytes[12:]
        plaintext = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")


session = CryptoSession()
session_lock = Lock()


class AppHandler(BaseHTTPRequestHandler):
    static_files = {
        "/": ("index.html", "text/html; charset=utf-8"),
        "/index.html": ("index.html", "text/html; charset=utf-8"),
        "/styles.css": ("styles.css", "text/css; charset=utf-8"),
        "/app.js": ("app.js", "application/javascript; charset=utf-8"),
    }

    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/api/status":
            with session_lock:
                self.send_json(200, session.status())
            return

        file_info = self.static_files.get(self.path)
        if not file_info:
            self.send_json(404, {"error": "Not found"})
            return

        file_name, content_type = file_info
        file_path = ROOT / file_name
        if not file_path.exists():
            self.send_json(404, {"error": f"Missing file: {file_name}"})
            return

        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        try:
            data = self.read_json()

            if self.path == "/api/start":
                with session_lock:
                    result = session.start(data.get("peerPublicKey", ""))
                self.send_json(200, result)
                return

            if self.path == "/api/reset":
                with session_lock:
                    session.reset()
                    result = session.status()
                self.send_json(200, result)
                return

            if self.path == "/api/encrypt":
                message = data.get("message", "")
                with session_lock:
                    encrypted = session.encrypt(message)
                self.send_json(200, {"encrypted": encrypted})
                return

            if self.path == "/api/decrypt":
                encrypted = data.get("encrypted", "")
                with session_lock:
                    message = session.decrypt(encrypted)
                self.send_json(200, {"message": message})
                return

            self.send_json(404, {"error": "Not found"})

        except ValueError as exc:
            self.send_json(400, {"error": str(exc)})
        except RuntimeError as exc:
            self.send_json(409, {"error": str(exc)})
        except Exception:
            self.send_json(400, {"error": "Could not decrypt that message."})

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        if not raw:
            return {}
        return json.loads(raw)

    def send_json(self, status, payload):
        content = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(content)


def main():
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print(f"Local encrypted messenger running at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
