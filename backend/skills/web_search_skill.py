from __future__ import annotations

import json
import re
from html import unescape
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen

from backend.skills.base import BaseSkill


class WebSearchSkill(BaseSkill):
    name = "web_search"
    description = "Fetch lightweight web search results and return compact snippets."

    def input_schema(self) -> dict:
        return {
            "query": "str",
            "max_results": "int",
        }

    def run(self, **kwargs) -> dict:
        query = kwargs.get("query", "").strip()
        max_results = kwargs.get("max_results", 4)
        if not query:
            return {"summary": "搜索词为空，未执行网页检索。", "results": []}

        results = self._instant_answer_results(query)
        if len(results) < max_results:
            html_results = self._duckduckgo_html_results(query)
            seen_urls = {item["url"] for item in results}
            for item in html_results:
                if item["url"] not in seen_urls:
                    results.append(item)
                    seen_urls.add(item["url"])
                if len(results) >= max_results:
                    break

        results = results[:max_results]
        if not results:
            return {
                "summary": "未获取到网页搜索结果，可能是当前网络环境限制了外部检索。",
                "results": [],
            }

        topics = "、".join(item["title"] for item in results[:3])
        return {
            "summary": f"已获取 {len(results)} 条网页结果，主要涉及：{topics}。",
            "results": results,
        }

    def _instant_answer_results(self, query: str) -> list[dict]:
        url = f"https://api.duckduckgo.com/?q={quote_plus(query)}&format=json&no_html=1&skip_disambig=1"
        payload = self._request_text(url)
        if not payload:
            return []

        data = json.loads(payload)
        results: list[dict] = []

        abstract_text = data.get("AbstractText") or ""
        abstract_url = data.get("AbstractURL") or ""
        heading = data.get("Heading") or query
        if abstract_text and abstract_url:
            results.append(
                {
                    "title": heading,
                    "url": abstract_url,
                    "snippet": abstract_text.strip(),
                }
            )

        for topic in self._flatten_topics(data.get("RelatedTopics", [])):
            text = (topic.get("Text") or "").strip()
            url = (topic.get("FirstURL") or "").strip()
            if text and url:
                title = text.split(" - ", 1)[0]
                results.append({"title": title, "url": url, "snippet": text})
            if len(results) >= 6:
                break

        return results

    def _duckduckgo_html_results(self, query: str) -> list[dict]:
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
        html = self._request_text(url)
        if not html:
            return []

        link_pattern = re.compile(
            r'<a[^>]*class="result__a"[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<title>.*?)</a>',
            re.IGNORECASE | re.DOTALL,
        )
        snippet_pattern = re.compile(
            r'<a[^>]*class="result__snippet"[^>]*>(?P<snippet>.*?)</a>|'
            r'<div[^>]*class="result__snippet"[^>]*>(?P<divsnippet>.*?)</div>',
            re.IGNORECASE | re.DOTALL,
        )

        snippets = [
            self._clean_html(match.group("snippet") or match.group("divsnippet") or "")
            for match in snippet_pattern.finditer(html)
        ]

        results: list[dict] = []
        for index, match in enumerate(link_pattern.finditer(html)):
            href = self._unwrap_duckduckgo_url(match.group("href"))
            title = self._clean_html(match.group("title"))
            snippet = snippets[index] if index < len(snippets) else ""
            if href and title:
                results.append({"title": title, "url": href, "snippet": snippet})
            if len(results) >= 6:
                break

        return results

    def _request_text(self, url: str) -> str:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
                )
            },
        )
        try:
            with urlopen(request, timeout=10) as response:
                return response.read().decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _flatten_topics(self, topics: list[dict]) -> list[dict]:
        flattened: list[dict] = []
        for item in topics:
            if "Topics" in item:
                flattened.extend(item["Topics"])
            else:
                flattened.append(item)
        return flattened

    def _unwrap_duckduckgo_url(self, value: str) -> str:
        href = unescape(value)
        if href.startswith("//"):
            href = f"https:{href}"

        parsed = urlparse(href)
        if "duckduckgo.com" in parsed.netloc and parsed.path.startswith("/l/"):
            target = parse_qs(parsed.query).get("uddg", [""])[0]
            return unquote(target)
        return href

    def _clean_html(self, value: str) -> str:
        text = re.sub(r"<[^>]+>", " ", value)
        text = unescape(text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()
