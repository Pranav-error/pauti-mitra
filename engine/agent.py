"""Pauti Mitra agent: a Kannada conversation that ends in a filled pouthi preparation pack.

The LLM (sarvam-105b) asks one question at a time and calls tools. It never decides who inherits or what
blocks the transfer: compute_heirs (heirs.py) and check_blockers (blockers.py) do, from code and live data.

Run:  .venv/bin/python engine/agent.py                 (chat in the terminal)
      .venv/bin/python engine/agent.py --script FILE   (one user message per line; for demos and tests)
Needs SARVAM_API_KEY (.env) and PAUTI_DB (survey index).
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bhoomi  # noqa: E402
import blockers as blockers_mod  # noqa: E402
import heirs as heirs_mod  # noqa: E402
import papers  # noqa: E402
import rtc_reader  # noqa: E402

for line in (HERE.parent / ".env").read_text().splitlines() if (HERE.parent / ".env").exists() else []:
    k, _, v = line.partition("=")
    os.environ.setdefault(k.strip(), v.strip())

DB = os.environ.get("PAUTI_DB", "data/karnataka_lands_full.db")
CASES = Path(os.environ.get("PAUTI_CASES", HERE.parent / "cases"))  # local only, gitignored: family data

SYSTEM = """You are Pauti Mitra, helping a rural Karnataka family move a dead person's land record (RTC) into the heirs' names (pouthi khata).
Speak simple, polite Kannada. Ask ONE short question at a time. The user may not read well: no lists of questions, no legal jargon.

Collect, in this order:
1. Who died (name, man or woman, date of death if known). Religion (the rules cover Hindu, Jain, Sikh, Buddhist).
2. Is there a will? Any family dispute or court case on the land? Is it ancestral (joint family) land?
3. Is the husband/wife alive? Is the dead person's mother alive (only matters if a man died)?
4. Every child: name, son or daughter, alive or dead. ALWAYS ask about daughters, including married daughters.
   For a child who died: their husband/wife if alive, and their children.
   Do NOT ask about husbands/wives or children of LIVING children: they do not inherit here. Do not ask for full names or surnames.
5. The land: village and survey number (hissa if they know it).
Whenever the user gives the village and survey number (or hissa), call find_land right away, even if family facts are still missing.
Call record_family as soon as you have family facts (call it again whenever facts change). Write names exactly as the
user says them, in Kannada script. Then call find_land, check_blockers, compute_heirs.

