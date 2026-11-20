from app.eligibility.engine import (
    Status, evaluate, evaluate_all, load_fields, load_schemes, next_question,
)

SCHEMES = {s["id"]: s for s in load_schemes()}

CLEAN_FARMER = {
    "state": "Maharashtra",
    "owns_cultivable_land": True,
    "is_income_tax_payer": False,
    "is_govt_employee": False,
    "is_constitutional_post_holder": False,
    "is_professional": False,
    "monthly_pension": 0,
}


def test_pm_kisan_eligible_farmer():
    assert evaluate(SCHEMES["pm_kisan"], CLEAN_FARMER).status == Status.ELIGIBLE


def test_pm_kisan_excluded_income_tax_payer():
    r = evaluate(SCHEMES["pm_kisan"], {**CLEAN_FARMER, "is_income_tax_payer": True})
    assert r.status == Status.NOT_ELIGIBLE
    assert r.matched_exclusions[0]["field"] == "is_income_tax_payer"


def test_pm_kisan_excluded_high_pension():
    r = evaluate(SCHEMES["pm_kisan"], {**CLEAN_FARMER, "monthly_pension": 12000})
    assert r.status == Status.NOT_ELIGIBLE


def test_pm_kisan_no_land():
    r = evaluate(SCHEMES["pm_kisan"], {**CLEAN_FARMER, "owns_cultivable_land": False})
    assert r.status == Status.NOT_ELIGIBLE


def test_pm_kisan_need_info_when_profile_partial():
    r = evaluate(SCHEMES["pm_kisan"], {"owns_cultivable_land": True})
    assert r.status == Status.NEED_INFO
    assert "is_income_tax_payer" in r.missing_fields


def test_namo_shetkari_only_maharashtra():
    p = {"state": "Karnataka", "owns_cultivable_land": True, "is_pm_kisan_beneficiary": True}
    assert evaluate(SCHEMES["namo_shetkari"], p).status == Status.NOT_ELIGIBLE
    p["state"] = "maharashtra"
    assert evaluate(SCHEMES["namo_shetkari"], p).status == Status.ELIGIBLE


def test_ujjwala_requires_woman_without_lpg():
    p = {"gender": "female", "age": 30, "household_has_lpg": False, "is_poor_household": True}
    assert evaluate(SCHEMES["pm_ujjwala"], p).status == Status.ELIGIBLE
    assert evaluate(SCHEMES["pm_ujjwala"], {**p, "gender": "male"}).status == Status.NOT_ELIGIBLE
    assert evaluate(SCHEMES["pm_ujjwala"], {**p, "household_has_lpg": True}).status == Status.NOT_ELIGIBLE
    assert evaluate(SCHEMES["pm_ujjwala"], {**p, "age": 17}).status == Status.NOT_ELIGIBLE


def test_next_question_and_translations():
    results = evaluate_all(list(SCHEMES.values()), {"state": "maharashtra"})
    q = next_question(results)
    assert q is not None
    fields = load_fields()
    for r in results:
        for f in r.missing_fields:
            assert f in fields, f"missing question text for {f}"
            assert {"en", "hi", "mr"} <= fields[f]["question"].keys()


# ---------- data integrity ----------

REQUIRED_KEYS = {"id", "name", "level", "states", "benefit", "eligibility", "exclusions",
                 "documents", "how_to_apply", "source_url", "official_url", "verified"}


def _fields_in(node):
    if "field" in node:
        yield node["field"]
    for key in ("all_of", "any_of"):
        for child in node.get(key, []):
            yield from _fields_in(child)


def test_every_scheme_is_complete_and_askable():
    fields = load_fields()
    for s in SCHEMES.values():
        assert REQUIRED_KEYS <= s.keys(), s["id"]
        for lang in ("en", "hi", "mr"):
            assert s["name"][lang] and s["benefit"][lang] and s["how_to_apply"][lang], s["id"]
        for f in _fields_in(s["eligibility"]):
            assert f in fields, f"{s['id']}: no question for {f}"
        for f in _fields_in(s["exclusions"]):
            assert f in fields, f"{s['id']}: no question for {f}"


# ---------- OR groups ----------

def test_shravanbal_income_or_bpl():
    base = {"state": "maharashtra", "age": 70}
    assert evaluate(SCHEMES["shravanbal"], {**base, "is_bpl": True}).status == Status.ELIGIBLE
    assert evaluate(SCHEMES["shravanbal"], {**base, "is_bpl": False, "annual_family_income": 20000}).status == Status.ELIGIBLE
    assert evaluate(SCHEMES["shravanbal"], {**base, "is_bpl": False, "annual_family_income": 50000}).status == Status.NOT_ELIGIBLE
    r = evaluate(SCHEMES["shravanbal"], base)
    assert r.status == Status.NEED_INFO and {"is_bpl", "annual_family_income"} <= set(r.missing_fields)
    assert evaluate(SCHEMES["shravanbal"], {**base, "age": 60, "is_bpl": True}).status == Status.NOT_ELIGIBLE


# ---------- new schemes ----------

