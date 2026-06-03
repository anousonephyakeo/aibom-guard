"""A toy hiring assistant: screens resumes and ranks candidates."""
from anthropic import Anthropic
from transformers import pipeline

client = Anthropic()
classifier = pipeline("text-classification")

def screen_resume(text: str) -> dict:
    """Candidate ranking for recruitment scoring (resume screening)."""
    # NOTE: employment / applicant tracking use case
    resp = client.messages.create(model="claude-3-5-sonnet", max_tokens=200,
                                  messages=[{"role": "user", "content": text}])
    return {"decision": resp}
