"""Score the tier-1 RTC reader against labelled RTCs.

  real Bhoomi set (bhoomi-NNN.jpg + .json from the portal):  did it LOCATE the record?
      village codes (top candidate == label), survey, hissa
  synthetic set (NNN.jpg + .json from tools/make_rtcs.py):   did it READ the fields?
      survey, hissa, MR numbers, earlier inheritance (ಪೌತಿ)

Run: TESSDATA_PREFIX=... python3 tools/eval_reader.py DIR [SURVEY_INDEX_DB]
"""
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "engine"))
import rtc_reader  # noqa: E402


def main(d, db=None):
    rows, t0 = [], time.time()
    for img in sorted(glob.glob(os.path.join(d, "*.jpg"))):
        lab = json.load(open(img[:-4] + ".json", encoding="utf-8"))
        got = rtc_reader.read(img, db)
        r = {"file": os.path.basename(img), "survey": got["survey"] == str(lab["survey"]),
             "hissa": got["hissa"] == str(lab["hissa"]).strip("*") or (got["hissa"] in (None, "*") and lab["hissa"] in ("*", None)),
             "tier2": got["needs_tier2"]}
        if "vlg" in lab:  # real Bhoomi label
            top = (got["candidates"] or [{}])[0]
            r["located"] = all(top.get(k) == lab[k] for k in ("dist", "taluk", "hobli", "vlg"))
            r["in_top5"] = any(all(c.get(k) == lab[k] for k in ("dist", "taluk", "hobli", "vlg")) for c in got["candidates"] or [])
        else:  # synthetic label
            want = {m["mr"] for m in lab["mutations"]}
            have = {m["mr"] for m in got["mutations"]}
            r["mr_recall"] = len(want & have) / len(want) if want else 1.0
            r["inheritance"] = got["inheritance_before"] == any(m["type"] == "ಪೌತಿ" for m in lab["mutations"])
        rows.append(r)
    n = len(rows)
    keys = [k for k in rows[0] if k != "file"]
    summary = {k: round(sum(float(r[k]) for r in rows) / n, 3) for k in keys}
    summary.update(n=n, secs_per_rtc=round((time.time() - t0) / n, 2))
    print(json.dumps(summary))
    return rows, summary


if __name__ == "__main__":
    rows, _ = main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    for r in rows:
        if not all(v for k, v in r.items() if k not in ("file", "tier2", "mr_recall")):
            print("miss", r)
