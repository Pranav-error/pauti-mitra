"""Heir rules engine: who inherits a Hindu owner's land, and what share.

Code decides, the LLM only explains. Covers the common case (Hindu Succession Act 1956, as amended 2005):
  - male owner, no will: Class I heirs, s.8 + s.10 Rules 1-4
  - female owner, no will: s.15(1)(a) + s.16 Rule 2
Everything else raises NeedsReview and goes to the revenue office. The agent never guesses.

Text checked against the Indian Kanoon copy of the Act (doc/685111), not the gazette. Re-verify before the finale.

Case shape (what the agent fills in from the conversation):
  {"sex": "M"|"F", "religion": "hindu", "will": False, "ancestral": False, "dispute": False,
   "spouse": "name or None", "mother": "name or None",
   "children": [person]}
  person = {"name", "sex", "alive", "spouse": name or None, "children": [person]}
"""
from fractions import Fraction

# The Act covers Hindus, Buddhists, Jains and Sikhs (s.2).
COVERED = {"hindu", "buddhist", "jain", "sikh"}
CHILD = {"M": "son", "F": "daughter"}


class NeedsReview(Exception):
    """A case the rules don't settle. Send it to the revenue office."""


def _label(path):
    # path is the line of descent, e.g. ["son", "daughter"] -> "daughter of predeceased son"
    *up, last = path
    return " of ".join([last] + [f"predeceased {p}" for p in reversed(up)])


def _split(units):
    """units: list of {name: (relation, share within unit)}. Each unit gets an equal part."""
    out = {}
    for u in units:
        for name, (rel, f) in u.items():
            if name in out:
                raise ValueError(f"duplicate name {name!r}: names must be unique")
            out[name] = (rel, f / len(units))
    return out


def _alive_descendants(p):
    return any(c["alive"] or _alive_descendants(c) for c in p.get("children", []))


def _son_branch(p, path):
    """s.10 Rule 4(i): his widow, his surviving children, and each of his predeceased sons' branches
    take equal portions. Class I reaches one level down (son / daughter / widow of a predeceased son
    of a predeceased son)."""
    units = []
    if p.get("spouse"):
        units.append({p["spouse"]: (_label(path[:-1] + ["widow"]) if len(path) > 1 else "widow of predeceased son", Fraction(1))})
    for c in p.get("children", []):
        cpath = path + [CHILD[c["sex"]]]
        if c["alive"]:
            units.append({c["name"]: (_label(cpath), Fraction(1))})
        elif not _alive_descendants(c):
            continue
        elif c["sex"] == "M" and len(path) == 1:
            sub = _son_branch(c, cpath)
            if sub:
                units.append(sub)
        elif c["sex"] == "F" and len(path) == 1:
            # 2005 made "daughter of a predeceased daughter of a predeceased son" Class I, but Rule 4 gives no portion.
            raise NeedsReview(f"{c['name']}: predeceased daughter inside a son's branch; Rule 4 is silent")
        # deeper descendants are not Class I and take nothing
    return _split(units) if units else {}


def _daughter_branch(p, path):
    """s.10 Rule 4(ii): her surviving sons and daughters take equal portions. Her husband takes nothing."""
    for c in p.get("children", []):
        if not c["alive"] and _alive_descendants(c):
            # 2005 added great-grandchildren through her to Class I, but Rule 4(ii) gives no portion.
            raise NeedsReview(f"{c['name']}: predeceased child inside a daughter's branch; Rule 4 is silent")
    units = [{c["name"]: (_label(path + [CHILD[c["sex"]]]), Fraction(1))} for c in p.get("children", []) if c["alive"]]
    return _split(units) if units else {}


def heirs(case):
    """Return [{"name", "relation", "share"}] with shares as Fractions summing to 1, or raise NeedsReview."""
    if case.get("religion", "hindu").lower() not in COVERED:
        raise NeedsReview("not covered by the Hindu Succession Act; different personal law")
    for flag, why in (("will", "a will exists"), ("ancestral", "ancestral/coparcenary property (s.6)"),
                      ("dispute", "family dispute or court case")):
        if case.get(flag):
            raise NeedsReview(why)

    units = []
    if case["sex"] == "M":
        if case.get("spouse"):
            units.append({case["spouse"]: ("widow", Fraction(1))})          # Rule 1
        if case.get("mother"):
            units.append({case["mother"]: ("mother", Fraction(1))})         # Rule 2
        for c in case.get("children", []):
            path = [CHILD[c["sex"]]]
            if c["alive"]:
                units.append({c["name"]: (_label(path), Fraction(1))})      # Rule 2
            else:
                b = (_son_branch if c["sex"] == "M" else _daughter_branch)(c, path)  # Rules 3, 4
                if b:
                    units.append(b)
        if not units:
            raise NeedsReview("no Class I heir; Class II / agnates apply")
    else:
        if case.get("spouse"):
            units.append({case["spouse"]: ("husband", Fraction(1))})
        for c in case.get("children", []):
            path = [CHILD[c["sex"]]]
            if c["alive"]:
                units.append({c["name"]: (_label(path), Fraction(1))})
            else:  # s.16 Rule 2: living children of a predeceased child take the parent's share
                kids = [{g["name"]: (_label(path + [CHILD[g["sex"]]]), Fraction(1))}
                        for g in c.get("children", []) if g["alive"]]
                if kids:
                    units.append(_split(kids))
        if not units:
            raise NeedsReview("no child or husband; s.15(1)(b)-(e) and s.15(2) source-of-property rules apply")

    return [{"name": n, "relation": r, "share": f} for n, (r, f) in _split(units).items()]
