import threading
import json
import urllib.request
import urllib.error

try:
    import requests
except Exception:
    requests = None


def _fetch_url(url: str, timeout: int = 3) -> str:
    if requests:
        response = requests.get(url, timeout=timeout)
        return response.text
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def get_public_ip():
   
    services = [
        ("https://api.ipify.org?format=json", "json"),
        ("https://ipinfo.io/ip", "text"),
        ("https://ifconfig.me/ip", "text"),
    ]
    for url, kind in services:
        try:
            text = _fetch_url(url, timeout=4).strip()
            if kind == "json":
                data = json.loads(text)
                ip = data.get("ip", "").strip()
            else:
                ip = text
            if ip:
                return ip
        except (urllib.error.URLError, json.JSONDecodeError, Exception):
            continue
    return "Unknown"


def get_ip_async(callback):
 
    def fetch():
        ip = get_public_ip()
        if callback:
            try:
                callback(ip)
            except Exception as e:
                pass
    
    thread = threading.Thread(target=fetch, daemon=True)
    thread.start()