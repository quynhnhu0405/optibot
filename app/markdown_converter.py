import re
from pathlib import Path

from markdownify import markdownify as html_to_markdown

from config import config
from scraper import Article


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
    return slug.strip("-")


def article_to_markdown(article: Article) -> str:
    body = html_to_markdown(
        article.html_body,
        heading_style="ATX",
        code_language="",
    )
    return f"# {article.title}\n\nArticle URL:\n{article.url}\n\n---\n\n{body}\n"


def save_articles_as_markdown(articles: list[Article]) -> list[Path]:
    config.markdown_dir.mkdir(parents=True, exist_ok=True)

    paths: list[Path] = []
    for article in articles:
        slug = slugify(article.title)
        file_path = config.markdown_dir / f"{slug}.md"
        file_path.write_text(article_to_markdown(article), encoding="utf-8")
        paths.append(file_path)

    return paths
