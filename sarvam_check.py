"""One Sarvam call to prove the key works. Run: .venv/bin/python sarvam_check.py"""
import os
from pathlib import Path

from sarvamai import SarvamAI

# Read .env without adding python-dotenv; the real environment wins.
for line in (Path(__file__).parent / ".env").read_text().splitlines():
    k, _, v = line.partition("=")
    if k.strip() and not k.startswith("#"):
        os.environ.setdefault(k.strip(), v.strip())

client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])
r = client.chat.completions(
    model="sarvam-105b",
    messages=[{"role": "user", "content": "In one Kannada sentence, what is a pauti khate?"}],
    reasoning_effort="low",  # it reasons by default; at 200 tokens it spent all of them thinking. API rejects "none".
    max_tokens=4000,
)
print(r.choices[0].message.content)