def test_ladki_bahin():
    p = {"state": "maharashtra", "gender": "female", "age": 35, "annual_family_income": 200000,
         "has_bank_account": True, "is_income_tax_payer": False, "is_govt_employee": False,
         "is_constitutional_post_holder": False, "owns_four_wheeler": False}
    assert evaluate(SCHEMES["ladki_bahin"], p).status == Status.ELIGIBLE
    assert evaluate(SCHEMES["ladki_bahin"], {**p, "owns_four_wheeler": True}).status == Status.NOT_ELIGIBLE
    assert evaluate(SCHEMES["ladki_bahin"], {**p, "annual_family_income": 300000}).status == Status.NOT_ELIGIBLE
    assert evaluate(SCHEMES["ladki_bahin"], {**p, "age": 66}).status == Status.NOT_ELIGIBLE
    assert evaluate(SCHEMES["ladki_bahin"], {**p, "state": "gujarat"}).status == Status.NOT_ELIGIBLE


def test_apy_age_and_self_tax():
    p = {"age": 30, "has_bank_account": True, "is_self_income_tax_payer": False}
    assert evaluate(SCHEMES["apy"], p).status == Status.ELIGIBLE
    assert evaluate(SCHEMES["apy"], {**p, "age": 41}).status == Status.NOT_ELIGIBLE
    assert evaluate(SCHEMES["apy"], {**p, "is_self_income_tax_payer": True}).status == Status.NOT_ELIGIBLE


def test_insurance_age_bands():
    assert evaluate(SCHEMES["pmjjby"], {"age": 50, "has_bank_account": True}).status == Status.ELIGIBLE
    assert evaluate(SCHEMES["pmjjby"], {"age": 51, "has_bank_account": True}).status == Status.NOT_ELIGIBLE
    assert evaluate(SCHEMES["pmsby"], {"age": 70, "has_bank_account": True}).status == Status.ELIGIBLE
    assert evaluate(SCHEMES["pmsby"], {"age": 70, "has_bank_account": False}).status == Status.NOT_ELIGIBLE


def test_pm_kmy_small_farmer_only():
    p = {**CLEAN_FARMER, "age": 30, "land_hectares": 1.5, "has_other_pension_scheme": False}
    assert evaluate(SCHEMES["pm_kmy"], p).status == Status.ELIGIBLE
    assert evaluate(SCHEMES["pm_kmy"], {**p, "land_hectares": 3}).status == Status.NOT_ELIGIBLE
    assert evaluate(SCHEMES["pm_kmy"], {**p, "has_other_pension_scheme": True}).status == Status.NOT_ELIGIBLE


def test_pmmvy_income_group():
    p = {"gender": "female", "age": 25, "is_pregnant_or_new_mother": True, "is_govt_employee": False,
         "is_poor_household": False, "is_bpl": False, "annual_family_income": 500000}
    assert evaluate(SCHEMES["pmmvy"], p).status == Status.ELIGIBLE
    assert evaluate(SCHEMES["pmmvy"], {**p, "annual_family_income": 900000}).status == Status.NOT_ELIGIBLE
    assert evaluate(SCHEMES["pmmvy"], {**p, "annual_family_income": 900000, "is_bpl": True}).status == Status.ELIGIBLE


def test_satara_farmer_story():
    """The demo story: a 45-year-old male farmer in Maharashtra with 2 acres."""
    profile = {**CLEAN_FARMER, "age": 45, "gender": "male", "is_pm_kisan_beneficiary": True,
               "land_hectares": 0.8, "is_cultivator": True, "has_bank_account": True,
               "is_self_income_tax_payer": False, "has_other_pension_scheme": False,
               "is_street_vendor": False, "household_has_lpg": True, "is_poor_household": False,
               "is_bpl": False, "annual_family_income": 120000, "is_pregnant_or_new_mother": False,
               "owns_four_wheeler": False}
    eligible = {r.scheme_id for r in evaluate_all(list(SCHEMES.values()), profile) if r.status == Status.ELIGIBLE}
    assert {"pm_kisan", "namo_shetkari", "pmfby", "pmsby", "pmjjby", "gopinath_munde"} <= eligible
    assert "pm_kmy" not in eligible      # age 45 > 40
    assert "apy" not in eligible         # age 45 > 40
    assert "ladki_bahin" not in eligible


def test_namo_shetkari_needs_land_so_no_pm_kisan_question():
    r = evaluate(SCHEMES["namo_shetkari"], {"state": "maharashtra", "owns_cultivable_land": False})
    assert r.status == Status.NOT_ELIGIBLE
    assert "is_pm_kisan_beneficiary" not in r.missing_fields


def test_near_miss_bank_account():
    from app.eligibility.engine import near_misses
    profile = {"state": "maharashtra", "gender": "female", "age": 35, "has_bank_account": False}
    tips = near_misses(list(SCHEMES.values()), profile)
    unlocked = {s["id"] for s in tips["has_bank_account"]}
    assert {"ladki_bahin", "pmjjby", "pmsby", "apy"} <= unlocked
    assert "pm_kisan" not in unlocked


def test_no_near_miss_when_already_has_account():
    from app.eligibility.engine import near_misses
    assert near_misses(list(SCHEMES.values()), {"age": 35, "has_bank_account": True}) == {}
