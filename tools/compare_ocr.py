"""Head-to-head: Tesseract (free, local) vs Sarvam document intelligence on the same real RTCs.

Both engines' raw text is scored the same way against the Bhoomi portal's own labels:
  village  - the correct village name appears (spelling-insensitive, fuzzy >= 0.85)
  survey   - the survey number appears as a standalone token
  owners   - share of the portal's owner names that appear (fuzzy >= 0.8 over 1-4 token windows)

Run: TESSDATA_PREFIX=... python3 tools/compare_ocr.py BHOOMI_DIR SARVAM_HTML_DIR
"""
import difflib
import glob
import html as H
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
import rtc_reader as r  # noqa: E402


def sarvam_text(path):
    s = open(path, encoding="utf-8").read()
    s = re.sub(r"<style.*?</style>|<script.*?</script>|<head.*?</head>", "", s, flags=re.S)
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", s)))


def tokens(text):
    return [t.strip(":.|,()") for t in text.replace("‌", "").replace("‍", "").split() if t.strip(":.|,()")]


def key(s):
    return r.squash(r.latin(s)) if re.search(r"[ಀ-೿]", s) else r.squash(s)


def has(toks, target, cutoff, max_window=4):
    want = key(target)
    if not want:
        return False
    for n in range(1, max_window + 1):
        for i in range(len(toks) - n + 1):
            if difflib.SequenceMatcher(None, key("".join(toks[i:i + n])), want).ratio() >= cutoff:
                return True
    return False


def score(text, lab):
    toks = tokens(text)
    names = [o["name"].replace("ಲೇ", " ") for o in lab["owners"]][:10]  # big joint holdings: first 10
    return {"village": has(toks, lab["village"] or "", 0.85, 2),
            "survey": str(lab["survey"]) in toks,
            "owners": sum(has(toks, n, 0.8) for n in names) / len(names) if names else 1.0}


def main(bdir, sdir):
    res = {"tesseract": [], "sarvam": []}
    for img in sorted(glob.glob(os.path.join(bdir, "*.jpg"))):
        name = os.path.basename(img)[:-4]
        sv = os.path.join(sdir, name + ".html")
        if not os.path.exists(sv):
            continue
        lab = json.load(open(img[:-4] + ".json", encoding="utf-8"))
        res["tesseract"].append(score(" ".join(w["t"] for w in r.ocr(img)), lab))
        res["sarvam"].append(score(sarvam_text(sv), lab))
    for eng, rows in res.items():
        n = len(rows)
        print(eng, json.dumps({k: round(sum(float(x[k]) for x in rows) / n, 3) for k in rows[0]} | {"n": n}))
    return res


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
