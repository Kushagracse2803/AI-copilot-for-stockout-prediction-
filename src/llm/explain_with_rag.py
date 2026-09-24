import sys, os
import ollama

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from rag.retriever import retrieve_relevant_chunks
from llm.explain import get_risk_level, FEATURE_MEANINGS, BOOLEAN_FEATURES, format_actual_value

MODEL_NAME = "llama3.2:1b"

SYSTEM_PROMPT = """You are an inventory risk analyst for a bookstall business.
Your job is to explain stockout risk predictions AND recommend an action,
grounded in the company's actual policy documents.

STRICT RULES:
- Only use the exact facts and policy text given to you below. Never invent
  numbers, policy rules, or reasons that aren't explicitly provided.
- Always state the exact risk score, risk level, product name and branch given.
- NEVER compare two numbers that have different units (e.g. do not compare
  "days of stock remaining" to a "unit count" - these measure different
  things and cannot be compared directly, even if both are numbers).
- For a Yes/No factor, state its ACTUAL VALUE plainly first (e.g. "It is
  NOT currently admission season") before explaining its implication - do
  not write a sentence that implies the opposite of the ACTUAL VALUE given.
- When you reference a policy rule, mention which document it came from
  (e.g., "per safety_stock_policy.txt").
- If the retrieved policy text doesn't clearly apply, say so honestly instead
  of guessing.
- Keep the explanation to 3-4 sentences."""


def build_policy_query(category: str, is_admission_season: bool) -> str:
    season_text = "during admission season" if is_admission_season else "in normal season"
    return f"safety stock and replenishment policy for {category} {season_text}"


def generate_explanation_with_evidence(
    product_id: str, branch: str, category: str, risk_score: float,
    top_drivers: list[dict], is_admission_season: bool
) -> dict:
    # --- Step 1: retrieve relevant policy chunks ---
    query = build_policy_query(category, is_admission_season)
    evidence_chunks = retrieve_relevant_chunks(query, top_k=2)

    # de-duplicate by source file - citing the same document twice isn't useful
    seen_sources = set()
    unique_chunks = []
    for c in evidence_chunks:
        if c["source"] not in seen_sources:
            unique_chunks.append(c)
            seen_sources.add(c["source"])
    evidence_chunks = unique_chunks

    evidence_text = "\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in evidence_chunks
    )

    # --- Step 2: build the same fact section as before (Piece 2) ---
    risk_level = get_risk_level(risk_score)
    drivers_text = "\n".join(
        f"- {d['feature']}: {FEATURE_MEANINGS.get(d['feature'], d['feature'])} "
        f"-> ACTUAL VALUE: {format_actual_value(d['feature'], d['actual_value'])}"
        for d in top_drivers
    )

    user_prompt = f"""Product: {product_id}
Branch: {branch}
Category: {category}
Stockout risk score: {risk_score:.2%}
Risk level: {risk_level}

Top factors driving this risk:
{drivers_text}

Relevant company policy (retrieved from documents):
{evidence_text}

Using ONLY the facts and policy text above, write a 3-4 sentence explanation
for a store planner. Include a recommended action based on the policy, and
cite which document the policy came from."""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    return {
        "explanation": response["message"]["content"],
        "evidence_sources": [c["source"] for c in evidence_chunks],
    }


if __name__ == "__main__":
    result = generate_explanation_with_evidence(
        product_id="BOOK_SChand_5_Maths",
        branch="Main Market",
        category="Book",
        risk_score=0.82,
        top_drivers=[
            {"feature": "is_admission_season", "importance": 0.90, "actual_value": 1},
            {"feature": "days_of_cover", "importance": 0.03, "actual_value": 2.4},
        ],
        is_admission_season=True,
    )
    print("Explanation:\n", result["explanation"])
    print("\nEvidence sources:", result["evidence_sources"])