Rules:
- Never state heirs or shares yourself. Only explain what compute_heirs returns. If it says NeedsReview, say the revenue office must decide.
- If a daughter wants to give up her share, record it in relinquish, and tell the family she must confirm it herself, separately.
- Explain blockers in plain words with what to do.
- If find_land says deceased_on_rtc is false, stop and sort that out with the family before making papers.
- Everyone goes on the RTC together first; dividing the land is a separate later step. The family does not need to agree on division to start.
- When heirs and land are known, call make_papers and tell them what is in the pack (heirs, family tree drawing, affidavit draft, checklist, OTP-day list).
"""

PERSON = {"type": "object", "properties": {
    "name": {"type": "string"}, "sex": {"type": "string", "enum": ["M", "F"]}, "alive": {"type": "boolean"},
    "spouse": {"type": "string", "description": "living husband/wife of a child who died, else omit"},
    "children": {"type": "array", "items": {"type": "object", "properties": {
        "name": {"type": "string"}, "sex": {"type": "string", "enum": ["M", "F"]}, "alive": {"type": "boolean"},
        "spouse": {"type": "string"}, "children": {"type": "array", "items": {"type": "object"}}},
        "required": ["name", "sex", "alive"]}}},
    "required": ["name", "sex", "alive"]}

TOOLS = [
    {"type": "function", "function": {"name": "record_family", "description": "Save or update the family facts in the case file. Names in Kannada script as the user said them.",
     "parameters": {"type": "object", "properties": {
         "deceased_name": {"type": "string"}, "deceased_sex": {"type": "string", "enum": ["M", "F"]},
         "date_of_death": {"type": "string"},
         "religion": {"type": "string", "enum": ["hindu", "jain", "sikh", "buddhist", "muslim", "christian", "other"]},
         "will": {"type": "boolean"}, "dispute": {"type": "boolean"}, "ancestral": {"type": "boolean"},
         "spouse": {"type": "string", "description": "name of the living husband/wife of the deceased; omit if dead"},
         "mother": {"type": "string", "description": "name of the deceased's living mother; omit if dead"},
         "children": {"type": "array", "items": PERSON}, "applicant": {"type": "string"},
         "relinquish": {"type": "array", "items": {"type": "string"}}},
         "required": ["deceased_name", "deceased_sex"]}}},
    {"type": "function", "function": {"name": "find_land", "description": "Find the land record and its current owners on Bhoomi.",
     "parameters": {"type": "object", "properties": {
         "village": {"type": "string", "description": "village name, Kannada or English"}, "survey": {"type": "string"},
         "hissa": {"type": "string", "description": "hissa number exactly as the family says it"},
         "place": {"type": "string", "description": "district or taluk, only when find_land returned need_place"}},
         "required": ["village", "survey"]}}},
    {"type": "function", "function": {"name": "check_blockers", "description": "Live check for court cases, transfers in progress, and e-Pouthi already filed on the found land.",
     "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "compute_heirs", "description": "Work out legal heirs and shares from the recorded family. The only source of heirs and shares.",
     "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {"name": "make_papers", "description": "Make the PDF pack for the family.",
     "parameters": {"type": "object", "properties": {}}}},
]


def _norm_person(p):
    return {"name": p.get("name", ""), "sex": p.get("sex", "M"), "alive": bool(p.get("alive", True)),
            "spouse": p.get("spouse"), "children": [_norm_person(c) for c in p.get("children", []) or []]}


def owner_match(name, owners, cutoff=0.75):
    """Is the deceased on the RTC? Spelling-insensitive, Kannada or English, ignores initials and 'bin/ಬಿನ್' tails."""
    import difflib
    want = rtc_reader.squash(rtc_reader.latin(name))
    for o in owners:
        for part in o["name"].replace(".", " ").split():
            got = rtc_reader.squash(rtc_reader.latin(part))
            if len(got) > 2 and difflib.SequenceMatcher(None, got, want).ratio() >= cutoff:
                return True
    return False


class Case:
    def __init__(self, cid):
        self.path = CASES / f"{cid}.json"
        self.d = json.loads(self.path.read_text()) if self.path.exists() else {"id": cid, "land": {}, "blockers": []}

    def save(self):
        CASES.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.d, ensure_ascii=False, indent=1))

    # ---- tools ----
    def record_family(self, **a):
        d = self.d
        d["deceased"] = {"name": a["deceased_name"], "sex": a["deceased_sex"], "date_of_death": a.get("date_of_death")}
        for k in ("religion", "will", "dispute", "ancestral", "spouse", "mother", "applicant"):
            if k in a:
                d[k] = a[k]
        if "children" in a:
            d["children"] = [_norm_person(c) for c in a["children"]]
        if "relinquish" in a:
            d["relinquish"] = a["relinquish"]
        return {"saved": True, "children": len(d.get("children", []))}

    def find_land(self, village, survey, hissa=None, place=None):
        survey = str(survey).strip()
        cands = rtc_reader.locate({"village": village, "survey": survey}, DB) or []
        want = {rtc_reader.squash(village), rtc_reader.squash(rtc_reader.latin(village))}
        exact = [c for c in cands if rtc_reader.squash(c["village"]) in want]
        cands = exact or cands[:1]  # same name only; a fuzzy look-alike is never offered as a second choice
        if not cands:
            return {"found": False, "say": "village + survey number not found; ask to repeat the village name or survey number"}
        if len(cands) > 1:
            for c in cands:
                c["place"] = bhoomi.place_name(c["dist"], c["taluk"])
            if place:
                import difflib
                pick = difflib.get_close_matches(place.lower(), [c["place"].lower() for c in cands], n=1, cutoff=0.3)
                cands = [c for c in cands if pick and c["place"].lower() == pick[0]] or cands
            if len(cands) > 1:
                return {"found": False, "need_place": [c["place"] for c in cands],
                        "say": "several villages have this name; ask which district/taluk, then call again with place"}
        c = cands[0]
        f = bhoomi.open_survey(c["dist"], c["taluk"], c["hobli"], c["vlg"], survey)
        sur, hs = bhoomi.hissas(f)
        if not hs:
            return {"found": False, "say": "Bhoomi has no RTC for this survey number"}
        pick = next((v for v, label in hs if hissa and label == str(hissa).strip()), None)
        if not pick and len(hs) > 1:
            self.d["land"] = {}
            return {"found": False, "village": c["village"], "need_hissa": [label for _, label in hs],
                    "say": "ask which hissa, then call find_land again with hissa"}
        pick = pick or hs[0][0]
        info = bhoomi.owners(f, pick)
        c.setdefault("place", bhoomi.place_name(c["dist"], c["taluk"]))
        dead = (self.d.get("deceased") or {}).get("name")
        on_rtc = owner_match(dead, info["owners"]) if dead else None
        self.d["land"] = {**c, "survey": survey, "surnoc": sur, "hissa": dict(hs)[pick], "deceased_on_rtc": on_rtc, **info}
        out = {"found": True, "village": c["village"], "place": c["place"], "survey": survey, "hissa": dict(hs)[pick],
               "owners": info["owners"], "ongoing_mutation": info["ongoing_mutation"], "deceased_on_rtc": on_rtc}
        if on_rtc is False:
            out["say"] = ("the person who died is NOT among the RTC owners. Pouthi needs them on the RTC. Read out the owner "
                          "names and ask: wrong survey/hissa, a different spelling, or was the land never moved into their name "
                          "(then the older pouthi must be done first)")
        return out

    def check_blockers(self):
        L = self.d.get("land", {})
        if not L.get("vlg"):
            return {"error": "find_land first"}
        loc = {"dist": L["dist"], "taluk": L["taluk"], "hobli": L["hobli"], "village_code": f"{L['lgd']}_{L['vlg']}", "survey": L["survey"]}
        self.d["blockers"] = blockers_mod.blockers(loc)
        return {"blockers": self.d["blockers"]}

    def compute_heirs(self):
        if "deceased" not in self.d:
            return {"error": "record_family first"}
        try:
            hs = papers.heirs_for(self.d)
        except heirs_mod.NeedsReview as e:
            return {"needs_review": str(e), "say": "the revenue office must decide this case"}
        return {"heirs": [{"name": h["name"], "relation": h["relation"], "share": str(h["share"]),
                           "percent": round(float(h["share"]) * 100, 1)} for h in hs]}

    def make_papers(self):
        if "deceased" not in self.d:
            return {"error": "record_family first"}
        out = CASES / f"{self.d['id']}-pack.pdf"
        papers.write(self.d, str(out))
        return {"pdf": str(out)}


def chat(case, messages, client, log=print):
    """Run the model until it answers the user (resolving tool calls on the way)."""
    for _ in range(8):
        r = client.chat.completions(model="sarvam-105b", reasoning_effort="low", max_tokens=4000, tools=TOOLS, messages=messages)
        m = r.choices[0].message
        calls = m.tool_calls or []
        messages.append({"role": "assistant", "content": m.content or "",
                         **({"tool_calls": [{"id": t.id, "type": "function", "function": {"name": t.function.name, "arguments": t.function.arguments}}
                                            for t in calls]} if calls else {})})
        if not calls:
            return m.content
        for t in calls:
            args = json.loads(t.function.arguments or "{}")
            log(f"  [tool] {t.function.name} {json.dumps(args, ensure_ascii=False)[:200]}")
            try:
                res = getattr(case, t.function.name)(**args)
            except Exception as e:  # noqa: BLE001 - tell the model, keep the conversation going
                res = {"error": f"{type(e).__name__}: {e}"}
            case.save()
            log(f"  [result] {json.dumps(res, ensure_ascii=False, default=str)[:300]}")
            messages.append({"role": "tool", "tool_call_id": t.id, "content": json.dumps(res, ensure_ascii=False, default=str)})
    return "(too many tool steps)"


def main():
    from sarvamai import SarvamAI
    client = SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])
    case = Case(time.strftime("case-%Y%m%d-%H%M%S"))
    messages = [{"role": "system", "content": SYSTEM}]
    script = Path(sys.argv[sys.argv.index("--script") + 1]).read_text().splitlines() if "--script" in sys.argv else None
    turns = iter(script) if script else None
    print("Pauti Mitra (case", case.d["id"], ")")
    while True:
        try:
            user = next(turns) if turns else input("\nನೀವು: ")
        except (StopIteration, EOFError):
            break
        if not user.strip():
            continue
        if turns:
            print(f"\nನೀವು: {user}")
        messages.append({"role": "user", "content": user})
        print("\nಪೌತಿ ಮಿತ್ರ:", chat(case, messages, client))
    case.save()
    print("\ncase file:", case.path)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        assert owner_match("ರಾಮಪ್ಪ", [{"name": "ರಾಮಪ್ಪ ಬಿನ್ ಲೇ ಚನ್ನಪ್ಪ"}])
        assert owner_match("Ramappa", [{"name": "ರಾಮಪ್ಪ ಬಿನ್ ಚನ್ನಪ್ಪ"}])
        assert not owner_match("ರಾಮಪ್ಪ", [{"name": "J.ಕೇಶವ A.ಜಯರಾಮು"}])
        print("ok")
    else:
        main()
