"""Realistic Indian coalfield baselines for seed data."""

COALFIELDS = [
    # name, subsidiary, state, area_sqkm, reserve_mt, baseline_gcv, baseline_ash, ob_ratio
    {"name": "Jharia", "subsidiary": "BCCL", "state": "Jharkhand", "area_sqkm": 450.0, "reserve_mt": 19300.0, "baseline_gcv": 5300.0, "baseline_ash": 22.0, "baseline_ob_ratio": 2.6},
    {"name": "Raniganj", "subsidiary": "ECL", "state": "West Bengal", "area_sqkm": 1530.0, "reserve_mt": 31100.0, "baseline_gcv": 4800.0, "baseline_ash": 24.0, "baseline_ob_ratio": 3.1},
    {"name": "East Bokaro", "subsidiary": "CCL", "state": "Jharkhand", "area_sqkm": 340.0, "reserve_mt": 128000.0, "baseline_gcv": 5900.0, "baseline_ash": 20.0, "baseline_ob_ratio": 2.2},
    {"name": "Korba", "subsidiary": "SECL", "state": "Chhattisgarh", "area_sqkm": 670.0, "reserve_mt": 10500.0, "baseline_gcv": 4420.0, "baseline_ash": 30.0, "baseline_ob_ratio": 4.2},
    {"name": "Singrauli", "subsidiary": "NCL", "state": "Madhya Pradesh", "area_sqkm": 2202.0, "reserve_mt": 15700.0, "baseline_gcv": 4100.0, "baseline_ash": 33.0, "baseline_ob_ratio": 5.1},
    {"name": "Talcher", "subsidiary": "MCL", "state": "Odisha", "area_sqkm": 1835.0, "reserve_mt": 18900.0, "baseline_gcv": 3950.0, "baseline_ash": 36.0, "baseline_ob_ratio": 6.0},
    {"name": "Ib Valley", "subsidiary": "MCL", "state": "Odisha", "area_sqkm": 2260.0, "reserve_mt": 13500.0, "baseline_gcv": 3800.0, "baseline_ash": 38.0, "baseline_ob_ratio": 5.4},
]

BLOCKS = {
    "Jharia": [
        {"block": "Pandaveswar East", "district": "Dhanbad"},
        {"block": "Sijua South", "district": "Dhanbad"},
        {"block": "Kusunda Central", "district": "Dhanbad"},
    ],
    "Raniganj": [
        {"block": "Barabani West", "district": "Bardhaman"},
        {"block": "Galudih North", "district": "Bardhaman"},
    ],
    "East Bokaro": [
        {"block": "Parej East", "district": "Bokaro"},
        {"block": "Parej West", "district": "Bokaro"},
    ],
    "Korba": [
        {"block": "Gare Palma IV", "district": "Korba"},
        {"block": "Jampali North", "district": "Raigarh"},
    ],
    "Singrauli": [
        {"block": "Nirsa East", "district": "Singrauli"},
    ],
    "Talcher": [
        {"block": "Talcher North", "district": "Angul"},
        {"block": "Kaniha West", "district": "Angul"},
        {"block": "Nandira Central", "district": "Angul"},
    ],
    "Ib Valley": [
        {"block": "Basundhara South", "district": "Jharsuguda"},
        {"block": "Sardega North", "district": "Bargarh"},
    ],
}

SEAMS = {
    "Jharia": ["Kajora Top", "XVIII seam", "Kajora Lower", "Argada top"],
    "Raniganj": ["Gondwana Main", "Sitalpur seam", "Rongritop", "Salanpur"],
    "East Bokaro": ["Karka Upper", "Karharbari", "Bermo Main", "Parej top"],
    "Korba": ["Kusmunda seam", "Gevra top", "Dipka main", "Mahamandal"],
    "Singrauli": ["Turra seam", "Rihand top", "Nirsa main", "Bina"],
    "Talcher": ["Talcher seam II", "Jharia top", "Kaniha main", "Gopalpur"],
    "Ib Valley": ["Bhubaneswari seam", "Jamual", "Basundhara main", "Sardega"],
}

GRADES = ["G8", "G10", "G12", "G14", "G16", "M2", "M4"]

# (suffix, category) permutations to build 18 distinct docs
# We'll generate a deterministic set in run_seed with assigned categories.