"""The family's pack for a pouthi (inheritance) transfer, as one printable HTML/PDF, Kannada with English.

Sections: land and current owners, family tree drawing, affidavit DRAFT for the family tree certificate,
heirs and shares (from heirs.py: code decides), blockers (from blockers.py), document checklist,
Aadhaar OTP-day list, and a separate consent page for any daughter giving up her share.

case = {
  "deceased": {"name", "sex": "M"|"F", "date_of_death"}, "religion", "will", "ancestral", "dispute",
  "spouse": name|None, "mother": name|None, "children": [person], "applicant": name,
  "relinquish": [names of heirs giving up their share],
  "land": {"village", "taluk", "hobli", "survey", "hissa", "owners": [...]},   (from bhoomi.py)
  "blockers": [...]                                                        (from blockers.py)
}
person = {"name", "sex", "alive", "spouse": name|None, "children": [person]}
"""
import html
import os
import subprocess
import tempfile

import heirs as heirs_engine

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
REL_KN = {"son": "ಮಗ", "daughter": "ಮಗಳು", "widow": "ಪತ್ನಿ", "husband": "ಪತಿ", "mother": "ತಾಯಿ"}
STATUS_KN = {"red": "ತಡೆ", "amber": "ಗಮನಿಸಿ", "green": "ಸರಿ", "unknown": "ಗೊತ್ತಿಲ್ಲ"}
e = html.escape


def heirs_for(case):
    c = {k: case.get(k) for k in ("religion", "will", "ancestral", "dispute", "spouse", "mother")}
    c.update(sex=case["deceased"]["sex"], children=case.get("children", []))
    c["religion"] = c["religion"] or "hindu"
    return heirs_engine.heirs(c)


def _rel_kn(rel):
    # "daughter of predeceased son" -> "ಮೃತ ಮಗನ ಮಗಳು"
    parts = rel.split(" of predeceased ")
    out = REL_KN.get(parts[0], parts[0])
    for p in parts[1:]:
        out = f"ಮೃತ {REL_KN.get(p, p)}ನ {out}" if p == "son" else f"ಮೃತ {REL_KN.get(p, p)}ಳ {out}"
    return out


# ---------- family tree drawing (SVG) ----------
BW, BH, GX, GY = 150, 46, 18, 80


def _leaves(p):
    kids = p.get("children", [])
    return max(1, sum(_leaves(k) for k in kids))


def _draw(p, x0, y, out, spouse=None):
    w = _leaves(p) * (BW + GX)
    cx = x0 + w / 2
    dead = not p.get("alive", True)
    label = e(p["name"]) + (" (ಮೃತ)" if dead else "")
    out.append(f'<rect x="{cx - BW / 2}" y="{y}" width="{BW}" height="{BH}" rx="6" fill="{"#eee" if dead else "#fff"}" '
               f'stroke="#333" stroke-dasharray="{"4 3" if dead else "0"}"/>'
               f'<text x="{cx}" y="{y + 28}" text-anchor="middle" font-size="14">{label}</text>')
    if spouse:
        out.append(f'<text x="{cx}" y="{y + BH + 16}" text-anchor="middle" font-size="12" fill="#555">+ {e(spouse)}</text>')
    x = x0
    for k in p.get("children", []):
        kw = _leaves(k) * (BW + GX)
        kx = x + kw / 2
        out.append(f'<path d="M{cx} {y + BH} V{y + BH + GY / 2 - 6} H{kx} V{y + GY + BH}" fill="none" stroke="#333"/>')
        _draw(k, x, y + GY + BH, out, k.get("spouse"))
        x += kw


def family_tree_svg(case):
    d = case["deceased"]
    root = {"name": d["name"], "alive": False, "children": case.get("children", [])}
    depth = lambda p: 1 + max((depth(k) for k in p.get("children", [])), default=0)  # noqa: E731
    out = []
    _draw(root, 0, 10, out, case.get("spouse"))
    w, h = _leaves(root) * (BW + GX), depth(root) * (BH + GY) + 20
    mother = f'<text x="4" y="{h - 4}" font-size="12" fill="#555">ತಾಯಿ / Mother: {e(case["mother"])}</text>' if case.get("mother") else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{"".join(out)}{mother}</svg>'


