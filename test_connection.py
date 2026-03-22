#!/usr/bin/env python3
"""Test LM Studio connection for JanitorAI proxy"""

import json
import urllib.request
import urllib.error

API_URL = "http://localhost:5001/v1"  # nginx proxy (use 1234 for direct)
API_KEY = "7Xwj8XiS/L0Mep1QvQ9weCjQ"
MODEL = "qwen/qwen3.5-9b"

def test_models():
    """Test listing available models"""
    print("Testing /v1/models endpoint...")
    req = urllib.request.Request(
        f"{API_URL}/models",
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            print(f"[OK] Available models: {[m['id'] for m in data['data']]}")
            return True
    except urllib.error.URLError as e:
        print(f"[FAIL] {e}")
        return False

def test_chat():
    """Test chat completion"""
    print("\nTesting /v1/chat/completions endpoint...")
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Say 'Connection successful!' and nothing else."}],
        "max_tokens": 50,
        "temperature": 0.1
    }
    req = urllib.request.Request(
        f"{API_URL}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
    )
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            response = data["choices"][0]["message"]["content"]
            print(f"[OK] Response: {response[:100]}...")
            return True
    except urllib.error.URLError as e:
        print(f"[FAIL] {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("LM Studio JanitorAI Proxy Connection Test")
    print("=" * 50)
    print(f"API URL: {API_URL}")
    print(f"Model: {MODEL}")
    print("=" * 50 + "\n")

    models_ok = test_models()
    chat_ok = test_chat()

    print("\n" + "=" * 50)
    if models_ok and chat_ok:
        print("[OK] All tests passed! Ready for JanitorAI.")
    else:
        print("[FAIL] Some tests failed. Check LM Studio is running.")
    print("=" * 50)
