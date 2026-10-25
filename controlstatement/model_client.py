"""Client for local model inference (Ollama / compatible local endpoints)."""

import json
import urllib.request
import urllib.error
from typing import List, Optional

from controlstatement.config import AppConfig, get_config
from controlstatement.models import Transaction
from controlstatement.rules import RuleAnalysisReport
from controlstatement.prompt_templates import build_analysis_prompt


def is_local_model_available(config: Optional[AppConfig] = None, timeout: float = 2.0) -> bool:
    """Check if the local Ollama / LLM endpoint is active on localhost."""
    cfg = config or get_config()
    tags_url = f"{cfg.local_model_endpoint.rstrip('/')}/api/tags"

    try:
        req = urllib.request.Request(tags_url, headers={"User-Agent": "ControlStatement/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def generate_ai_summary(
    analysis: RuleAnalysisReport,
    transactions: List[Transaction],
    config: Optional[AppConfig] = None,
) -> str:
    """Invoke local LLM to generate plain-language summary, trends, and nudges.

    Gracefully degrades if endpoint is offline or unavailable.
    """
    cfg = config or get_config()
    generate_url = f"{cfg.local_model_endpoint.rstrip('/')}/api/generate"

    prompt = build_analysis_prompt(analysis, transactions)
    payload = {
        "model": cfg.local_model_name,
        "prompt": prompt,
        "stream": False,
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            generate_url,
            data=data_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "ControlStatement/0.1"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=cfg.request_timeout) as resp:
            if resp.status == 200:
                body = json.loads(resp.read().decode("utf-8"))
                return body.get("response", "").strip()
            else:
                return (
                    f"[Notice: Local AI model returned HTTP {resp.status}. "
                    f"Showing rule-based financial analysis alone.]"
                )
    except urllib.error.URLError as e:
        return (
            f"[Notice: Local AI model endpoint ({cfg.local_model_endpoint}) is unreachable: {e.reason}. "
            f"Showing rule-based financial analysis alone.]"
        )
    except TimeoutError:
        return (
            "[Notice: Local AI inference timed out. "
            "Showing rule-based financial analysis alone.]"
        )
    except Exception as e:
        return (
            f"[Notice: Local AI inference encountered error ({e}). "
            f"Showing rule-based financial analysis alone.]"
        )
