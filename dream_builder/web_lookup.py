import requests
from bs4 import BeautifulSoup

SEARCH_URL = "https://html.duckduckgo.com/html/"


def search(query, max_results=5):
    """Run a real web search (DuckDuckGo HTML endpoint, no API key needed)
    and return a list of {title, url, snippet} dicts."""
    if not query:
        return []
    resp = requests.post(
        SEARCH_URL,
        data={"q": query},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=15,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    results = []
    for link in soup.select("a.result__a")[:max_results]:
        body = link.find_parent("div", class_="result__body")
        snippet = ""
        if body is not None:
            snippet_el = body.select_one(".result__snippet")
            if snippet_el is not None:
                snippet = snippet_el.get_text(strip=True)
        results.append(
            {
                "title": link.get_text(strip=True),
                "url": link.get("href"),
                "snippet": snippet,
            }
        )
    return results