# ---------- the pack ----------
def _members(case):
    """Everyone the family tree certificate must list: living and dead, daughters included."""
    rows = []
    if case.get("spouse"):
        rows.append((case["spouse"], "ಪತ್ನಿ / spouse" if case["deceased"]["sex"] == "M" else "ಪತಿ / husband", True))
    if case.get("mother"):
        rows.append((case["mother"], "ತಾಯಿ / mother", True))

    def walk(p, prefix):
        rel = ("ಮಗ / son" if p["sex"] == "M" else "ಮಗಳು / daughter") if not prefix else \
              f'{prefix} → {"ಮಗ / son" if p["sex"] == "M" else "ಮಗಳು / daughter"}'
        rows.append((p["name"], rel, p["alive"]))
        if not p["alive"] and p.get("spouse") and p["sex"] == "M":
            rows.append((p["spouse"], f"{p['name']} ಅವರ ಪತ್ನಿ / widow of {p['name']}", True))
        for k in p.get("children", []):
            walk(k, p["name"])
    for c in case.get("children", []):
        walk(c, "")
    return rows


def render(case):
    d, land = case["deceased"], case.get("land", {})
    try:
        hs, review = heirs_for(case), None
    except heirs_engine.NeedsReview as ex:
        hs, review = [], str(ex)
    members = _members(case)
    owners = "".join(f"<li>{e(o['name'])} — {e(o.get('extent', ''))}"
                     f"{' · ನ್ಯಾಯಾಲಯ ತಡೆ / court stay' if o.get('court_stay') == 'Yes' else ''}</li>" for o in land.get("owners", []))
    share_rows = "".join(f"<tr><td>{e(h['name'])}</td><td>{e(_rel_kn(h['relation']))}<br><small>{e(h['relation'])}</small></td>"
                         f"<td><b>{h['share']}</b></td><td>{float(h['share']) * 100:.1f}%</td></tr>" for h in hs)
    block_rows = "".join(f"<tr><td>{STATUS_KN.get(b['status'], b['status'])} / {e(b['status'])}</td><td>{e(b['check'])}</td>"
                         f"<td>{e(b['detail'])}</td><td>{e(b.get('action', ''))}</td></tr>" for b in case.get("blockers", []))
    member_rows = "".join(f"<tr><td>{i}</td><td>{e(n)}</td><td>{e(r)}</td><td>{'ಜೀವಂತ / living' if a else 'ಮೃತ / deceased'}</td></tr>"
                          for i, (n, r, a) in enumerate(members, 1))
    otp_rows = "".join(f"<tr><td>{e(h['name'])}</td><td>☐</td><td>☐</td><td>☐</td></tr>" for h in hs)
    relinq = [h for h in hs if h["name"] in case.get("relinquish", [])]
    consent = "".join(f"""<section class=page><h2>ಪಾಲು ಬಿಟ್ಟುಕೊಡುವ ಒಪ್ಪಿಗೆ — ಪ್ರತ್ಯೇಕವಾಗಿ / Consent to give up a share — taken separately</h2>
<p>{e(h['name'])} ({e(_rel_kn(h['relation']))}) ಅವರ ಕಾನೂನು ಪಾಲು <b>{h['share']}</b>.
ಈ ಪಾಲನ್ನು ಬಿಟ್ಟುಕೊಡುವ ನಿರ್ಧಾರವನ್ನು ಅವರು <b>ಕುಟುಂಬದ ಇತರರು ಇಲ್ಲದೆ</b> ಸ್ವತಃ ದೃಢೀಕರಿಸಬೇಕು.</p>
<p><small>Her legal share is {h['share']}. She confirms this herself, in a separate call or visit, without other family members present.
Nobody can give up her share on her behalf.</small></p>
<p>ದೃಢೀಕರಣದ ದಿನಾಂಕ / Date confirmed: ________ &nbsp; ವಿಧಾನ / How (call/visit): ________ &nbsp; ಸಹಿ / Signature: ________</p></section>"""
                      for h in relinq if h["relation"].startswith("daughter"))
    review_html = f'<p class=warn>ಈ ಪ್ರಕರಣವನ್ನು ಕಂದಾಯ ಕಚೇರಿ ಪರಿಶೀಲಿಸಬೇಕು / Revenue office must review: {e(review)}</p>' if review else ""
    return f"""<!doctype html><html lang=kn><meta charset=utf-8><title>Pauti Mitra — {e(d['name'])}</title><style>
body{{font:14px 'Kannada Sangam MN','Noto Sans Kannada',sans-serif;margin:24px;color:#111}} h1{{font-size:22px}} h2{{font-size:17px;border-bottom:2px solid #333;padding-bottom:4px}}
table{{border-collapse:collapse;width:100%;margin:8px 0}} td,th{{border:1px solid #999;padding:6px;text-align:left;vertical-align:top}} th{{background:#f2f2f2}}
.page{{page-break-before:always}} .warn{{background:#fff3cd;border:1px solid #c90;padding:8px}} small{{color:#555}} .draft{{color:#a00;font-weight:bold}}
</style>
<h1>ಪೌತಿ ಖಾತೆ ಸಿದ್ಧತೆ ಪತ್ರ / Pauti Khate preparation pack</h1>
<p>ಮೃತರು / Deceased: <b>{e(d['name'])}</b> · ಮರಣ ದಿನಾಂಕ / Date of death: {e(d.get('date_of_death') or '________')}<br>
ಜಮೀನು / Land: {e(land.get('village', ''))}, {e(land.get('place', ''))} ·
ಸರ್ವೆ / Survey {e(str(land.get('survey', '')))} · ಹಿಸ್ಸಾ / Hissa {e(str(land.get('hissa', '')))}</p>
<p>ಈಗಿನ ಆರ್‌ಟಿಸಿ ಮಾಲೀಕರು (ಭೂಮಿ) / Current RTC owners (Bhoomi, live):</p><ul>{owners or '<li>—</li>'}</ul>
{review_html}{'<p class=warn>ಮೃತರ ಹೆಸರು ಈ ಆರ್‌ಟಿಸಿಯಲ್ಲಿ ಇಲ್ಲ / The deceased is not among these RTC owners: check the survey/hissa, or do the earlier pouthi first.</p>' if land.get('deceased_on_rtc') is False else ''}

<h2>1. ವಾರಸುದಾರರು ಮತ್ತು ಪಾಲು / Heirs and shares</h2>
<p><small>Worked out by tested rules (Hindu Succession Act, as amended 2005; daughters equal). Every heir goes on the RTC jointly first;
dividing the land (partition, 11E sketch, podi) is a separate later step.</small></p>
<table><tr><th>ಹೆಸರು / Name</th><th>ಸಂಬಂಧ / Relation</th><th>ಪಾಲು / Share</th><th></th></tr>{share_rows}</table>

<h2>2. ತಡೆಗಳು / Blockers on this land</h2>
<table><tr><th>ಸ್ಥಿತಿ</th><th>Check</th><th>Detail</th><th>What to do</th></tr>{block_rows or '<tr><td colspan=4>—</td></tr>'}</table>

<h2>3. ದಾಖಲೆಗಳ ಪಟ್ಟಿ / Document checklist</h2>
<ul><li>☐ ಮರಣ ಪ್ರಮಾಣ ಪತ್ರ / Death certificate of {e(d['name'])}</li>
<li>☐ ವಂಶವೃಕ್ಷ ಪ್ರಮಾಣ ಪತ್ರ / Family tree certificate (Nadakacheri or Seva Sindhu; ~14 days): use the drawing and affidavit draft below</li>
<li>☐ ಈಗಿನ ಆರ್‌ಟಿಸಿ ಪ್ರತಿ / Current RTC copy</li>
<li>☐ ಪ್ರತಿ ವಾರಸುದಾರರ ಆಧಾರ್ / Aadhaar of every heir listed above</li></ul>

<h2>4. ಆಧಾರ್ OTP ದಿನದ ಪಟ್ಟಿ / Aadhaar OTP-day list</h2>
<p><small>The village officer's app sends OTPs to each heir (government OTP, then Aadhaar eKYC OTP, then a final OTP).
Every heir needs a working mobile linked to their Aadhaar, and must be reachable on the visit day.</small></p>
<table><tr><th>ವಾರಸುದಾರ / Heir</th><th>ಆಧಾರ್‌ಗೆ ಮೊಬೈಲ್ ಲಿಂಕ್ / Mobile linked to Aadhaar</th><th>ಭೇಟಿ ದಿನ ಲಭ್ಯ / Reachable on visit day</th><th>OTP ಪೂರ್ಣ / OTPs done</th></tr>{otp_rows}</table>

<section class=page><h2>5. ವಂಶವೃಕ್ಷ / Family tree</h2>{family_tree_svg(case)}
<p><small>Dashed box = deceased. This drawing goes with the family tree certificate application.</small></p></section>

<section class=page><h2>6. ವಂಶವೃಕ್ಷ ಪ್ರಮಾಣ ಪತ್ರಕ್ಕೆ ಪ್ರಮಾಣ ಪತ್ರ — <span class=draft>ಕರಡು / DRAFT</span></h2>
<p class=draft>ಇದು ಕರಡು ಮಾತ್ರ. ನಾಡಕಚೇರಿ ಅಥವಾ ನೋಟರಿ ಅಂತಿಮಗೊಳಿಸಬೇಕು. / Draft only: the Nadakacheri or a notary must finalise the wording and stamp paper.</p>
<p>ನಾನು, {e(case.get('applicant') or '________')}, ದಿವಂಗತ {e(d['name'])} ಅವರ ಕುಟುಂಬದ ಸದಸ್ಯರ ವಿವರಗಳು ಈ ಕೆಳಗಿನಂತಿವೆ ಎಂದು ತಿಳಿಸುತ್ತೇನೆ.
ಯಾವುದೇ ಸದಸ್ಯರನ್ನು (ವಿವಾಹಿತ ಹೆಣ್ಣುಮಕ್ಕಳು ಸೇರಿದಂತೆ) ಬಿಟ್ಟಿಲ್ಲ.</p>
<p><small>I, {e(case.get('applicant') or '________')}, state that the members of the family of the late {e(d['name'])} are as below.
No member has been left out, including married daughters.</small></p>
<table><tr><th>#</th><th>ಹೆಸರು / Name</th><th>ಸಂಬಂಧ / Relation</th><th>ಸ್ಥಿತಿ / Status</th></tr>{member_rows}</table>
<p>ಸ್ಥಳ / Place: ________ &nbsp; ದಿನಾಂಕ / Date: ________ &nbsp; ಸಹಿ / Signature: ________</p></section>
{consent}
</html>"""


