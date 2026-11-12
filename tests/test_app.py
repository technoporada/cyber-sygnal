import unittest

from app import classify, parse_feed, _date_order


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

    def test_classifies_all_categories(self):
        cases = [
            ("oszust phishing podszyw", "", "Phishing"),
            ("wyciek danych osobowych", "", "Wycieki"),
            ("cve-2026-9999 exploit", "", "Podatności"),
            ("atak ransomware malware", "", "Ataki"),
            ("pogoda jest piękna dzisiaj", "", "Inne"),
        ]
        for title, summary, expected in cases:
            with self.subTest(title=title):
                self.assertEqual(classify(title, summary), expected)

    def test_parses_wycieki_category(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>Wyciek bazy klientów sklepu</title>
          <link>https://news.example.test/leak</link>
          <description>Ukradziono dane osobowe i hasła użytkowników.</description>
          <pubDate>Mon, 09 Nov 2026 08:00:00 GMT</pubDate>
          <guid>leak-1</guid>
        </item></channel></rss>""".encode("utf-8")

        items = parse_feed(xml, "Test")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["category"], "Wycieki")
        self.assertEqual(items[0]["source"], "Test")

    def test_parses_ataki_category(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel><item>
          <title>Nowy atak DDoS na serwery gov.pl</title>
          <link>https://news.example.test/ddos</link>
          <description>Atak hakerówparaliżował strony administracji.</description>
          <pubDate>Sun, 08 Nov 2026 12:00:00 GMT</pubDate>
          <guid>ddos-1</guid>
        </item></channel></rss>""".encode("utf-8")

        items = parse_feed(xml, "Test")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["category"], "Ataki")

    def test_deduplicates_by_guid(self):
        xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel>
          <item>
            <title>Duplicate item</title>
            <link>https://news.example.test/dup</link>
            <description>First occurrence</description>
            <pubDate>Tue, 10 Nov 2026 10:00:00 GMT</pubDate>
            <guid>dup-1</guid>
          </item>
          <item>
            <title>Duplicate item again</title>
            <link>https://news.example.test/dup2</link>
            <description>Second occurrence</description>
            <pubDate>Tue, 10 Nov 2026 11:00:00 GMT</pubDate>
            <guid>dup-1</guid>
          </item>
        </channel></rss>""".encode("utf-8")

        items = parse_feed(xml, "Test")
        self.assertEqual(len(items), 1)

    def test_date_order_iso_with_z(self):
        self.assertGreater(
            _date_order("2026-11-10T10:00:00Z"),
            _date_order("2026-11-09T10:00:00Z"),
        )

    def test_date_order_rfc2822(self):
        self.assertGreater(
            _date_order("Tue, 10 Nov 2026 10:00:00 GMT"),
            _date_order("Mon, 09 Nov 2026 10:00:00 GMT"),
        )

    def test_date_order_empty(self):
        self.assertEqual(_date_order(""), 0.0)

    def test_date_order_invalid(self):
        self.assertEqual(_date_order("not-a-date"), 0.0)


if __name__ == "__main__":
    unittest.main()
