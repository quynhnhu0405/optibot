import sys

from hash_manager import diff_files, load_hashes, save_hashes
from logger import configure_logging
from markdown_converter import save_articles_as_markdown
from scraper import scrape_articles
from uploader import load_files_meta, save_files_meta, test_assistant, upload_to_gemini


def main() -> None:
    configure_logging()

    print("--------------------------------")
    print("Scraping articles...")

    articles = scrape_articles(30)
    if len(articles) == 0:
        print("No articles scraped. Exiting.", file=sys.stderr)
        raise SystemExit(1)
    print(f"Found {len(articles)} articles")

    file_paths = save_articles_as_markdown(articles)

    old_hashes = load_hashes()
    changes, added, updated, skipped = diff_files(file_paths, old_hashes)

    print("Uploading...")
    new_uploads = upload_to_gemini(changes)

    all_files = load_files_meta()
    for new_file in new_uploads:
        match_index = next(
            (index for index, file in enumerate(all_files) if file.name == new_file.name),
            -1,
        )
        if match_index >= 0:
            all_files[match_index] = new_file
        else:
            all_files.append(new_file)

    save_files_meta(all_files)

    new_hashes = {**old_hashes}
    for change in changes:
        new_hashes[change.file_path.name] = change.hash
    save_hashes(new_hashes)

    print("Upload complete.")
    print(f"Added: {added}")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")

    test_assistant(all_files)

    print("Done.")
    print("--------------------------------")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Fatal error: {error}", file=sys.stderr)
        raise SystemExit(1)
