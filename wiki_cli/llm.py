"""Talks to the local Gemma model through Ollama, which runs on this computer."""
import time

import requests

from wiki_cli.config import MODEL, OLLAMA_URL


class ModelUnavailable(Exception):
    """Raised when the local model cannot be reached."""


def chat(messages, temperature=0.2, num_ctx=4096):
    """Send a list of messages to Gemma and return (reply_text, seconds_taken)."""
    body = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "think": False,  # we want a direct answer, not the model's long reasoning
        "options": {"temperature": temperature, "num_ctx": num_ctx},
    }
    started = time.time()
    try:
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=600)
        if response.status_code == 400 and "think" in response.text:
            body.pop("think")  # this model version does not accept the setting
            response = requests.post(f"{OLLAMA_URL}/api/chat", json=body, timeout=600)
    except requests.ConnectionError:
        raise ModelUnavailable(
            f"Cannot reach Ollama at {OLLAMA_URL}. Open the Ollama app and try again."
        )
    if response.status_code == 404:
        raise ModelUnavailable(
            f"Model '{MODEL}' is not downloaded. Run: ollama pull {MODEL}"
        )
    response.raise_for_status()
    seconds = time.time() - started
    return response.json()["message"]["content"].strip(), seconds
