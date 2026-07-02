from dataclasses import dataclass
from pathlib import Path
import hashlib
import json

from config import config


HashRecord = dict[str, str]


@dataclass(frozen=True)
class FileChange:
    file_path: Path
    hash: str
    status: str


def sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_hashes() -> HashRecord:
    try:
        return json.loads(config.hash_file.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_hashes(hashes: HashRecord) -> None:
    config.hash_file.parent.mkdir(parents=True, exist_ok=True)
    config.hash_file.write_text(json.dumps(hashes, indent=2), encoding="utf-8")


def diff_files(file_paths: list[Path], old_hashes: HashRecord) -> tuple[list[FileChange], int, int, int]:
    changes: list[FileChange] = []
    added = 0
    updated = 0
    skipped = 0

    for file_path in file_paths:
        content = file_path.read_text(encoding="utf-8")
        file_hash = sha256(content)
        file_name = file_path.name

        if not old_hashes.get(file_name):
            changes.append(FileChange(file_path=file_path, hash=file_hash, status="added"))
            added += 1
        elif old_hashes[file_name] != file_hash:
            changes.append(FileChange(file_path=file_path, hash=file_hash, status="updated"))
            updated += 1
        else:
            skipped += 1

    return changes, added, updated, skipped
