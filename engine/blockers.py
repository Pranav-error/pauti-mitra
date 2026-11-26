"""Blocker check: is anything on this survey number going to stall an inheritance transfer?

Live, read-only lookups on the Karnataka e-Chawadi portal for ONE survey number:
  - pending revenue court cases (RCCMS)  -> the transfer will likely be held until the case is decided
  - pending mutations                    -> a transfer is already in progress (maybe the family's own application)
Nothing fetched is stored. A lookup that fails is `unknown`, never green.

Ported from the author's plotcheck (Oct 2026). Resolving a survey number to portal codes needs the
survey index (SQLite table `survey_index`, ~9M rows from the author's cadastral crawl). It is NOT in
this repo: point PAUTI_DB at it. Government records are not redistributed.

Portal format changed from JSON to HTML cards after 2026-10-28; parsers below match the 2026-11-27 layout.

Finding shape: {check, status (red/amber/green/unknown), detail, action, source}
"""
import html
import json
import os
import re
import sqlite3
import ssl
import sys
import urllib.request

try:
    import certifi
    _SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL = ssl.create_default_context()

DB = os.environ.get("PAUTI_DB", "data/karnataka_lands_full.db")
ECHAWADI = "https://rdservices.karnataka.gov.in/echawadi/Home/"


def base_survey(s):
    """'100/*/9' -> '100', ' 23 / * / 3,' -> '23'."""
    m = re.match(r"\s*(\d+)", str(s))
    return m.group(1) if m else None


def resolve(village, survey):
    """Village name or LGD code + survey number -> e-Chawadi portal codes."""
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    col = "village_code" if str(village).isdigit() else "upper(village_name)"
    rows = con.execute(
        f"select distinct village_name, village_code, dist, taluk, hobli, vlg from survey_index "
        f"where {col}=? and survey_no_norm=?", (str(village).upper(), base_survey(survey))).fetchall()
    if not rows:
        raise LookupError(f"survey {survey} not found in {village}")
    if len(rows) > 1:
        raise LookupError(f"{len(rows)} villages named {village}; ask for the taluk or use the LGD code")
    name, lgd, d, t, h, v = rows[0]
    return {"village": name, "lgd": lgd, "dist": d, "taluk": t, "hobli": h, "village_code": f"{lgd}_{v}", "survey": survey}


def _text(raw):
    """Portal now returns rendered HTML cards (changed after 2026-10-28; it used to be JSON)."""
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", "", raw, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()


def _echawadi(endpoint, loc, **extra):
    p = {"Dist": loc["dist"], "Taluk": loc["taluk"], "Hobli": loc["hobli"], "Village": loc["village_code"], **extra}
    req = urllib.request.Request(ECHAWADI + endpoint, data=json.dumps({"paramObj": p}).encode(),
                                 headers={"Content-Type": "application/json; charset=utf-8", "User-Agent": "Mozilla/5.0"})
    t = _text(urllib.request.urlopen(req, timeout=30, context=_SSL).read().decode())
    if "Items Found" not in t and "No Records Found" not in t:
        raise RuntimeError("portal response format changed")
    return t


SURVEY = r"(\d+\s*/\s*[\w*]+\s*/\s*[\w*]+)"


def parse_cases(t):
    """RCCMS cards: 'Case No.: X Applicant Name: Y Village Name : V Case Status : S Survey No. : 23 / * / 3'."""
    return [dict(zip(("case", "applicant", "status", "survey"), m)) for m in re.findall(
        r"Case No\.: (\S+) Applicant Name: (.*?) Village Name : .*? Case Status : (.*?) Survey No\. : " + SURVEY, t)]


def parse_mutations(t):
    """Mutation cards: '... ಸ್ವಾಧೀನತೆ ರೀತಿ: (ಆ) ಕ್ರಯ Status: S ಸರ್ವೆ ನಂ.: 23 / * / 3, 23 / * / 4,'."""
    out = []
    for kind, status, surveys in re.findall(r"ಸ್ವಾಧೀನತೆ ರೀತಿ: (.*?) Status: (.*?) ಸರ್ವೆ ನಂ\.: ([\d\s/*,\w]+?)(?: Form-|$)", t):
        out.append({"kind": kind, "status": status, "surveys": [x.strip() for x in surveys.split(",") if x.strip()]})
    return out


def _f(check, status, detail, action, source):
    return {"check": check, "status": status, "detail": detail, "action": action, "source": source}


def _unknown(check, e, source):
    return _f(check, "unknown", f"lookup failed: {e}", "Check at the village accountant's office.", source)


