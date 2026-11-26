"""RTC reader, tier 1: free and local. Tesseract (kan+eng) + fixed rules for Karnataka's RTC layout.

Cost cascade (same idea as the author's InfrX mortgage pipeline):
  tier 0  family gives the survey number by voice -> Bhoomi lookup, no OCR at all
  tier 1  this file: Tesseract + rules, ~3 s, Rs 0
  tier 2  Sarvam Vision, only when tier 1 cannot locate the record (Rs ~0.5/page)
The photo's job is to LOCATE the record (taluk, hobli, village, survey, hissa) and read history
(col 10 MR entries) and liabilities (col 11). Owners come from Bhoomi, not from OCR.

Needs: tesseract on PATH, kan + eng traineddata (TESSDATA_PREFIX).
"""
import difflib
import os
import re
import sqlite3
import subprocess
import sys
import tempfile

MR = re.compile(r"MR\s*([A-Z]{1,2}\d+\s*/\s*\d{4}\s*-\s*\d{4})")
DATE = re.compile(r"\d{2}/\d{2}/\d{4}")
EXTENT = re.compile(r"\b\d{1,3}\.\d{2}\.\d{2}\.\d{2}")
MUT_TYPES = {"ಪೌತಿ": "inheritance", "ಕ್ರಯ": "sale", "ವಿಭಜನೆ": "partition", "ವಿಭಾಗ": "partition", "ದಾನ": "gift",
             "ಹಕ್ಕು": "rights", "ಭೂಸ್ವಾಧೀನ": "acquisition"}
LIABILITY = ["ಸಾಲ", "ಬ್ಯಾಂಕ್", "ಪ್ರಾ.ಕೃ", "ಸ.ಸಂ", "ಬೋಜಾ", "ತಡೆ", "ನ್ಯಾಯಾಲಯ", "ಅಡಮಾನ"]

# Kannada -> rough Latin, only to fuzzy-match against the survey index's English village names.
V = {"ಅ": "a", "ಆ": "a", "ಇ": "i", "ಈ": "i", "ಉ": "u", "ಊ": "u", "ಋ": "ru", "ಎ": "e", "ಏ": "e", "ಐ": "ai", "ಒ": "o", "ಓ": "o", "ಔ": "au"}
S = {"ಾ": "a", "ಿ": "i", "ೀ": "i", "ು": "u", "ೂ": "u", "ೃ": "ru", "ೆ": "e", "ೇ": "e", "ೈ": "ai", "ೊ": "o", "ೋ": "o", "ೌ": "au"}
C = dict(zip("ಕಖಗಘಙಚಛಜಝಞಟಠಡಢಣತಥದಧನಪಫಬಭಮಯರಲವಶಷಸಹಳ",
             "k kh g gh n ch chh j jh n t th d dh n t th d dh n p ph b bh m y r l v sh sh s h l".split()))


def latin(s):
    out, i = [], 0
    for ch in s:
        if ch in C:
            out.append(C[ch] + "a")
        elif ch in S and out:
            out[-1] = out[-1][:-1] + S[ch]
        elif ch == "್" and out:
            out[-1] = out[-1][:-1]
        elif ch in V:
            out.append(V[ch])
        elif ch in "ಂ":
            out.append("n")
        elif ch.isascii() and ch.isalnum():
            out.append(ch.lower())
    return "".join(out)


