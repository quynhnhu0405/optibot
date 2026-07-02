from dataclasses import dataclass

import requests

from config import config


@dataclass(frozen=True)
class Article:
    title: str
    url: str
    html_body: str


def scrape_articles(min_count: int = 30) -> list[Article]:
    articles: list[Article] = []
    page = 1
    per_page = 30

    while len(articles) < min_count:
        url = f"{config.zendesk_base_url}/en-us/articles.json"
        params = {"per_page": per_page, "page": page}

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except Exception as error:
            print(f"[ERROR] Failed to fetch page {page}: {error}")
            break

        page_articles = data.get("articles") or []
        if not page_articles:
            break

        for article in page_articles:
            body = article.get("body")
            if body:
                articles.append(
                    Article(
                        title=article.get("title", ""),
                        url=article.get("html_url", ""),
                        html_body=body,
                    )
                )

        if not data.get("next_page"):
            break
        page += 1

    return articles
