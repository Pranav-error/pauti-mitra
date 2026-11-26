"""Run: python3 engine/test_heirs.py  (or pytest)"""
from fractions import Fraction as F
from heirs import heirs, NeedsReview


def P(name, sex, alive=True, spouse=None, children=()):
    return {"name": name, "sex": sex, "alive": alive, "spouse": spouse, "children": list(children)}


def shares(case):
    out = {h["name"]: h["share"] for h in heirs(case)}
    assert sum(out.values()) == 1, out
    return out


def review(case):
    try:
        heirs(case)
    except NeedsReview:
        return True
    return False


def test_widow_mother_children_equal():
    # Rules 1+2: widow, mother, sons and daughter each one share; daughter equal to son (2005).
    c = {"sex": "M", "spouse": "Lakshmi", "mother": "Gowramma",
         "children": [P("Ravi", "M"), P("Suresh", "M"), P("Kavya", "F")]}
    assert shares(c) == {n: F(1, 5) for n in ["Lakshmi", "Gowramma", "Ravi", "Suresh", "Kavya"]}


def test_predeceased_son_branch():
    # Rule 4(i): his widow and his children split his one share equally.
    c = {"sex": "M", "spouse": "Lakshmi",
         "children": [P("Ravi", "M"), P("Mohan", "M", alive=False, spouse="Shanta",
                                         children=[P("Arun", "M"), P("Divya", "F")])]}
    s = shares(c)
    assert s["Lakshmi"] == s["Ravi"] == F(1, 3)
    assert s["Shanta"] == s["Arun"] == s["Divya"] == F(1, 9)


def test_predeceased_daughter_branch_husband_excluded():
    # Rule 4(ii): her children split her share; her husband takes nothing.
    c = {"sex": "M", "children": [P("Ravi", "M"),
                                  P("Meena", "F", alive=False, spouse="Prakash",
                                    children=[P("Anil", "M"), P("Sita", "F")])]}
    s = shares(c)
    assert s == {"Ravi": F(1, 2), "Anil": F(1, 4), "Sita": F(1, 4)}
    assert "Prakash" not in s


def test_two_level_son_branch():
    # Predeceased son of predeceased son: his widow and children are Class I.
    grandson = P("Kiran", "M", alive=False, spouse="Asha", children=[P("Neha", "F")])
    c = {"sex": "M", "children": [P("Ravi", "M"), P("Mohan", "M", alive=False, children=[P("Vinay", "M"), grandson])]}
    s = shares(c)
    assert s["Ravi"] == F(1, 2) and s["Vinay"] == F(1, 4)
    assert s["Asha"] == s["Neha"] == F(1, 8)
    rel = {h["name"]: h["relation"] for h in heirs(c)}
    assert rel["Neha"] == "daughter of predeceased son of predeceased son"


def test_female_owner():
    # s.15(1)(a) + s.16 Rule 2.
    c = {"sex": "F", "spouse": "Ramesh",
         "children": [P("Ravi", "M"), P("Meena", "F", alive=False, children=[P("Anil", "M"), P("Sita", "F")])]}
    assert shares(c) == {"Ramesh": F(1, 3), "Ravi": F(1, 3), "Anil": F(1, 6), "Sita": F(1, 6)}


def test_dead_branch_with_nobody_alive_takes_nothing():
    c = {"sex": "M", "spouse": "Lakshmi", "children": [P("Mohan", "M", alive=False)]}
    assert shares(c) == {"Lakshmi": F(1)}


def test_flags_go_to_revenue_office():
    base = {"sex": "M", "children": [P("Ravi", "M")]}
    assert review({**base, "will": True})
    assert review({**base, "ancestral": True})
    assert review({**base, "religion": "muslim"})
    assert review({"sex": "M", "children": []})                          # Class II
    assert review({"sex": "F", "children": []})                          # s.15(1)(b) onwards
    # 2005 Class I entry that Rule 4 gives no portion to
    assert review({"sex": "M", "children": [P("Mohan", "M", alive=False, children=[
        P("Rekha", "F", alive=False, children=[P("Pooja", "F")])])]})
    assert not review(base)


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