def _prep(path, min_width=2400):
    """Phone photos are small: enlarge to ~2400 px wide, greyscale, autocontrast (MR recall 0.35 -> 0.55 on
    the synthetic set; sharpening and binarising did not help). Needs Pillow; without it, OCR the original."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return path, None
    im = Image.open(path)
    if im.width >= min_width:
        return path, None
    im = ImageOps.autocontrast(ImageOps.grayscale(im).resize((min_width, int(im.height * min_width / im.width)), Image.LANCZOS), cutoff=1)
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=os.path.dirname(os.path.abspath(path)))
    im.save(tmp.name)
    return tmp.name, tmp.name


def squash(s):
    """Spelling-insensitive key: 'TAGGEEKUPPE' and 'tagikuppe' -> 'tagikupe'."""
    s = s.lower()
    for a, b in (("ee", "i"), ("oo", "u"), ("aa", "a"), ("w", "v"), ("th", "t"), ("dh", "d"), ("sh", "s"),
                 ("kh", "k"), ("gh", "g"), ("bh", "b"), ("ph", "p"), ("chh", "c"), ("ch", "c"), ("z", "j")):
        s = s.replace(a, b)
    return re.sub(r"(.)\1+", r"\1", re.sub(r"[^a-z]", "", s))


def ocr(path):
    """Tesseract TSV -> list of words with boxes."""
    src, tmp = _prep(path)
    try:
        tsv = subprocess.run(["tesseract", src, "-", "-l", "kan+eng", "--psm", "11", "tsv"],
                             capture_output=True, text=True, check=True).stdout
    finally:
        if tmp:
            os.remove(tmp)
    words = []
    for line in tsv.splitlines()[1:]:
        f = line.split("\t")
        t = f[11].replace("\u200c", "").replace("\u200d", "").strip() if len(f) == 12 else ""
        if t and float(f[10]) > 0:
            words.append({"t": t, "x": int(f[6]), "y": int(f[7]), "w": int(f[8]), "h": int(f[9]), "conf": float(f[10])})
    return words


LABELS = ("ತಾಲ್ಲೂಕು", "ತಾಲೂಕು", "ಹೋಬಳಿ", "ಗ್ರಾಮ", "ಮೊಹರು", "ನಮೂನೆ", "ಸಂಖ್ಯೆ", "ಪುಟದ", "ಕ್ರಮ", "ಹೆಸರು", "ತಂದೆಯ",
          "ವಿಸ್ತೀರ್ಣ", "ಖಾತೆ", "ಕಂದಾಯ", "ಸರ್ವೆ", "ಹಿಸ್ಸಾ", "ಖೇತವಾರು", "ಕಬ್ಜೆ", "ಕಟ್ಟೆ", "ಸ್ವಾಧೀನ")
KN_WORD = re.compile(r"^[\u0C80-\u0CFF]{3,}$")


def _after(words, label, band=None):
    """Nearest Kannada word to the right of a label on the same line, e.g. 'ಗ್ರಾಮ:' -> 'ದೊಡ್ಡಮಸ್ಕಲ್'.
    Skips label words, so 'ತಾಲ್ಲೂಕು ಮೊಹರು' (the seal) and 'ಗ್ರಾಮ ನಮೂನೆ ೨' (form name) are passed over."""
    for w in words:
        if not w["t"].rstrip(":.").startswith(label) or (band and w["y"] > band):
            continue
        cy = w["y"] + w["h"] / 2  # values print in a bigger font than labels: compare box centres
        right = sorted((v for v in words if abs(v["y"] + v["h"] / 2 - cy) < 1.5 * w["h"] and 0 < v["x"] - w["x"] < 15 * w["h"]),
                       key=lambda v: v["x"])
        for v in right[:3]:
            t = v["t"].strip(":.|,")
            if any(t.startswith(k) for k in LABELS):
                break  # next label on the line: this occurrence has no value
            if KN_WORD.match(t):
                return t
    return None


def _right(words, label, pat):
    """First token matching pat to the right of label on the same line (hissa: '2. ಹಿಸ್ಸಾ  4A2')."""
    for w in words:
        if w["t"].startswith(label):
            cy = w["y"] + w["h"] / 2
            for v in sorted((v for v in words if abs(v["y"] + v["h"] / 2 - cy) < 1.5 * w["h"] and 0 < v["x"] - w["x"] < 8 * w["h"]),
                            key=lambda v: v["x"]):
                t = v["t"].strip("*:.|,")
                if re.match(pat, t):
                    return t
    return None


def _below(words, label, pat=r"^\d{1,4}$", dy=6):
    """First matching word under a column label (survey number under 'ಸರ್ವೆ', hissa after 'ಹಿಸ್ಸಾ')."""
    for w in words:
        if w["t"].startswith(label):
            cands = [v for v in words if re.match(pat, v["t"].strip("*:.|")) and v["y"] > w["y"] + 0.5 * w["h"]
                     and v["y"] < w["y"] + dy * w["h"] and abs(v["x"] - w["x"]) < 6 * w["h"]]
            if cands:
                return min(cands, key=lambda v: (v["y"] - w["y"]) ** 2 + (v["x"] - w["x"]) ** 2)["t"].strip("*:.|")
    return None


HISSA = r"^\d{1,3}[A-Za-z0-9/*]{0,4}$|^\*$"


def parse(words):
    text = " ".join(w["t"] for w in words)
    band = 0.12 * max((w["y"] + w["h"] for w in words), default=0)  # header lines: taluk, hobli, village
    muts = []
    for i, w in enumerate(words):  # 'MR' 'T1/2012-2013' then, on the line below, '17/09/2012' 'ವಿಭಜನೆ'
        nxt = words[i + 1]["t"] if i + 1 < len(words) else ""
        m = MR.match(w["t"] + " " + nxt) if w["t"] == "MR" else MR.match(w["t"])
        if not m:
            continue
        near = [v for v in words if 0 < v["y"] - w["y"] < 2.5 * w["h"] and -2 * w["h"] < v["x"] - w["x"] < 14 * w["h"]]
        d = next((v["t"] for v in sorted(near, key=lambda v: v["x"]) if DATE.match(v["t"])), None)
        kind = next((MUT_TYPES[k] for v in near for k in MUT_TYPES if v["t"].startswith(k)), None)
        muts.append({"mr": "MR " + re.sub(r"\s", "", m.group(1)), "date": d, "type": kind})
    owners_hint = [w["t"] for w in words if w["t"] in ("ಬಿನ್", "ಕೋಂ")]
    return {
        "taluk": _after(words, "ತಾಲ್ಲೂಕು", band) or _after(words, "ತಾಲೂಕು", band),
        "hobli": _after(words, "ಹೋಬಳಿ", band),
        "village": _after(words, "ಗ್ರಾಮ", band),
        "survey": _below(words, "ಸರ್ವೆ"),
        "hissa": _right(words, "ಹಿಸ್ಸಾ", HISSA) or _below(words, "ಹಿಸ್ಸಾ", pat=HISSA, dy=2),
        "mutations": muts,
        "inheritance_before": any(m["type"] == "inheritance" for m in muts),
        "late_marker": "ಲೇ" in text.split(),  # 'ಬಿನ್ ಲೇ X' = son of the late X
        "relation_words": len(owners_hint),
        "extents": EXTENT.findall(text),
        "liability_words": sorted({k for k in LIABILITY if k in text}),
    }


def locate(fields, db):
    """Fuzzy-match OCR'd taluk/hobli/village (Kannada) to survey-index codes (English names)."""
    if not fields.get("village"):
        return None
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    names = [r[0] for r in con.execute("select distinct village_name from survey_index where village_name <> ''")]
    keys = {}
    for n in names:
        keys.setdefault(squash(n), []).append(n)
    close = difflib.get_close_matches(squash(latin(fields["village"])), list(keys), n=25, cutoff=0.6)
    best = [n for k in close for n in keys[k]]
    if not best:
        return None
    q = (f"select distinct village_name, dist, taluk, hobli, vlg from survey_index where village_name in "
         f"({','.join('?' * len(best))})")
    args = list(best)
    if fields.get("survey"):  # the survey number must exist in that village: removes most look-alikes
        q += " and survey_no_norm = ?"
        args.append(fields["survey"])
    rows = con.execute(q, args).fetchall()
    rank = {n: i for i, n in enumerate(best)}
    rows.sort(key=lambda r: rank[r[0]])
    return [{"village": r[0], "dist": r[1], "taluk": r[2], "hobli": r[3], "vlg": r[4]} for r in rows][:5]


