from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey
)
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import serialization
import base64
import hashlib
import os

# Generate Alice keys
private_key = X25519PrivateKey.generate()
public_key = private_key.public_key()

# Export public key
public_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw
)

print("=== SEND THIS TO BOB ===")
print(base64.b64encode(public_bytes).decode())

# Paste Bob public key
bob_public_b64 = input("\nPaste Bob public key: ")

bob_public_bytes = base64.b64decode(bob_public_b64)

bob_public_key = X25519PublicKey.from_public_bytes(
    bob_public_bytes
)

# Shared secret
shared_secret = private_key.exchange(bob_public_key)

# Derive AES key
aes_key = hashlib.sha256(shared_secret).digest()

print("\nShared secret established.")

aesgcm = AESGCM(aes_key)

while True:
    choice = input("\nSend or receive a message? (s/r/q): ").strip().lower()

    if choice in ("s", "send"):
        message = input("\nMessage to encrypt: ").encode()

        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, message, None)
        final = base64.b64encode(nonce + ciphertext).decode()

        print("\n=== SEND THIS ENCRYPTED MESSAGE ===")
        print(final)

    elif choice in ("r", "receive"):
        encrypted_b64 = input("\nPaste encrypted message: ")

        try:
            encrypted_bytes = base64.b64decode(encrypted_b64)
            nonce = encrypted_bytes[:12]
            ciphertext = encrypted_bytes[12:]

            message = aesgcm.decrypt(nonce, ciphertext, None)

            print("\n=== DECRYPTED MESSAGE ===")
            print(message.decode())
        except Exception:
            print("\nCould not decrypt message. Check that it was copied correctly and uses the same shared key.")

    elif choice in ("q", "quit", "exit"):
        print("\nSession closed.")
        break

    else:
        print("\nPlease type 's' to send, 'r' to receive, or 'q' to quit.")
