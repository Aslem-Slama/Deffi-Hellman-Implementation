const dom = {
  body: document.body,
  statusPill: document.querySelector("#statusPill"),
  setupPanel: document.querySelector("#setupPanel"),
  chatPanel: document.querySelector("#chatPanel"),
  publicKey: document.querySelector("#publicKey"),
  peerKey: document.querySelector("#peerKey"),
  setupError: document.querySelector("#setupError"),
  chatError: document.querySelector("#chatError"),
  thread: document.querySelector("#thread"),
  encryptedBlock: document.querySelector("#encryptedBlock"),
  encryptedOutput: document.querySelector("#encryptedOutput"),
  encryptedInput: document.querySelector("#encryptedInput"),
  messageInput: document.querySelector("#messageInput"),
  startBtn: document.querySelector("#startBtn"),
  resetKeyBtn: document.querySelector("#resetKeyBtn"),
  newSessionBtn: document.querySelector("#newSessionBtn"),
  copyPublicBtn: document.querySelector("#copyPublicBtn"),
  copyEncryptedBtn: document.querySelector("#copyEncryptedBtn"),
  clearReceivedBtn: document.querySelector("#clearReceivedBtn"),
  sendForm: document.querySelector("#sendForm"),
  receiveForm: document.querySelector("#receiveForm"),
};

async function api(path, body) {
  const options = body
    ? {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    : {};

  const response = await fetch(path, options);
  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(data.error || "Request failed.");
  }

  return data;
}

function setError(target, message = "") {
  target.textContent = message;
}

function setLoading(button, isLoading, loadingText) {
  if (!button.dataset.label) {
    button.dataset.label = button.textContent;
  }

  button.disabled = isLoading;
  button.textContent = isLoading ? loadingText : button.dataset.label;
}

function setSessionActive(isActive) {
  dom.body.classList.toggle("session-active", isActive);
  dom.setupPanel.classList.toggle("is-hidden", isActive);
  dom.chatPanel.classList.toggle("is-hidden", !isActive);
  dom.statusPill.dataset.state = isActive ? "ready" : "setup";
  dom.statusPill.textContent = isActive ? "Ready" : "Setup";

  if (isActive) {
    dom.messageInput.focus();
  } else {
    dom.peerKey.focus();
  }
}

function addMessage(type, title, text) {
  const message = document.createElement("article");
  message.className = `message ${type}`;

  const label = document.createElement("p");
  label.className = "message-title";
  label.textContent = title;

  const body = document.createElement("p");
  body.className = "message-body";
  body.textContent = text;

  message.append(label, body);
  dom.thread.append(message);
  dom.thread.scrollTop = dom.thread.scrollHeight;
}

async function copyText(text, button) {
  if (!text) return;

  await navigator.clipboard.writeText(text);
  const oldLabel = button.textContent;
  button.textContent = "Copied";
  setTimeout(() => {
    button.textContent = oldLabel;
  }, 900);
}

async function loadStatus() {
  try {
    const status = await api("/api/status");
    dom.publicKey.value = status.publicKey || "";
    setSessionActive(Boolean(status.sessionActive));

    if (status.sessionActive && dom.thread.children.length === 0) {
      addMessage("system", "Session", "Shared key established.");
    }
  } catch (error) {
    setError(dom.setupError, error.message);
  }
}

async function startSession() {
  setError(dom.setupError);
  setLoading(dom.startBtn, true, "Starting");

  try {
    await api("/api/start", { peerPublicKey: dom.peerKey.value });
    dom.thread.innerHTML = "";
    addMessage("system", "Session", "Shared key established.");
    setSessionActive(true);
  } catch (error) {
    setError(dom.setupError, error.message);
  } finally {
    setLoading(dom.startBtn, false);
  }
}

async function resetSession() {
  setError(dom.setupError);
  setError(dom.chatError);

  const status = await api("/api/reset", {});
  dom.publicKey.value = status.publicKey || "";
  dom.peerKey.value = "";
  dom.thread.innerHTML = "";
  dom.encryptedOutput.value = "";
  dom.encryptedInput.value = "";
  dom.messageInput.value = "";
  dom.encryptedBlock.classList.add("is-hidden");
  setSessionActive(false);
}

async function sendMessage(event) {
  event.preventDefault();
  setError(dom.chatError);

  const message = dom.messageInput.value;
  if (!message.trim()) {
    setError(dom.chatError, "Type a message first.");
    return;
  }

  const submitButton = dom.sendForm.querySelector("button[type='submit']");
  setLoading(submitButton, true, "Encrypting");

  try {
    const result = await api("/api/encrypt", { message });
    dom.encryptedOutput.value = result.encrypted;
    dom.encryptedBlock.classList.remove("is-hidden");
    addMessage("outgoing", "Sent", message);
    dom.messageInput.value = "";
  } catch (error) {
    setError(dom.chatError, error.message);
  } finally {
    setLoading(submitButton, false);
  }
}

async function receiveMessage(event) {
  event.preventDefault();
  setError(dom.chatError);

  const encrypted = dom.encryptedInput.value;
  if (!encrypted.trim()) {
    setError(dom.chatError, "Paste an encrypted message first.");
    return;
  }

  const submitButton = dom.receiveForm.querySelector("button[type='submit']");
  setLoading(submitButton, true, "Decrypting");

  try {
    const result = await api("/api/decrypt", { encrypted });
    addMessage("incoming", "Received", result.message);
    dom.encryptedInput.value = "";
  } catch (error) {
    setError(dom.chatError, error.message);
  } finally {
    setLoading(submitButton, false);
  }
}

dom.startBtn.addEventListener("click", startSession);
dom.resetKeyBtn.addEventListener("click", resetSession);
dom.newSessionBtn.addEventListener("click", resetSession);
dom.sendForm.addEventListener("submit", sendMessage);
dom.receiveForm.addEventListener("submit", receiveMessage);
dom.clearReceivedBtn.addEventListener("click", () => {
  dom.encryptedInput.value = "";
  setError(dom.chatError);
});
dom.copyPublicBtn.addEventListener("click", () => copyText(dom.publicKey.value, dom.copyPublicBtn));
dom.copyEncryptedBtn.addEventListener("click", () => copyText(dom.encryptedOutput.value, dom.copyEncryptedBtn));

loadStatus();
