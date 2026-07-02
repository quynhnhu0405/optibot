import sys

from config import config
from uploader import GEMINI_API_BASE, _request_with_retries, load_files_meta


def _parse_response_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""

    parts = candidates[0].get("content", {}).get("parts") or []
    return "".join(part.get("text", "") for part in parts)


def _ask_gemini(question: str, file_parts: list[dict]) -> str:
    if not config.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is required.")

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [*file_parts, {"text": question}],
            }
        ],
        "systemInstruction": {"parts": [{"text": config.assistant_prompt}]},
    }

    response = _request_with_retries(
        "POST",
        f"{GEMINI_API_BASE}/v1beta/models/{config.gemini_model}:generateContent",
        headers={
            "x-goog-api-key": config.gemini_api_key,
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=120,
    )
    return _parse_response_text(response.json())


def chat() -> None:
    files = load_files_meta()
    if len(files) == 0:
        print("[ERROR] No uploaded files found. Run 'python app/main.py' first.", file=sys.stderr)
        raise SystemExit(1)

    file_parts = [
        {"fileData": {"fileUri": file.uri, "mimeType": file.mimeType}}
        for file in files
    ]

    print("\nOptiBot Chat")
    print("Ask anything about OptiSigns (Type 'exit' to quit)\n")

    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question in ("exit", "quit"):
            break

        try:
            answer = _ask_gemini(question, file_parts)
            print(f"\nOptiBot: {answer}\n")
        except Exception as error:
            print(f"[ERROR] Chat call failed: {error}", file=sys.stderr)


if __name__ == "__main__":
    try:
        chat()
    except KeyboardInterrupt:
        print()
