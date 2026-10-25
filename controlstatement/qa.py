"""Natural-language Q&A engine over normalized financial transactions."""

import json
import urllib.request
import urllib.error
from typing import List, Optional

from controlstatement.config import AppConfig, get_config
from controlstatement.models import Transaction


def build_qa_prompt(question: str, transactions: List[Transaction]) -> str:
    """Build a guardrailed prompt containing normalized transaction context."""
    txn_lines = []
    for t in transactions:
        txn_lines.append(
            f"Date: {t.date} | Description: {t.description} | Amount: {t.amount:+.2f} {t.currency} | "
            f"Category: {t.category} | Balance: {t.balance if t.balance is not None else 'N/A'}"
        )

    prompt = f"""You are ControlStatement Financial Q&A, an offline private assistant.
Answer the user's question using ONLY the provided verified transaction records below.

GUARDRAILS (STRICT):
1. Rely ONLY on the facts directly mentioned in the TRANSACTION RECORDS.
2. Do NOT invent, assume, or extrapolate transactions, merchants, or amounts not in the list.
3. If no transactions match the query, explicitly state that no matching transactions were found.
4. Calculate totals accurately based on the numbers listed.
5. Provide a direct, concise, and helpful answer citing dates and amounts.

TRANSACTION RECORDS:
{chr(10).join(txn_lines)}

USER QUESTION: {question}

ANSWER:
"""
    return prompt.strip()


def answer_question(
    question: str,
    transactions: List[Transaction],
    config: Optional[AppConfig] = None,
) -> str:
    """Send user question and transaction context to local LLM with fallback."""
    if not transactions:
        return "No transactions are available in the selected document to answer your question."

    cfg = config or get_config()
    generate_url = f"{cfg.local_model_endpoint.rstrip('/')}/api/generate"

    prompt = build_qa_prompt(question, transactions)
    payload = {
        "model": cfg.local_model_name,
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "num_predict": 120,
            "temperature": 0.1,
            "top_p": 0.85,
        },
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
                return f"[Local model returned HTTP {resp.status}]"
    except urllib.error.URLError as e:
        return f"[Notice: Local AI endpoint is unreachable ({e.reason}).]"
    except Exception as e:
        return f"[Notice: Error communicating with local AI model ({e})]"
