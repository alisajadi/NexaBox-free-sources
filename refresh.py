"""Copy supported URI text from public Telegram pages; never execute source text."""
import html
import json
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

MAX_BODY = 2 * 1024 * 1024
MAX_LINKS = 1000
CHANNEL = re.compile(r"^[A-Za-z][A-Za-z0-9_]{3,63}$")
SHARE = re.compile(r'''(?i)(?:vless|vmess|trojan|ss|socks5?|https?)://[^\s<>"']+''')
MESSAGES = re.compile(r'''<div[^>]*class=["'][^"']*tgme_widget_message_text[^"']*["'][^>]*>(.*?)</div>''', re.S)

def valid_url(raw):
    u = urllib.parse.urlsplit(raw)
    if u.scheme != "https" or not u.hostname or u.username or u.password or u.fragment or len(raw) > 8192:
        raise ValueError("HTTPS source without credentials/fragment required")
    if u.hostname.lower() == "t.me":
        name = u.path.strip("/").removeprefix("s/")
        if not CHANNEL.fullmatch(name) or u.query or u.port:
            raise ValueError("Public Telegram channel required")
        return "https://t.me/s/" + name, name
    return raw, None

class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        valid_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def extract(body):
    text = body.decode("utf-8", errors="replace")
    parts = []
    for message in MESSAGES.findall(text)[:500]:
        message = re.sub(r"<(script|style)\b[^>]*>.*?</\1>", "", message, flags=re.S | re.I)
        parts.extend(re.findall(r'''href=["']([^"']+)["']''', message, flags=re.I))
        parts.append(re.sub(r"<[^>]*>", "\n", message))
    links = SHARE.findall(html.unescape("\n".join(parts)))
    # Preserve explicit HTTP proxy authorities, while omitting ordinary web
    # pages/ad references. The app validates every candidate with its parser.
    def share(link):
        if len(link) > 32768:
            return False
        if not link.lower().startswith(("https://", "http://")):
            return True
        try:
            u = urllib.parse.urlsplit(link)
            return bool(u.hostname and u.port and 1 <= u.port <= 65535 and u.path in ("", "/") and not u.query)
        except ValueError:
            return False
    links = [x for x in links if share(x)]
    return list(dict.fromkeys(links))[:MAX_LINKS]

def refresh(root, fetch=None):
    root = Path(root)
    if fetch is None:
        opener = urllib.request.build_opener(Redirect())
        def fetch(url):
            req = urllib.request.Request(url, headers={"User-Agent": "NexaBox-public-feed/0.7"})
            with opener.open(req, timeout=20) as response:
                body = response.read(MAX_BODY + 1)
                if len(body) > MAX_BODY:
                    raise ValueError("Source exceeds 2 MiB")
                return body
    urls = []
    for line in (root / "sources.txt").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            urls.append(valid_url(line))
    if len(urls) > 50:
        raise ValueError("Maximum 50 sources")
    index = ["# Managed public list. Edit sources.txt; generated snapshots keep prior data on fetch failure."]
    errors = 0
    successes = 0
    for raw, name in dict.fromkeys(urls):
        if name is None:
            index.append(raw)
            continue
        path = root / "channels" / (name + ".txt")
        try:
            body = fetch(raw)
            if len(body) > MAX_BODY:
                raise ValueError("Source exceeds 2 MiB")
            links = extract(body)
            if not links:
                raise ValueError("No supported public share links")
            path.parent.mkdir(exist_ok=True)
            path.write_text("# Public channel: " + name + "\n" + "\n".join(links) + "\n", encoding="utf-8")
            successes += 1
        except (OSError, ValueError, urllib.error.URLError):
            errors += 1
            print("Public channel snapshot failed; cached text retained: " + name)
        if path.exists():
            index.append("https://raw.githubusercontent.com/alisajadi/NexaBox-free-sources/main/channels/" + name + ".txt")
    if len(index) == 1:
        raise ValueError("No public feed or cached snapshot; previous index retained")
    (root / "free-connection.txt").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(json.dumps({"channels_refreshed": successes, "channel_errors": errors, "index_references": len(index)-1}))
    return successes, errors

if __name__ == "__main__":
    refresh(Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent)
