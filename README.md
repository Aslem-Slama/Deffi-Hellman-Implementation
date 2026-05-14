# Local Encrypted Messenger

This project has two parts:

- `web_chat.py` is the local backend server.
- `index.html`, `styles.css`, and `app.js` are the browser frontend.

The backend serves the frontend, so you only need to start one server.

## 1. Install the dependency

If you have not installed `cryptography` yet, run:

```powershell
python -m pip install -r requirements.txt
```

If pip is missing, run:

```powershell
python -m ensurepip --upgrade
python -m pip install -r requirements.txt
```

## 2. Start the backend and frontend

From this folder:

```powershell
cd "C:\Users\amras\Desktop\local deffi hellman"
python .\web_chat.py
```

You should see:

```text
Local encrypted messenger running at http://127.0.0.1:8765
Press Ctrl+C to stop.
```

## 3. Open the frontend

Open this in your browser:

```text
http://127.0.0.1:8765
```

## 4. Use it

1. Copy your public key and send it to the other person.
2. Paste the other person's public key into the app.
3. Click `Start Session`.
4. Type a message and click `Encrypt`.
5. Send the encrypted text to the other person.
6. Paste received encrypted text into the receive box and click `Decrypt`.

## Stop the server

Go back to the terminal where `web_chat.py` is running and press:

```text
Ctrl+C
```

## Optional: use another port

If port `8765` is busy, start it with another port:

```powershell
$env:PORT = "9000"
python .\web_chat.py
```

Then open:

```text
http://127.0.0.1:9000
```

## Note

This app does not automatically connect to WhatsApp or Messenger yet. It encrypts and decrypts messages locally, then you manually copy and paste the encrypted text.