def write(case, out_path):
    """Write the pack as HTML, and as PDF too when out_path ends in .pdf (needs Chrome)."""
    page = render(case)
    if not out_path.endswith(".pdf"):
        open(out_path, "w", encoding="utf-8").write(page)
        return out_path
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as t:
        t.write(page)
    try:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={os.path.abspath(out_path)}", "file://" + t.name],
                       check=True, capture_output=True, timeout=90)
    finally:
        os.remove(t.name)
    return out_path


if __name__ == "__main__":
    P = lambda name, sex, alive=True, spouse=None, children=(): {"name": name, "sex": sex, "alive": alive, "spouse": spouse, "children": list(children)}  # noqa: E731
    demo = {"deceased": {"name": "ರಾಮಪ್ಪ", "sex": "M", "date_of_death": "12/03/2024"}, "applicant": "ರವಿ",
            "spouse": "ಲಕ್ಷ್ಮಮ್ಮ", "mother": None, "relinquish": ["ಕಾವ್ಯ"],
            "children": [P("ರವಿ", "M"), P("ಕಾವ್ಯ", "F"), P("ಮೋಹನ", "M", alive=False, spouse="ಶಾಂತ", children=[P("ಅರುಣ್", "M"), P("ದಿವ್ಯ", "F")])],
            "land": {"village": "ದೊಡ್ಡಮಸ್ಕಲ್", "hobli": "ಮಾಡಬಾಳ್", "taluk": "ಮಾಗಡಿ", "survey": "16", "hissa": "1",
                     "owners": [{"name": "ರಾಮಪ್ಪ ಬಿನ್ ಲೇ ಚನ್ನಪ್ಪ", "extent": "2.30.0"}]},
            "blockers": [{"check": "Pending revenue court case", "status": "green", "detail": "no active case", "action": ""}]}
    page = render(demo)
    for must in ("ಕಾವ್ಯ", "1/4", "1/12", "ಕರಡು", "ವಂಶವೃಕ್ಷ", "<svg", "ಪ್ರತ್ಯೇಕವಾಗಿ"):
        assert must in page, must
    print(write(demo, os.path.expanduser("~/Documents/tech4bharat/demo-pack.pdf")))
