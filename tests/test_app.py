import unittest

from app import classify, parse_feed


class FeedParsingTests(unittest.TestCase):
    def test_parses_rss_and_classifies_phishing(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>Nowy phishing podszywa się pod bank</title>
          <link>https://news.example.test/phishing</link>
          <description><![CDATA[<p>Uważaj na fałszywe wiadomości.</p>]]></description>
          <pubDate>Tue, 10 Nov 2026 10:00:00 GMT</pubDate>
          <guid>phishing-1</guid>
        </item></channel></rss>""".encode("utf-8")

        items = parse_feed(xml, "Test")

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["category"], "Phishing")
        self.assertEqual(items[0]["summary"], "Uważaj na fałszywe wiadomości.")
        self.assertEqual(items[0]["link"], "https://news.example.test/phishing")

    def test_parses_atom_link(self):
        xml = b"""<feed xmlns="http://www.w3.org/2005/Atom">
          <entry><title>Podatnosc CVE-2026-1234</title>
          <link href="https://news.example.test/cve"/>
          <summary>Nowa podatnosc.</summary></entry>
        </feed>"""

        items = parse_feed(xml, "Atom")

        self.assertEqual(items[0]["category"], "Podatności")
        self.assertEqual(items[0]["link"], "https://news.example.test/cve")

    def test_rejects_non_https_article_links(self):
        xml = b"""<rss><channel><item>
          <title>Niebezpieczny link</title>
          <link>javascript:alert(1)</link>
        </item></channel></rss>"""

        self.assertEqual(parse_feed(xml, "Test"), [])

    def test_rejects_missing_article_links(self):
        xml = b"""<rss><channel><item>
          <title>Wpis bez linku</title>
        </item></channel></rss>"""

        self.assertEqual(parse_feed(xml, "Test"), [])

    def test_rejects_xml_entity_declarations(self):
        xml = b'<!DOCTYPE rss [<!ENTITY x "x">]><rss><channel/></rss>'

        with self.assertRaises(ValueError):
            parse_feed(xml, "Test")

    def test_classifies_known_leak_keywords(self):
        self.assertEqual(classify("Wyciek haseł", ""), "Wycieki")


if __name__ == "__main__":
    unittest.main()
