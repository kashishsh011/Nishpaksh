"""
gemini_client.py
----------------
Centralised Gemini API client with:
  - Task-based model routing (classify/analyze/narrative)
  - Module-level session cache (dict keyed by task:hash)
  - Graceful fallback — never raises, returns None on total failure
  - Rate-limit retry with backoff
"""

from google import genai
from google.genai import types
import hashlib
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Task-based model routing — preserves Pro quota for narrative generation
TASK_MODELS = {
    "classify": [
        "gemini-2.5-flash-lite",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-pro",
    ],
    "analyze": [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.5-pro",
    ],
    "narrative": [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
    ],
}

# Module-level session cache — avoids duplicate API calls
_gemini_cache: dict[str, str] = {}

# Singleton client
_client = None


def _get_client():
    """Lazy-initialise and return the Gemini client."""
    global _client
    if _client is not None:
        return _client
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key or api_key == "your-gemini-api-key-here":
        return None
    _client = genai.Client(api_key=api_key)
    return _client


def _cache_key(prompt: str, task: str) -> str:
    """Generate a deterministic cache key from task + prompt hash."""
    h = hashlib.md5(prompt.encode("utf-8")).hexdigest()
    return f"{task}:{h}"


def call_gemini(
    prompt: str,
    task: str = "narrative",
    system_instruction: str = "",
    temperature: float = 0.3,
    max_output_tokens: int = 2000,
) -> str | None:
    """
    Central Gemini call with task-based model routing and caching.

    Args:
        prompt: The user prompt to send.
        task: One of "classify", "analyze", "narrative". Determines model order.
        system_instruction: Optional system instruction.
        temperature: Generation temperature.
        max_output_tokens: Max tokens in response.

    Returns:
        Raw text response on success, None on total failure (never raises).
    """
    # 1. Check cache first
    key = _cache_key(prompt, task)
    if key in _gemini_cache:
        print(f"[Gemini] Cache hit for task={task}")
        return _gemini_cache[key]

    # 2. Get client
    client = _get_client()
    if client is None:
        print("[Gemini] No API key configured — skipping")
        return None

    # 3. Determine model chain for this task
    models = TASK_MODELS.get(task, TASK_MODELS["narrative"])
    max_retries = 2  # attempts per model

    last_error = None
    for model_id in models:
        for attempt in range(max_retries):
            try:
                print(f"[Gemini] task={task} model={model_id} attempt={attempt + 1}")

                config_kwargs = {
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                }
                if system_instruction:
                    config_kwargs["system_instruction"] = system_instruction

                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                    config=types.GenerateContentConfig(**config_kwargs),
                )
                result = response.text.strip()
                print(f"[Gemini] Success: task={task} model={model_id}")

                # Store in cache
                _gemini_cache[key] = result
                return result

            except Exception as e:
                error_str = str(e)
                last_error = e
                print(f"[Gemini] Failed: {model_id} attempt {attempt + 1}: {e}")

                # Rate-limited — wait and retry same model
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    if attempt < max_retries - 1:
                        wait = 30
                        print(f"[Gemini] Rate limited — waiting {wait}s...")
                        time.sleep(wait)
                        continue
                # Other error — skip to next model
                break

    print(f"[Gemini] All models failed for task={task}. Last error: {last_error}")
    return None


def parse_json_response(raw: str | None) -> list | dict | None:
    """
    Parse a Gemini response that should be JSON.
    Strips markdown fences if present. Returns None on failure.
    """
    if raw is None:
        return None
    text = raw.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json) and last line (```)
        end = len(lines) - 1 if lines[-1].strip() == "```" else len(lines)
        text = "\n".join(lines[1:end])
        if text.startswith("json"):
            text = text[4:].strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError) as e:
        print(f"[Gemini] JSON parse failed: {e}")
        return None
