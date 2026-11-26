"""Who owns this land right now: Bhoomi's public View RTC page (no login, no captcha).

Walks the page's ASP.NET form: district, taluk, hobli, village, survey -> surnoc, hissa -> period, year
-> "Fetch details" (owner table) -> optional "View" (rendered RTC PNG).
Codes are the survey-index / e-Chawadi codes. Reads one record at a time, 1 s between requests.
For production this should be an agreed data feed from the Revenue Department, not form-walking.
"""
import html as H
import http.cookiejar
import re
import time
import urllib.parse
import urllib.request

U = "https://landrecords.karnataka.gov.in/service2/RTC.aspx"
P = "ctl00$MainContent$"
BTN = {"btnCGo": "Go", "btnCFetchDetails": "Fetch details", "btnCPreview": "View"}


class Form:
    def __init__(self, pause=1.0):
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.op.addheaders = [("User-Agent", "Mozilla/5.0")]
        self.pause = pause
        self.s = self.op.open(U, timeout=40).read().decode("utf-8", "replace")
        self.v = {}

    def options(self, name):
        m = re.search(r'<select[^>]*name="' + re.escape(P + name) + r'"[^>]*>(.*?)</select>', self.s, re.S)
        return [(v, H.unescape(t).strip()) for v, t in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>([^<]*)', m.group(1))
                if not v.startswith("Select") and v != "0"] if m else []

    def post(self, target=None, button=None, **vals):
        self.v.update({P + k: v for k, v in vals.items()})
        hidden = {n: H.unescape(v) for n, v in re.findall(r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', self.s)}
        d = {**hidden, **self.v, "__EVENTTARGET": P + target if target else "", "__EVENTARGUMENT": ""}
        if button:
            d[P + button] = BTN[button]
        time.sleep(self.pause)
        self.s = self.op.open(U, urllib.parse.urlencode(d).encode(), timeout=60).read().decode("utf-8", "replace")


def _text(s):
    return re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def open_survey(dist, taluk, hobli, vlg, survey, pause=1.0):
    """Walk to the survey number. Returns (form, [(surnoc, [(hissa_value, hissa_label)])]) for the first surnoc."""
    f = Form(pause)
    f.post("ddlCDistrict", ddlCDistrict=dist)
    f.post("ddlCTaluk", ddlCTaluk=taluk)
    f.post("ddlCHobli", ddlCHobli=hobli)
    f.post("ddlCVillage", ddlCVillage=vlg)
    f.post(button="btnCGo", txtCSurveyNo=str(survey))
    return f


def place_name(dist, taluk, pause=1.0):
    """'District / Taluk' names for codes, from the same page (two requests). Used only to tell look-alike villages apart."""
    f = Form(pause)
    d = dict(f.options("ddlCDistrict")).get(dist, dist)
    f.post("ddlCDistrict", ddlCDistrict=dist)
    return f"{d} / {dict(f.options('ddlCTaluk')).get(taluk, taluk)}"


def hissas(f, surnoc=None):
    sur = surnoc or f.options("ddlCSurnocNo")[0][0]
    f.post("ddlCSurnocNo", ddlCSurnocNo=sur)
    return sur, f.options("ddlCHissaNo")


def owners(f, hissa_value):
    """Owner table for one hissa: [{name, extent, category, gov_restriction, court_stay, alienated}] + flags."""
    f.post("ddlCHissaNo", ddlCHissaNo=hissa_value)
    f.post("ddlCPeriod", ddlCPeriod=f.options("ddlCPeriod")[0][0])
    f.post(button="btnCFetchDetails", ddlCYear=f.options("ddlCYear")[0][0])
    grid = re.search(r'id="ctl00_MainContent_grdCurrentYearOwnerDetails1".*?</table>', f.s, re.S)
    rows = [[_text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
            for r in re.findall(r"<tr.*?</tr>", grid.group(0), re.S)] if grid else []
    keys = ["name", "extent", "category", "gov_restriction", "court_stay", "alienated"]
    t = _text(f.s)
    flag = lambda k: (re.search(k + r" : (\w+)", t) or [None, None])[1]  # noqa: E731
    return {"owners": [dict(zip(keys, r)) for r in rows if len(r) >= 6],
            "ongoing_mutation": flag("OnGoing Mutation"), "pyki": flag("PYKI"),
            "source": "Bhoomi View RTC (live)"}


def rtc_png(f):
    """After owners(): the rendered RTC as PNG bytes (transparent background)."""
    f.post(button="btnCPreview")
    prev = f.op.open(U.replace("RTC.aspx", "PreviewRTC.aspx"), timeout=60).read().decode("utf-8", "replace")
    img = H.unescape(re.search(r'id="ImgSketchPage" src="([^"]+)"', prev).group(1))
    png = f.op.open(img, timeout=60).read()
    if png[:4] != b"\x89PNG":
        raise RuntimeError("Bhoomi did not return a PNG")
    return png


if __name__ == "__main__":  # live check: Doddamaskal (Magadi) survey 16
    f = open_survey("29", "1", "2", "41", "16")
    sur, hs = hissas(f)
    print("surnoc", sur, "hissas", hs)
    r = owners(f, hs[0][0])
    assert r["owners"] and r["owners"][0]["name"], r
    print(r)
