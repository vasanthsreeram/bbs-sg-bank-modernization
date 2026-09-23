"""Static checks that the frontend is wired up and self-contained.

These catch the "browser crashes on a null element" and "hidden element stays
visible" classes of bug without needing a browser in CI.
"""

from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
HTML = (FRONTEND / "index.html").read_text()
CSS = (FRONTEND / "styles.css").read_text()
JS = (FRONTEND / "app.js").read_text()


class _IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.classes: set[str] = set()
        self.scripts: list[str] = []
        self.stylesheets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.add(attributes["id"])
        if attributes.get("class"):
            self.classes.update(attributes["class"].split())
        if tag == "script" and attributes.get("src"):
            self.scripts.append(attributes["src"])
        if tag == "link" and attributes.get("href", "").endswith(".css"):
            self.stylesheets.append(attributes["href"])


class FrontendWiringTest(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = _IdCollector()
        self.parser.feed(HTML)

    def test_every_element_id_used_by_js_exists_in_the_markup(self) -> None:
        referenced = set(re.findall(r'\bel\("([^"]+)"\)', JS))
        referenced |= set(re.findall(r'getElementById\(\s*[`"\']([^`"\']+)[`"\']', JS))
        referenced -= {"view-{name}"}
        missing = sorted(name for name in referenced if name not in self.parser.ids and "${" not in name)
        self.assertEqual(missing, [], f"app.js references ids that index.html does not define: {missing}")

    def test_view_sections_and_tabs_line_up(self) -> None:
        views = {name for name in self.parser.ids if name.startswith("view-")}
        tabs = set(re.findall(r'data-view="([^"]+)"', HTML))
        self.assertEqual(views, {"view-" + tab for tab in tabs})
        self.assertTrue(views)

    def test_query_selector_hooks_exist(self) -> None:
        for hook in ("tab", "view", "is-active", "toast"):
            self.assertIn(hook, CSS)
        self.assertIn("data-goto", HTML)
        self.assertIn("data-amount", HTML)
        self.assertIn('name="kind"', HTML)

    def test_assets_referenced_by_the_page_are_local_and_present(self) -> None:
        for reference in self.parser.scripts + self.parser.stylesheets:
            self.assertTrue(reference.startswith("/"), reference)
            self.assertTrue((FRONTEND / reference.lstrip("/")).is_file(), reference)

    def test_no_external_network_dependencies(self) -> None:
        # XML namespace declarations are not network fetches.
        allowed = ("http://www.w3.org/", "https://www.w3.org/")
        for name, text in (("index.html", HTML), ("styles.css", CSS), ("app.js", JS)):
            for match in re.findall(r"https?://[^\s\"'<>)]+", text):
                if match.startswith(allowed):
                    continue
                if name == "index.html" and match == "http://127.0.0.1:8792/":
                    continue
                self.fail(f"{name} references an external URL: {match}")

    def test_original_terminal_link_opens_the_local_cobol_service(self) -> None:
        self.assertIn('href="http://127.0.0.1:8792/" target="_blank" rel="noopener noreferrer"', HTML)
        self.assertIn("legacy-ui/run.sh", HTML)

    def test_api_paths_used_by_js_exist_in_the_backend(self) -> None:
        backend = (Path(__file__).resolve().parents[1] / "backend" / "app.py").read_text()
        routed = set(re.findall(r'path (?:==|\.startswith\()\s*"(/api/[^"]+)"', backend))
        self.assertTrue(routed)
        called = {match.split("?")[0] for match in re.findall(r'"(/api/[a-z]+[^"]*)"', JS)}
        for path in sorted(called):
            self.assertTrue(
                any(path == route or path.startswith(route.rstrip("<")) or path.startswith(route) for route in routed),
                f"{path} is called by the UI but not routed in app.py (routes: {sorted(routed)})",
            )

    def test_author_display_rules_do_not_beat_the_hidden_attribute(self) -> None:
        self.assertIn("[hidden] { display: none !important; }", CSS)

    # --- branding and the single synthetic-demo disclosure -----------------

    @staticmethod
    def _normalise(text: str) -> str:
        return " ".join(text.split())

    @staticmethod
    def _disclaimer_from_backend() -> str:
        backend = (Path(__file__).resolve().parents[1] / "backend" / "app.py").read_text()
        return re.search(r'"disclaimer": \(\s*"([^"]+)"\s*"([^"]+)"\s*"([^"]+)"', backend).groups()

    def test_exactly_one_disclosure_and_it_is_in_the_footer(self) -> None:
        self.assertEqual(HTML.count('id="disclaimer"'), 1)
        footer = HTML[HTML.index("<footer"):]
        self.assertIn('id="disclaimer"', footer)
        self.assertIn('class="disclosure"', footer)
        self.assertNotIn('class="disclaimer"', HTML)  # the old top banner is gone

    def test_footer_disclosure_matches_the_api_text(self) -> None:
        footer = HTML[HTML.index("<footer"):]
        shown = self._normalise(re.search(r'<p class="disclosure" id="disclaimer">(.*?)</p>', footer, re.S).group(1))
        api_text = self._normalise("".join(self._disclaimer_from_backend()))
        self.assertEqual(shown, api_text)

    def test_disclosure_is_not_repeated_in_the_header_or_hero(self) -> None:
        above_main = re.sub(r"<[^>]+>", " ", HTML[: HTML.index("<main")])  # visible text only
        self.assertNotIn("not a real institution", above_main)
        self.assertNotIn("no real customers", above_main)
        # a compact marker still tells the reader what they are looking at
        self.assertIn("synthetic demo", above_main.lower())

    def test_branding_is_prominent(self) -> None:
        self.assertIn("<title>BBS SG Bank", HTML)
        header = HTML[: HTML.index("</header>")]
        self.assertIn('class="brand__mark"', header)
        self.assertIn("BBS SG Bank", header)
        self.assertIn("BBS SG Bank", HTML[HTML.index("<footer"):])
        self.assertEqual(HTML.count("<h1"), 6)  # one heading per view, branding stays in the chrome

    # --- selected-account detail staleness ---------------------------------

    def test_selected_account_detail_is_refreshed_with_the_ledger(self) -> None:
        refresh_all = JS[JS.index("async function refreshAll()"):]
        refresh_all = refresh_all[: refresh_all.index("\n  }")]
        self.assertIn("renderAccountDetail()", refresh_all)
        # the Accounts tab and its Refresh button both re-read the selected account
        self.assertIn('name === "accounts" && state.selected) renderAccountDetail()', JS)
        self.assertIn("refreshAccountsView().catch", JS)
        self.assertIn("async function refreshAccountsView()", JS)
        self.assertIn("await renderAccountDetail();", JS)


if __name__ == "__main__":
    unittest.main()
