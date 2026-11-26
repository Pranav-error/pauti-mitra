"""Make a labelled test set of synthetic RTCs that look like phone photos.

Layout follows the real RTC in the IIHS/DoLR report (Annexure 1): 13 columns, owners in col 9,
mutation history in col 10, rights and liabilities in col 11. All names and numbers are made up.
Each image NNN.jpg comes with NNN.json (the ground truth), so the RTC reader can be scored.

Run: .venv/bin/python tools/make_rtcs.py OUT_DIR [N]   (needs Google Chrome and Pillow)
"""
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MALE = "ರಾಮಪ್ಪ ಕರಿಯಪ್ಪ ಮುನಿಯಪ್ಪ ಚನ್ನಪ್ಪ ಬಸವರಾಜು ನಾಗರಾಜು ವೆಂಕಟೇಶ ಹನುಮಂತಪ್ಪ ಶಿವಣ್ಣ ಮಂಜುನಾಥ ಕೃಷ್ಣಪ್ಪ ಸಿದ್ದಪ್ಪ ಗೋವಿಂದಪ್ಪ ರಂಗಪ್ಪ ಮರಿಶೆಟ್ಟಿ".split()
FEMALE = "ಲಕ್ಷ್ಮಮ್ಮ ಗೌರಮ್ಮ ಸಾವಿತ್ರಮ್ಮ ಮುನಿಯಮ್ಮ ಸರೋಜಮ್ಮ ನಾಗಮ್ಮ ಪಾರ್ವತಮ್ಮ ಕಮಲಮ್ಮ ಜಯಮ್ಮ ಸುಶೀಲಮ್ಮ".split()
PLACES = [("ಕನಕಪುರ", "ಉಯ್ಯಂಬಳ್ಳಿ"), ("ಮಾಗಡಿ", "ಸೋಲೂರು"), ("ಕೋಲಾರ", "ಕಸಬಾ"), ("ಮುಳಬಾಗಿಲು", "ಆವಣಿ"), ("ಹೊಸಕೋಟೆ", "ಜಡಿಗೇನಹಳ್ಳಿ")]
VILLAGES = "ದೊಡ್ಡಕೊಪ್ಪ ಹುಲಿಕೆರೆ ಬೇವೂರು ಕೆಂಪನಹಳ್ಳಿ ಮಲ್ಲಸಂದ ಗೊಲ್ಲಹಳ್ಳಿ ಕಲ್ಲಹಳ್ಳಿ ಹೊಸೂರು".split()
MUT_TYPES = ["ಪೌತಿ", "ಕ್ರಯ", "ವಿಭಾಗ", "ದಾನ", "ಪೌತಿ"]  # inheritance twice: it's what we care about
CROPS = ["ರಾಗಿ (ಮು)", "ಭತ್ತ (ಮು)", "ಜೋಳ (ಮು)", "ತೆಂಗು", "No Crop Info."]
LIABILITIES = ["ಕೃಷಿ ಸಾಲ ರೂ. {n},000 ಪ್ರಾ.ಕೃ.ಪ.ಸ.ಸಂಘ", "ಬೆಳೆ ಸಾಲ ರೂ. {n},000 ಕೆನರಾ ಬ್ಯಾಂಕ್", "ನ್ಯಾಯಾಲಯ ತಡೆಯಾಜ್ಞೆ ಓ.ಎಸ್ {n}/2023"]


def ext(guntas):
    return f"{guntas // 40}.{guntas % 40:02d}.00.00"  # acre.gunta.anna.paisa; 40 guntas = 1 acre