def blockers(loc):
    sn = base_survey(loc["survey"])
    out = []

    c = "Pending revenue court case"
    try:
        cases = [x for x in parse_cases(_echawadi("GetActiveRCCMS", loc, RCCMSSearchtype="P")) if base_survey(x["survey"]) == sn]
        for x in cases:
            out.append(_f(c, "red", f"{x['case']} on {x['survey']}, status {x['status']}, applicant {x['applicant']}",
                          "The transfer will likely wait for this case. Ask the Tahsildar office about it before applying.",
                          "e-Chawadi RCCMS (live)"))
            if "ಸರ್ಕಾರ" in x["applicant"]:
                out.append(_f("Government land", "red", f"Government is a party: {x['applicant']}",
                              "Inheritance transfer may not apply. Send to the revenue office.", "e-Chawadi RCCMS"))
        if not cases:
            out.append(_f(c, "green", "no active case on this survey number", "", "e-Chawadi RCCMS (live)"))
    except Exception as e:  # noqa: BLE001 - a failed lookup must never read as "clear"
        out.append(_unknown(c, e, "e-Chawadi RCCMS"))

    c = "Transfer already in progress"
    try:
        muts = [m for m in parse_mutations(_echawadi("GetActiveCasesofMutationStatus", loc))
                if sn in {base_survey(x) for x in m["surveys"]}]
        for m in muts:
            out.append(_f(c, "amber", f"{m['kind']} on {', '.join(m['surveys'])}: {m['status']}",
                          "Check if this is the family's own application before filing again; if not, someone else "
                          "is transferring this land.", "e-Chawadi mutation register (live)"))
        if not muts:
            out.append(_f(c, "green", "no pending mutation on this survey number", "", "e-Chawadi mutation register (live)"))
    except Exception as e:  # noqa: BLE001
        out.append(_unknown(c, e, "e-Chawadi mutations"))

    # e-Pouthi = the govt inheritance drive. Records carry heirs' Aadhaar and mobile: never surfaced, only presence.
    # ponytail: filled-record layout not seen yet (Nagavara has none); parse is presence-only until we see one.
    c = "e-Pouthi application already filed"
    for kind, label in (("P", "pending"), ("W", "ongoing")):
        try:
            t = _echawadi("GetEpoutiData", loc, EPouthiSearchType=kind)
            if "No Records Found" in t:
                continue
            if sn in {base_survey(x) for x in re.findall(SURVEY, t)}:
                out.append(_f(c, "amber", f"an e-Pouthi application ({label}) includes this survey number",
                              "The family may already have applied. Confirm with the village accountant before starting.",
                              "e-Chawadi e-Pouthi (live)"))
            else:
                out.append(_f(c, "unknown", f"e-Pouthi records ({label}) exist in this village; could not match survey",
                              "Check at the village accountant's office.", "e-Chawadi e-Pouthi (live)"))
        except Exception as e:  # noqa: BLE001
            out.append(_unknown(c, e, "e-Chawadi e-Pouthi"))
    if not any(f["check"] == c for f in out):
        out.append(_f(c, "green", "no pending or ongoing e-Pouthi application in this village", "", "e-Chawadi e-Pouthi (live)"))
    return out


if __name__ == "__main__":
    assert base_survey("100/*/9") == "100" and base_survey(" 23 / * / 3,") == "23" and base_survey("") is None
    t = "Total 1 Items Found Case No.: RP/1/2010 Applicant Name: A B Village Name : X Case Status : Pending Survey No. : 23 / * / 3 Case Details"
    assert parse_cases(t) == [{"case": "RP/1/2010", "applicant": "A B", "status": "Pending", "survey": "23 / * / 3"}]
    t = "ಸ್ವಾಧೀನತೆ ರೀತಿ: (ಆ) ಕ್ರಯ Status: ಬಾಕಿಇದೆ ಸರ್ವೆ ನಂ.: 23 / * / 3, 24 / * / 1, Form-12"
    assert parse_mutations(t) == [{"kind": "(ಆ) ಕ್ರಯ", "status": "ಬಾಕಿಇದೆ", "surveys": ["23 / * / 3", "24 / * / 1"]}]
    village, survey = sys.argv[1:3] or ["938328", "23"]  # Nagavara 23: mutation stuck behind a case (seen 2026-10-28)
    loc = resolve(village, survey)
    for f in blockers(loc):
        print(f"[{f['status']:7}] {f['check']}: {f['detail']}\n          -> {f['action']}  <{f['source']}>")
