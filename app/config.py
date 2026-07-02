from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Config:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = "gemini-3.5-flash"
    zendesk_base_url: str = "https://support.optisigns.com/api/v2/help_center"
    markdown_dir: Path = PROJECT_ROOT / "markdown"
    hash_file: Path = PROJECT_ROOT / "data" / "hashes.json"
    files_meta_file: Path = PROJECT_ROOT / "data" / "files.json"
    assistant_name: str = "OptiBot"
    assistant_prompt: str = """You are OptiBot, the customer-support bot for OptiSigns.com.

Tone: helpful, factual, concise.

Only answer using the uploaded docs.

Max 5 bullet points; else link to the doc.

Cite up to 3 "Article URL:" lines per reply."""


config = Config()