def make_case(rng):
    taluk, hobli = rng.choice(PLACES)
    total = rng.randint(20, 400)  # guntas
    n = rng.choice([1, 1, 2, 2, 3, 4])
    cuts = sorted(rng.sample(range(1, total), n - 1)) if n > 1 else []
    parts = [b - a for a, b in zip([0] + cuts, cuts + [total])]
    father = rng.choice(MALE)
    late = rng.random() < 0.6  # "ಬಿನ್ ಲೇ" = son of the late ...
    owners = []
    for i, g in enumerate(parts):
        wife = i == 0 and n > 1 and rng.random() < 0.3
        name = rng.choice(FEMALE if wife else MALE)
        rel = f"ಕೋಂ {'ಲೇ ' if late else ''}{father}" if wife else f"ಬಿನ್ {'ಲೇ ' if late else ''}{father}"
        owners.append({"name": name, "relation": rel, "text": f"{name} {rel}", "extent": ext(g),
                       "khata": rng.randint(1, 400)})
    muts = []
    for o in owners:
        y = rng.randint(1998, 2025)
        muts.append({"mr": f"MR {rng.choice('HTKP')}{rng.randint(1, 60)}/{y}-{y + 1}",
                     "date": f"{rng.randint(1, 28):02d}/{rng.randint(1, 12):02d}/{y}", "type": rng.choice(MUT_TYPES)})
    liab = [rng.choice(LIABILITIES).format(n=rng.randint(10, 300))] if rng.random() < 0.35 else []
    return {"survey": str(rng.randint(1, 450)), "hissa": rng.choice(["*", "1", "2", "3", "1ಎ"]),
            "village": rng.choice(VILLAGES), "taluk": taluk, "hobli": hobli, "total_extent": ext(total),
            "owners": owners, "mutations": muts, "liabilities": liab, "crop": rng.choice(CROPS),
            "watermark": rng.random() < 0.5}


def html(c, rng):
    rows9 = "".join(f"<div class=r>{o['text']}</div>" for o in c["owners"])
    ext9 = "".join(f"<div class=r>{o['extent']}</div>" for o in c["owners"])
    kh9 = "".join(f"<div class=r>{o['khata']}</div>" for o in c["owners"])
    m10 = "".join(f"<div class=r>{m['mr']}<br>{m['date']} {m['type']}</div>" for m in c["mutations"])
    l11 = "".join(f"<div class=r>{x}</div>" for x in c["liabilities"])
    cult = "".join(f"<div class=r>{o['text']}</div>" for o in c["owners"])
    wm = '<div class=wm>For Viewing Only &nbsp;&nbsp;&nbsp; For Viewing Only</div>' if c["watermark"] else ""
    return f"""<!doctype html><meta charset=utf-8><style>
body{{margin:0;width:1700px;font:19px 'Kannada Sangam MN','Kannada MN',sans-serif;background:#fff;position:relative}}
table{{border-collapse:collapse;width:1680px;margin:6px 10px}} td,th{{border:1.5px solid #222;vertical-align:top;padding:4px}}
th{{font-weight:normal;font-size:14px}} .r{{min-height:44px}} .h{{text-align:center;font-size:22px;margin-top:8px}}
.wm{{position:absolute;top:560px;left:120px;font:64px Arial;color:rgba(120,120,120,.35);white-space:nowrap}}</style>
<div class=h>ರೆಕಾರ್ಡ್ ಆಫ್ ರೈಟ್ಸ್, ಗೇಣಿ ಮತ್ತು ಪಹಣಿ ಪತ್ರಿಕೆ (R.T.C) ಫಾರಂ ನಂ. 16 <small>Village Account Form No. 2</small></div>
<div style="margin:4px 12px">ತಾಲ್ಲೂಕು: {c['taluk']} &nbsp; ಹೋಬಳಿ: {c['hobli']} &nbsp; ಗ್ರಾಮ: {c['village']}</div>
<table><tr><th style=width:7%>1. ಸರ್ವೆ ನಂಬರು</th><th style=width:14%>3. ಕ್ಷೇತ್ರವಾರು / ಒಟ್ಟು ವಿಸ್ತೀರ್ಣ</th>
<th style=width:9%>4. ಕಂದಾಯ</th><th style=width:22%>9. ಕಬ್ಜೆದಾರರ ಹೆಸರು ತಂದೆಯ ಹೆಸರು ಮತ್ತು ವಿಳಾಸ</th><th style=width:8%>ವಿಸ್ತೀರ್ಣ</th>
<th style=width:5%>ಖಾತೆ ನಂ.</th><th style=width:15%>10. ಕಬ್ಜೆ ಅಥವಾ ಸ್ವಾಧೀನತೆಯ ರೀತಿ</th><th>11. ಇತರ ಹಕ್ಕುಗಳು ಮತ್ತು ಋಣಗಳು</th></tr>
<tr style=height:360px><td>{c['survey']}<br><br>2. ಹಿಸ್ಸಾ<br>{c['hissa']}</td><td>{c['total_extent']}</td><td>{rng.uniform(0.5, 9):.2f}</td>
<td>{rows9}</td><td>{ext9}</td><td>{kh9}</td><td>{m10}</td><td>{l11}</td></tr></table>
<table><tr><th style=width:9%>12. ವರ್ಷ ಮತ್ತು ಕಾಲ</th><th style=width:30%>ವ್ಯವಸಾಯಗಾರನ ಹೆಸರು</th><th>ಸಾಗುವಳಿ ಪದ್ಧತಿ</th><th>13. ಬೆಳೆಯ ಹೆಸರು</th></tr>
<tr style=height:260px><td>2025-2026 ಮುಂಗಾರು</td><td>{cult}</td><td>ಸ್ವಂತ</td><td>{c['crop']}</td></tr></table>
<div style="margin:6px 12px;font:15px Arial">RTC DIGITALLY SIGNED BY : DS BHOOMI MONITORING CELL</div>{wm}"""


