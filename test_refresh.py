import tempfile
from pathlib import Path
import unittest
from refresh import refresh, valid_url, extract, MAX_BODY

class PublicFeedTest(unittest.TestCase):
    def test_snapshot_outage_and_removed_source(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "sources.txt").write_text("https://t.me/LonUp_M\nhttps://example.org/sub.txt\n")
            body = b'<div class="tgme_widget_message_text">vless://public-uuid@example.org:443#one<script>trojan://ignored</script></div>'
            self.assertEqual(refresh(root, lambda _: body), (1, 0))
            snapshot = (root / "channels/LonUp_M.txt").read_bytes()
            self.assertNotIn(b"ignored", snapshot)
            self.assertIn("channels/LonUp_M.txt", (root / "free-connection.txt").read_text())
            def failure(_): raise OSError("offline")
            self.assertEqual(refresh(root, failure), (0, 1))
            self.assertEqual((root / "channels/LonUp_M.txt").read_bytes(), snapshot)
            (root / "sources.txt").write_text("https://example.org/sub.txt\n")
            refresh(root, failure)
            self.assertNotIn("LonUp_M", (root / "free-connection.txt").read_text())

    def test_limits_and_private_sources(self):
        for raw in ["http://example.org", "https://user:secret@example.org", "https://t.me/+private", "https://t.me/chan?token=secret"]:
            with self.assertRaises(ValueError): valid_url(raw)
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "sources.txt").write_text("https://t.me/LonUp_M\nhttps://example.org/sub.txt\n")
            refresh(root, lambda _: b"x" * (MAX_BODY+1))
            self.assertFalse((root / "channels/LonUp_M.txt").exists())

    def test_public_proxy_authorities_and_web_references(self):
        links = extract(b'<div class="tgme_widget_message_text">http://public:test@example.org:8080#proxy https://example.org/ad https://example.org:99999 ss://encoded</div>')
        self.assertEqual(links, ["http://public:test@example.org:8080#proxy", "ss://encoded"])

if __name__ == "__main__": unittest.main()
