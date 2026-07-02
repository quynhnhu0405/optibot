# OptiBot Python

A Python CLI tool that mirrors the existing TypeScript OptiBot project: it scrapes OptiSigns support articles, converts them to Markdown, uploads new or changed files to Google Gemini, and asks a short verification question.

---

## Project Structure

```text
app/
├── config.py                # Configuration constants
├── scraper.py               # Zendesk articles API scraper
├── markdown_converter.py    # HTML to Markdown converter
├── hash_manager.py          # SHA-256 incremental updater
├── uploader.py              # Gemini file upload and verification
├── logger.py                # Logging setup
├── chat.py                  # Terminal chat loop
└── main.py                  # Orchestrator and entry point
markdown/                    # Scraped articles in .md
data/
├── hashes.json              # File hashes for tracking changes
└── files.json               # Uploaded files metadata, auto-created
Dockerfile
requirements.txt
.env.example
README.md
```

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your-gemini-api-key-here
```

---

## Run Locally

```bash
python app/main.py
```

This will execute:

1. Scrape support articles.
2. Convert them to clean Markdown.
3. Upload new or changed files to Gemini.
4. Update stored hashes.
5. Print sync status and ask a test question.

---

## Chat In Terminal

After running the sync once, start the terminal chat:

```bash
python app/chat.py
```

Type `exit` or `quit` to close the chat.

---

## Docker

### Build

```bash
sudo docker build -t optibot-python .
```

### Run

```bash
docker run --env-file .env optibot-python
```