def photo(png, rng):
    """Make a clean render look like a phone photo of a printout."""
    im = Image.open(png).convert("RGB")
    im = ImageEnhance.Color(im).enhance(0.9)
    tint = Image.new("RGB", im.size, (rng.randint(235, 255), rng.randint(228, 250), rng.randint(205, 240)))
    im = Image.blend(im, tint, rng.uniform(0.05, 0.2))
    shade = Image.new("L", im.size, 0)  # one-sided shadow, like a hand or phone over the page
    d = ImageDraw.Draw(shade)
    k = rng.uniform(0, 70)
    for x in range(0, im.width, 4):
        d.rectangle([x, 0, x + 4, im.height], fill=int(k * x / im.width))
    im = Image.composite(Image.new("RGB", im.size, (40, 40, 40)), im, shade.point(lambda v: v // 3))
    w, h = im.size
    j = lambda: rng.uniform(-0.04, 0.04) * w  # noqa: E731
    im = im.transform((w, h), Image.QUAD, (j(), j(), j(), h + j(), w + j(), h + j(), w + j(), j()),
                      Image.BICUBIC, fillcolor=(90, 80, 70))
    im = im.rotate(rng.uniform(-4, 4), Image.BICUBIC, expand=True, fillcolor=(90, 80, 70))
    im = im.filter(ImageFilter.GaussianBlur(rng.uniform(0, 1.6)))
    im = ImageEnhance.Brightness(im).enhance(rng.uniform(0.75, 1.1))
    s = rng.uniform(0.55, 0.9)
    return im.resize((int(im.width * s), int(im.height * s)))


def main(out, n=60, seed=7):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(n):
            c = make_case(rng)
            page, png = Path(tmp, "p.html"), Path(tmp, "p.png")
            page.write_text(html(c, rng), encoding="utf-8")
            subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--screenshot={png}",
                            "--window-size=1700,1000", page.as_uri()], check=True, capture_output=True, timeout=60)
            photo(png, rng).save(out / f"{i:03d}.jpg", quality=rng.randint(45, 85))
            c.pop("watermark")
            (out / f"{i:03d}.json").write_text(json.dumps(c, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{n} RTCs in {out}")


if __name__ == "__main__":
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 60)
