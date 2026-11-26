"""Agent tools without the LLM or the network: Bhoomi and e-Chawadi replaced by fakes (no real people)."""
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ["PAUTI_CASES"] = tempfile.mkdtemp()
import agent  # noqa: E402

OWNERS = [{"name": "ರಾಮಪ್ಪ ಬಿನ್ ಲೇ ಚನ್ನಪ್ಪ", "extent": "2.10.0", "court_stay": "No"}]
agent.rtc_reader.locate = lambda f, db: [{"village": "DODDAMASKAL", "dist": "29", "taluk": "1", "hobli": "2", "vlg": "41", "lgd": "1"}]
agent.bhoomi.open_survey = lambda *a: None
agent.bhoomi.hissas = lambda f: ("*", [("87", "1"), ("88", "2")])
agent.bhoomi.owners = lambda f, h: {"owners": OWNERS, "ongoing_mutation": "No", "pyki": "No"}
agent.bhoomi.place_name = lambda d, t: "RAMANAGARA / MAGADI"
agent.blockers_mod.blockers = lambda loc: [{"check": "court", "status": "green", "detail": "none", "action": ""}]

c = agent.Case("t1")
c.record_family(deceased_name="ರಾಮಪ್ಪ", deceased_sex="M", religion="hindu", spouse="ಲಕ್ಷ್ಮಮ್ಮ", relinquish=["ಕಾವ್ಯ"],
                children=[{"name": "ರವಿ", "sex": "M", "alive": True}, {"name": "ಕಾವ್ಯ", "sex": "F", "alive": True}])

r = c.find_land("ದೊಡ್ಡಮಸ್ಕಲ್", "16")
assert r["found"] is False and r["need_hissa"] == ["1", "2"], r          # two hissas: must ask, not guess
r = c.find_land("ದೊಡ್ಡಮಸ್ಕಲ್", "16", hissa="2")
assert r["found"] and r["hissa"] == "2" and r["deceased_on_rtc"] is True, r
assert c.check_blockers()["blockers"][0]["status"] == "green"
h = {x["name"]: x["share"] for x in c.compute_heirs()["heirs"]}
assert h == {"ಲಕ್ಷ್ಮಮ್ಮ": "1/3", "ರವಿ": "1/3", "ಕಾವ್ಯ": "1/3"}, h
pdf = c.make_papers()["pdf"]
assert os.path.getsize(pdf) > 10_000, pdf

OWNERS[:] = [{"name": "J.ಕೇಶವ A.ಜಯರಾಮು", "extent": "2.30.0"}]                # someone else's land
r = c.find_land("ದೊಡ್ಡಮಸ್ಕಲ್", "16", hissa="1")
assert r["deceased_on_rtc"] is False and "NOT" in r["say"], r

c.record_family(deceased_name="ರಾಮಪ್ಪ", deceased_sex="M", religion="muslim", children=[])
assert "needs_review" in c.compute_heirs()                                 # outside the Act: never guessed
print("ok", pdf)
