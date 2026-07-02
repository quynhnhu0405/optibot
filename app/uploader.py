from dataclasses import asdict, dataclass
from pathlib import Path
import json
import time

import requests

from config import config
from hash_manager import FileChange


GEMINI_API_BASE = "https://generativelanguage.googleapis.com"


@dataclass(frozen=True)
class UploadedFile:
    name: str
    uri: str
    mimeType: str


def _require_api_key() -> None:
    if not config.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is required.")


def _headers() -> dict[str, str]:
    return {"x-goog-api-key": config.gemini_api_key}


def _request_with_retries(method: str, url: str, **kwargs) -> requests.Response:
    last_error: Exception | None = None

    for attempt in range(4):
        try:
            response = requests.request(method, url, **kwargs)
        except requests.RequestException as error:
            last_error = error
            time.sleep(2 * (attempt + 1))
            continue

        if response.status_code not in (429, 500, 502, 503, 504):
            response.raise_for_status()
            return response

        last_error = requests.HTTPError(
            f"{response.status_code} Server Error: {response.reason} for url: {response.url}",
            response=response,
        )
        time.sleep(2 * (attempt + 1))

    if last_error:
        raise last_error
    raise RuntimeError("Gemini request failed.")


def _parse_response_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""

    parts = candidates[0].get("content", {}).get("parts") or []
    return "".join(part.get("text", "") for part in parts)


def _normalize_file(file_data: dict) -> UploadedFile:
    return UploadedFile(
        name=file_data["name"],
        uri=file_data["uri"],
        mimeType=file_data.get("mimeType") or "text/markdown",
    )


def _start_upload(file_path: Path, mime_type: str) -> str:
    metadata = {"file": {"display_name": file_path.name}}
    headers = {
        **_headers(),
        "X-Goog-Upload-Protocol": "resumable",
        "X-Goog-Upload-Command": "start",
        "X-Goog-Upload-Header-Content-Length": str(file_path.stat().st_size),
        "X-Goog-Upload-Header-Content-Type": mime_type,
        "Content-Type": "application/json",
    }

    response = _request_with_retries(
        "POST",
        f"{GEMINI_API_BASE}/upload/v1beta/files",
        headers=headers,
        json=metadata,
        timeout=30,
    )

    upload_url = response.headers.get("X-Goog-Upload-URL")
    if not upload_url:
        raise RuntimeError("Gemini did not return an upload URL.")
    return upload_url


def _finalize_upload(upload_url: str, file_path: Path, mime_type: str) -> UploadedFile:
    headers = {
        "Content-Length": str(file_path.stat().st_size),
        "X-Goog-Upload-Offset": "0",
        "X-Goog-Upload-Command": "upload, finalize",
        "Content-Type": mime_type,
    }

    with file_path.open("rb") as file_handle:
        response = _request_with_retries(
            "POST",
            upload_url,
            headers=headers,
            data=file_handle,
            timeout=120,
        )

    data = response.json()
    return _normalize_file(data["file"])


def _get_file(name: str) -> UploadedFile:
    response = _request_with_retries(
        "GET",
        f"{GEMINI_API_BASE}/v1beta/{name}",
        headers=_headers(),
        timeout=30,
    )
    return _normalize_file(response.json())


def upload_file(file_path: Path) -> UploadedFile:
    _require_api_key()
    mime_type = "text/markdown"

    upload_url = _start_upload(file_path, mime_type)
    uploaded = _finalize_upload(upload_url, file_path, mime_type)

    response = _request_with_retries(
        "GET",
        f"{GEMINI_API_BASE}/v1beta/{uploaded.name}",
        headers=_headers(),
        timeout=30,
    )
    file_data = response.json()

    while file_data.get("state") == "PROCESSING":
        time.sleep(2)
        response = _request_with_retries(
            "GET",
            f"{GEMINI_API_BASE}/v1beta/{file_data['name']}",
            headers=_headers(),
            timeout=30,
        )
        file_data = response.json()

    if file_data.get("state") != "ACTIVE":
        raise RuntimeError(f"File processing failed: {file_data.get('name')}")

    return _normalize_file(file_data)


def upload_to_gemini(changes: list[FileChange]) -> list[UploadedFile]:
    uploaded: list[UploadedFile] = []
    for change in changes:
        uploaded.append(upload_file(change.file_path))
    return uploaded


def load_files_meta() -> list[UploadedFile]:
    try:
        raw_files = json.loads(config.files_meta_file.read_text(encoding="utf-8"))
        return [
            UploadedFile(
                name=file_data["name"],
                uri=file_data["uri"],
                mimeType=file_data.get("mimeType") or "text/markdown",
            )
            for file_data in raw_files
        ]
    except Exception:
        return []


def save_files_meta(files: list[UploadedFile]) -> None:
    config.files_meta_file.parent.mkdir(parents=True, exist_ok=True)
    config.files_meta_file.write_text(
        json.dumps([asdict(file) for file in files], indent=2),
        encoding="utf-8",
    )


def test_assistant(files: list[UploadedFile]) -> None:
    if not files:
        return

    _require_api_key()
    file_parts = [
        {"fileData": {"fileUri": file.uri, "mimeType": file.mimeType}}
        for file in files
    ]
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    *file_parts,
                    {"text": "What is OptiSigns? Give a short summary."},
                ],
            }
        ],
        "systemInstruction": {"parts": [{"text": config.assistant_prompt}]},
    }

    response = _request_with_retries(
        "POST",
        f"{GEMINI_API_BASE}/v1beta/models/{config.gemini_model}:generateContent",
        headers={**_headers(), "Content-Type": "application/json"},
        json=payload,
        timeout=120,
    )

    print(f"\nOptiBot: {_parse_response_text(response.json())}\n")
