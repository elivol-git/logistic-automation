import json
import anthropic
from config import CLAUDE_API_KEY, CLAUDE_MODEL

_PROMPT_TEMPLATE = """\
You are an assistant for a logistics company.
A customer sent an email about container unloading. Reply professionally in {language}.
Return ONLY a JSON object with exactly two keys: "subject" (reply subject line) and "body" (reply email body).
Do not include any text outside the JSON object.

Customer email:
{email_body}
"""

def generate_reply(email_body: str, language: str) -> dict:
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
    prompt = _PROMPT_TEMPLATE.format(language=language, email_body=email_body)
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        raw = raw.rsplit("```", 1)[0].strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Claude returned invalid JSON: {e}\nRaw: {raw}") from e
    return result
