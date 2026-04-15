import json
import socket
import sys
import urllib.request
from urllib.error import URLError, HTTPError

def check_ollama():
    print("Checking Ollama connectivity...")
    url = "http://127.0.0.1:11434/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                models = [m['name'] for m in data.get('models', [])]
                print(f"  [OK] Ollama is serving on 127.0.0.1:11434")
                print(f"  [OK] Available models: {', '.join(models)}")
                # Check for mistral with any tag
                has_mistral = any("mistral" in m for m in models)
                if has_mistral:
                    print(f"  [OK] Mistral model found.")
                else:
                    print(f"  [!] Mistral model not found in list. Please run 'ollama pull mistral'")
                return True
    except ConnectionRefusedError:
        print("  [FAIL] Connection refused. Is Ollama running?")
    except Exception as e:
        print(f"  [ERR] Error: {e}")
    return False

def check_ddg():
    print("Checking DuckDuckGo Search connectivity...")
    url = "https://duckduckgo.com/?q=test"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print("  [OK] DuckDuckGo is accessible")
                return True
    except Exception as e:
        print(f"  [FAIL] Error accessing DDG: {e}")
    return False

if __name__ == "__main__":
    print("AIdeator Diagnostic Script\n" + "="*30)
    o_ok = check_ollama()
    d_ok = check_ddg()
    print("="*30)
    if o_ok and d_ok:
        print("RESULT: ALL SYSTEMS GO. Ready for AIdeator runs.")
    else:
        print("RESULT: SYSTEM ISSUES DETECTED. See above for details.")
