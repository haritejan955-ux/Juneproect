"""RxNorm-lite local drug reference table.

Small, curated, public-domain-style reference data (not a substitute for RxNorm/
First Databank in production) used to normalize drug names and validate doses.
"""

from typing import TypedDict


class DoseRange(TypedDict):
    min: float
    max: float
    unit: str


class DrugRecord(TypedDict):
    canonical_name: str
    aliases: list[str]
    drug_class: str
    allergy_class: str | None
    adult_dose_range: DoseRange
    renal_adjustment: dict[str, str]
    contraindicated_conditions: list[str]


DRUG_REFERENCE: dict[str, DrugRecord] = {
    "warfarin": {
        "canonical_name": "Warfarin",
        "aliases": ["coumadin", "jantoven"],
        "drug_class": "anticoagulant",
        "allergy_class": None,
        "adult_dose_range": {"min": 1, "max": 10, "unit": "mg/day"},
        "renal_adjustment": {"severe": "Monitor INR more frequently; no fixed dose cap."},
        "contraindicated_conditions": ["active bleeding", "pregnancy"],
    },
    "aspirin": {
        "canonical_name": "Aspirin",
        "aliases": ["asa", "acetylsalicylic acid"],
        "drug_class": "nsaid_antiplatelet",
        "allergy_class": "nsaids",
        "adult_dose_range": {"min": 81, "max": 325, "unit": "mg/day"},
        "renal_adjustment": {"severe": "Avoid; increased GI bleed and renal risk."},
        "contraindicated_conditions": ["active bleeding", "peptic ulcer"],
    },
    "ibuprofen": {
        "canonical_name": "Ibuprofen",
        "aliases": ["advil", "motrin"],
        "drug_class": "nsaid",
        "allergy_class": "nsaids",
        "adult_dose_range": {"min": 200, "max": 3200, "unit": "mg/day"},
        "renal_adjustment": {
            "moderate": "Max 1200 mg/day; avoid chronic use.",
            "severe": "Avoid; risk of acute kidney injury.",
        },
        "contraindicated_conditions": ["chronic kidney disease", "peptic ulcer"],
    },
    "amoxicillin": {
        "canonical_name": "Amoxicillin",
        "aliases": ["amoxil"],
        "drug_class": "penicillin_antibiotic",
        "allergy_class": "penicillins",
        "adult_dose_range": {"min": 250, "max": 1750, "unit": "mg/day"},
        "renal_adjustment": {"severe": "Reduce dose interval; max ~500 mg every 12h."},
        "contraindicated_conditions": [],
    },
    "penicillin_v": {
        "canonical_name": "Penicillin V",
        "aliases": ["pen vk", "penicillin v potassium"],
        "drug_class": "penicillin_antibiotic",
        "allergy_class": "penicillins",
        "adult_dose_range": {"min": 250, "max": 2000, "unit": "mg/day"},
        "renal_adjustment": {"severe": "Reduce dose frequency."},
        "contraindicated_conditions": [],
    },
    "metformin": {
        "canonical_name": "Metformin",
        "aliases": ["glucophage"],
        "drug_class": "biguanide_antidiabetic",
        "allergy_class": None,
        "adult_dose_range": {"min": 500, "max": 2000, "unit": "mg/day"},
        "renal_adjustment": {
            "moderate": "Max 1000 mg/day; reassess renal function every 3-6 months.",
            "severe": "Contraindicated; risk of lactic acidosis.",
        },
        "contraindicated_conditions": ["severe renal impairment", "metabolic acidosis"],
    },
    "lisinopril": {
        "canonical_name": "Lisinopril",
        "aliases": ["zestril", "prinivil"],
        "drug_class": "ace_inhibitor",
        "allergy_class": None,
        "adult_dose_range": {"min": 5, "max": 40, "unit": "mg/day"},
        "renal_adjustment": {"severe": "Start at 2.5-5 mg/day; monitor potassium and creatinine."},
        "contraindicated_conditions": ["pregnancy", "bilateral renal artery stenosis"],
    },
    "spironolactone": {
        "canonical_name": "Spironolactone",
        "aliases": ["aldactone"],
        "drug_class": "potassium_sparing_diuretic",
        "allergy_class": None,
        "adult_dose_range": {"min": 25, "max": 200, "unit": "mg/day"},
        "renal_adjustment": {"severe": "Avoid; high hyperkalemia risk."},
        "contraindicated_conditions": ["hyperkalemia", "addison's disease"],
    },
    "sertraline": {
        "canonical_name": "Sertraline",
        "aliases": ["zoloft"],
        "drug_class": "ssri",
        "allergy_class": None,
        "adult_dose_range": {"min": 25, "max": 200, "unit": "mg/day"},
        "renal_adjustment": {},
        "contraindicated_conditions": [],
    },
    "phenelzine": {
        "canonical_name": "Phenelzine",
        "aliases": ["nardil"],
        "drug_class": "maoi",
        "allergy_class": None,
        "adult_dose_range": {"min": 15, "max": 90, "unit": "mg/day"},
        "renal_adjustment": {},
        "contraindicated_conditions": [],
    },
    "simvastatin": {
        "canonical_name": "Simvastatin",
        "aliases": ["zocor"],
        "drug_class": "statin",
        "allergy_class": None,
        "adult_dose_range": {"min": 5, "max": 40, "unit": "mg/day"},
        "renal_adjustment": {"severe": "Max 20 mg/day."},
        "contraindicated_conditions": ["active liver disease"],
    },
    "clarithromycin": {
        "canonical_name": "Clarithromycin",
        "aliases": ["biaxin"],
        "drug_class": "macrolide_antibiotic",
        "allergy_class": "macrolides",
        "adult_dose_range": {"min": 500, "max": 1000, "unit": "mg/day"},
        "renal_adjustment": {"severe": "Reduce dose by 50%."},
        "contraindicated_conditions": ["qt prolongation"],
    },
    "digoxin": {
        "canonical_name": "Digoxin",
        "aliases": ["lanoxin"],
        "drug_class": "cardiac_glycoside",
        "allergy_class": None,
        "adult_dose_range": {"min": 0.0625, "max": 0.25, "unit": "mg/day"},
        "renal_adjustment": {
            "moderate": "Reduce dose; monitor levels closely.",
            "severe": "Max 0.0625 mg/day or every other day; monitor levels closely.",
        },
        "contraindicated_conditions": ["ventricular fibrillation"],
    },
    "furosemide": {
        "canonical_name": "Furosemide",
        "aliases": ["lasix"],
        "drug_class": "loop_diuretic",
        "allergy_class": None,
        "adult_dose_range": {"min": 20, "max": 600, "unit": "mg/day"},
        "renal_adjustment": {},
        "contraindicated_conditions": ["anuria"],
    },
    "lithium": {
        "canonical_name": "Lithium",
        "aliases": ["lithobid", "eskalith"],
        "drug_class": "mood_stabilizer",
        "allergy_class": None,
        "adult_dose_range": {"min": 300, "max": 2400, "unit": "mg/day"},
        "renal_adjustment": {
            "moderate": "Reduce dose 25-50%; monitor levels closely.",
            "severe": "Avoid if possible; monitor levels closely if used.",
        },
        "contraindicated_conditions": ["severe renal impairment", "dehydration"],
    },
    "acetaminophen": {
        "canonical_name": "Acetaminophen",
        "aliases": ["tylenol", "paracetamol"],
        "drug_class": "analgesic",
        "allergy_class": None,
        "adult_dose_range": {"min": 325, "max": 3000, "unit": "mg/day"},
        "renal_adjustment": {"severe": "Extend dosing interval to every 8h."},
        "contraindicated_conditions": ["severe hepatic impairment"],
    },
}

# Groups drugs that cross-react for allergy checking (e.g. penicillin-class allergy
# applies to every penicillin_antibiotic, not just the one the patient was previously exposed to).
ALLERGY_CLASS_LABELS: dict[str, str] = {
    "penicillins": "Penicillin-class antibiotics",
    "nsaids": "NSAIDs",
    "macrolides": "Macrolide antibiotics",
}


def find_drug(name: str) -> DrugRecord | None:
    """Look up a drug by canonical name or any known alias, case-insensitively."""
    key = name.strip().lower().replace(" ", "_")
    if key in DRUG_REFERENCE:
        return DRUG_REFERENCE[key]
    normalized = name.strip().lower()
    for record in DRUG_REFERENCE.values():
        if normalized == record["canonical_name"].lower() or normalized in record["aliases"]:
            return record
    return None
