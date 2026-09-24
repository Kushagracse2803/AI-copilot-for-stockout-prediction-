import ollama

MODEL_NAME = "llama3.2:1b"

SYSTEM_PROMPT = """You are an inventory risk analyst for a bookstall business.
Your job is to explain stockout risk predictions in simple, clear business language.

STRICT RULES:
- Only use the exact facts given to you below. Never guess, assume, or invent any
  reason, event, number, or detail that is not explicitly provided.
- Do not mention "bestseller status", "popularity", "second month in store", or
  any other reason unless it was explicitly given to you.
- Always state the exact risk score percentage given to you.
- Always use the exact risk level label given to you (Low/Medium/High) consistently
  throughout your entire response - do not soften it or add another level like
  "moderate to low".
- Always state the exact product name and branch given to you.
- When mentioning a factor's actual value (like days of stock remaining), use
  ONLY the exact value given - never invent or estimate a number yourself.
- Keep the explanation to 2-3 sentences."""

FEATURE_MEANINGS = {
    "is_admission_season": "it is currently admission season (April-June), when demand for books rises sharply",
    "admission_season_next_30d": "admission season is starting within the next 30 days",
    "days_of_cover": "days of stock remaining at the current sales pace",
    "lead_time_delay_flag": "the supplier is currently delivering slower than usual",
    "sales_trend_ratio": "recent sales trend compared to the prior period",
}

# how to turn each feature's raw value into a human-readable fact
BOOLEAN_FEATURES = {"is_admission_season", "admission_season_next_30d", "lead_time_delay_flag"}


def format_actual_value(feature: str, value: float) -> str:
    if feature in BOOLEAN_FEATURES:
        return "Yes" if value >= 1 else "No"
    if feature == "days_of_cover":
        return f"{value:.1f} days"
    if feature == "sales_trend_ratio":
        return f"{value:.2f}x (1.0 = stable)"
    return f"{value}"


def get_risk_level(risk_score: float) -> str:
    if risk_score < 0.20:
        return "Low"
    elif risk_score < 0.50:
        return "Medium"
    else:
        return "High"


def build_user_prompt(product_id: str, branch: str, risk_score: float, top_drivers: list[dict]) -> str:
    risk_level = get_risk_level(risk_score)
    drivers_text = "\n".join(
        f"- {d['feature']}: {FEATURE_MEANINGS.get(d['feature'], d['feature'])} "
        f"-> ACTUAL VALUE: {format_actual_value(d['feature'], d['actual_value'])}"
        for d in top_drivers
    )
    return f"""Product: {product_id}
Branch: {branch}
Stockout risk score: {risk_score:.2%} (chance of stocking out in the next 7 days)
Risk level: {risk_level}

Top factors driving this risk, with their real current values:
{drivers_text}

Using ONLY the facts above, write a 2-3 sentence explanation for a store planner.
Start with the exact risk score, risk level, and product name. When referencing
a factor's value, use only the ACTUAL VALUE given - do not invent any other number."""


def generate_explanation(product_id: str, branch: str, risk_score: float, top_drivers: list[dict]) -> str:
    user_prompt = build_user_prompt(product_id, branch, risk_score, top_drivers)

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response["message"]["content"]


if __name__ == "__main__":
    explanation = generate_explanation(
        product_id="BOOK_SChand_5_Maths",
        branch="Main Market",
        risk_score=0.82,
        top_drivers=[
            {"feature": "is_admission_season", "importance": 0.90, "actual_value": 1},
            {"feature": "days_of_cover", "importance": 0.03, "actual_value": 2.4},
        ],
    )
    print(explanation)