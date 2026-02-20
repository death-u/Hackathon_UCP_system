# myapp/ai_groq.py
import json
from groq import Groq
from django.conf import settings


# ==========================================================
# SYSTEM PROMPT (STRICT + RULE-BASED + EXPLAINABLE)
# ==========================================================

SYSTEM_PROMPT = """
You are an insurance claim triage assistant.

Return STRICT JSON only (no markdown, no extra text).
Format EXACTLY like this:

{
  "risk_score": 0,
  "risk_level": "low",
  "summary": "short explanation",
  "recommendation": "auto-approve",
  "flags": ["short reason"],
  "rule_breakdown": {
    "vague": 0,
    "suspicious_wording": 0,
    "amount_ratio_points": 0,
    "emotional": 0,
    "contradictions": 0
  }
}

SCORING RULES:

Start risk_score at 0.

Add:
+3 if description is vague (missing clear event details)
+3 if suspicious wording (lost, stolen, disappeared, no witnesses)
+2 if amount_ratio_points is 2
+1 if amount_ratio_points is 1
+2 if emotional manipulation tone detected
+2 if contradictions exist

Clamp final score between 0 and 10.

Risk level:
0-3 -> low
4-7 -> medium
8-10 -> high

Recommendation:
low -> auto-approve
medium -> needs-review
high -> flag-suspicious

Use amount_ratio_points exactly as given.

IMPORTANT:
1) risk_score MUST equal:
vague + suspicious_wording + amount_ratio_points + emotional + contradictions
2) rule_breakdown values must be ONLY:
- vague: 0 or 3
- suspicious_wording: 0 or 3
- amount_ratio_points: 0 or 1 or 2
- emotional: 0 or 2
- contradictions: 0 or 2

Output JSON only.
""".strip()


# ==========================================================
# DETERMINISTIC AMOUNT SCORING (PYTHON SIDE)
# ==========================================================

def _amount_ratio_points(amount, coverage_limit):
    """
    Returns:
        (points, ratio)
    """
    try:
        a = float(amount)
        c = float(coverage_limit)
        if c <= 0:
            return 0, 0.0
        ratio = a / c
    except Exception:
        return 0, 0.0

    if ratio >= 0.80:
        return 2, ratio
    elif ratio >= 0.60:
        return 1, ratio
    return 0, ratio


# ==========================================================
# NORMALIZATION + VALIDATION (PROTECT DATABASE)
# ==========================================================

def _clamp(num, lo, hi):
    return max(lo, min(hi, num))


def _normalize_rule_breakdown(rb, ratio_points):
    """
    Coerce breakdown into expected integers and enforce allowed values.
    Also enforce amount_ratio_points equals ratio_points from Python.
    """
    if not isinstance(rb, dict):
        rb = {}

    def get_int(key, default=0):
        try:
            return int(rb.get(key, default))
        except Exception:
            return default

    vague = get_int("vague", 0)
    suspicious = get_int("suspicious_wording", 0)
    emotional = get_int("emotional", 0)
    contradictions = get_int("contradictions", 0)

    # enforce allowed values
    vague = 3 if vague == 3 else 0
    suspicious = 3 if suspicious == 3 else 0
    emotional = 2 if emotional == 2 else 0
    contradictions = 2 if contradictions == 2 else 0

    # lock ratio points to Python result (critical)
    amount_ratio_points = int(ratio_points)
    if amount_ratio_points not in (0, 1, 2):
        amount_ratio_points = 0

    return {
        "vague": vague,
        "suspicious_wording": suspicious,
        "amount_ratio_points": amount_ratio_points,
        "emotional": emotional,
        "contradictions": contradictions,
    }


def _derive_level_and_reco(score):
    if score <= 3:
        return "low", "auto-approve"
    elif score <= 7:
        return "medium", "needs-review"
    return "high", "flag-suspicious"


def _normalize_ai_output(data, ratio_points):
    """
    Normalizes fields, enforces scoring consistency,
    and protects DB from malformed responses.
    """
    if not isinstance(data, dict):
        data = {}

    # summary
    summary = str(data.get("summary", "")).strip()[:800]

    # flags
    flags = data.get("flags", [])
    if not isinstance(flags, list):
        flags = [str(flags)]
    flags = [str(f)[:160] for f in flags][:10]

    # rule breakdown (enforced + locked ratio points)
    rb = _normalize_rule_breakdown(data.get("rule_breakdown", {}), ratio_points)

    # compute score from breakdown (authoritative)
    computed_score = (
        rb["vague"]
        + rb["suspicious_wording"]
        + rb["amount_ratio_points"]
        + rb["emotional"]
        + rb["contradictions"]
    )
    computed_score = _clamp(float(computed_score), 0.0, 10.0)

    # derive level/reco from computed score (authoritative)
    risk_level, recommendation = _derive_level_and_reco(computed_score)

    # If model's risk_score disagrees, we override and note it.
    try:
        model_score = float(data.get("risk_score", computed_score))
    except Exception:
        model_score = computed_score

    model_score = _clamp(model_score, 0.0, 10.0)

    if abs(model_score - computed_score) > 0.0001:
        flags = (flags or []) + ["Adjusted risk_score to match rule_breakdown"]

    return {
        "risk_score": computed_score,
        "risk_level": risk_level,
        "summary": summary,
        "recommendation": recommendation,
        "flags": flags,
        "rule_breakdown": rb,
    }


# ==========================================================
# MAIN ANALYSIS FUNCTION
# ==========================================================

def analyze_claim_text(description, amount, coverage_limit, policy_type):
    client = Groq(api_key=settings.GROQ_API_KEY)

    # Deterministic ratio scoring
    ratio_points, ratio = _amount_ratio_points(amount, coverage_limit)

    # map vague policy types
    policy_type_for_ai = policy_type if policy_type != "any" else "general"

    payload = {
        "policy_type": policy_type_for_ai,
        "claim_amount": str(amount),
        "coverage_limit": str(coverage_limit),
        "amount_ratio": ratio,
        "amount_ratio_points": ratio_points,
        "STRICT_RULE": "amount_ratio_points is final and must be used exactly as given",
        "description": description,
    }

    response = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        temperature=0.0,
        max_tokens=500,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(payload)},
        ],
    )

    raw = (response.choices[0].message.content or "").strip()

    # parse JSON safely
    try:
        data = json.loads(raw)
    except Exception:
        return {
            "risk_score": 5.0,
            "risk_level": "medium",
            "summary": "AI response parsing failed.",
            "recommendation": "needs-review",
            "flags": ["Invalid JSON response from model"],
            "rule_breakdown": {
                "vague": 0,
                "suspicious_wording": 0,
                "amount_ratio_points": ratio_points,
                "emotional": 0,
                "contradictions": 0,
            },
        }

    return _normalize_ai_output(data, ratio_points)