def _line_after(path, words, label, scale):
    """Second pass for a header value the full-page OCR skipped: crop the strip right of the label and
    OCR it as one line (--psm 7). On real Bhoomi RTCs the village name is often missed by the first pass."""
    try:
        from PIL import Image
    except ImportError:
        return None
    lab = next((w for w in words if w["t"].rstrip(":.").startswith(label) and w["t"].endswith(":")), None) \
        or next((w for w in words if w["t"].rstrip(":.").startswith(label)), None)
    if not lab:
        return None
    s = 1 / scale
    # Crop whole lines around the label (cutting through the title above confuses Tesseract), label included
    # as an anchor, block mode (--psm 6). Two sizes, tuned on real Bhoomi RTCs.
    im = Image.open(path)
    for up, down, right in ((3, 2, 30), (3.5, 3, 40)):
        box = (int((lab["x"] - 30) * s), int((lab["y"] - up * lab["h"]) * s),
               int((lab["x"] + right * lab["h"]) * s), int((lab["y"] + down * lab["h"]) * s))
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir=os.path.dirname(os.path.abspath(path)))
        try:
            im.crop(box).save(tmp.name)
            out = subprocess.run(["tesseract", tmp.name, "-", "-l", "kan", "--psm", "6"], capture_output=True, text=True).stdout
        finally:
            os.remove(tmp.name)
        toks = [t.strip(":.|,") for t in out.replace("\u200c", "").replace("\u200d", "").split()]
        for i, t in enumerate(toks):
            if t.startswith(label):
                for v in toks[i + 1:i + 3]:
                    v = re.sub(r"[^\u0C80-\u0CE5\u0CF0-\u0CFF]", "", v)  # drop '__', Kannada digits like '೦'
                    if KN_WORD.match(v) and not any(v.startswith(k) for k in LABELS):
                        return v
    return None


def read(path, db=None):
    words = ocr(path)
    f = parse(words)
    scale = 1.0
    try:
        from PIL import Image
        w = Image.open(path).width
        scale = max(w, 2400) / w
    except ImportError:
        pass
    for key, label in (("village", "ಗ್ರಾಮ"), ("hobli", "ಹೋಬಳಿ"), ("taluk", "ತಾಲ್ಲೂಕು")):
        if not f[key]:
            f[key] = _line_after(path, [w for w in words if w["y"] < 0.12 * max(v["y"] + v["h"] for v in words)], label, scale)
    f["candidates"] = locate(f, db) if db else None
    f["tier"] = 1
    f["needs_tier2"] = not (f["village"] and f["survey"])
    return f


if __name__ == "__main__":
    assert latin("ದೊಡ್ಡಮಸ್ಕಲ್") == "doddamaskal", latin("ದೊಡ್ಡಮಸ್ಕಲ್")
    assert latin("ಕನಕಪುರ") == "kanakapura"
    assert squash(latin("ತಗೀಕುಪ್ಪೆ")) == squash("TAGGEEKUPPE"), (squash(latin("ತಗೀಕುಪ್ಪೆ")), squash("TAGGEEKUPPE"))
    import json
    print(json.dumps(read(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None), ensure_ascii=False, indent=1))
