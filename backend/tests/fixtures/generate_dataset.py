"""
generate_dataset.py
-------------------
Generates synthetic_hiring_500.csv — a reproducible 500-row Indian hiring
dataset with bias baked into the outcome column.

Bias rules (same skill scores, different hire rates by group):
  Muslim-origin surnames   → ~12% hire rate
  Upper-caste Hindu        → ~41% hire rate
  Tier-3 pin code          → ~18% hire rate
  Tier-1 pin code          → ~45% hire rate
  Private unranked college → ~12% hire rate
  IIT/IIM college          → ~76% hire rate

Run: python tests/fixtures/generate_dataset.py
"""

import numpy as np
import pandas as pd
import random
from pathlib import Path

rng = np.random.default_rng(42)

UPPER_HINDU_NAMES = [
    "Rahul Sharma", "Priya Mehta", "Arjun Verma", "Ananya Iyer", "Vikram Joshi",
    "Pooja Pandey", "Amit Tiwari", "Sneha Gupta", "Rajesh Kapoor", "Divya Malhotra",
    "Suresh Srivastava", "Kavya Saxena", "Aditya Bhatt", "Ritu Shukla", "Deepak Mishra",
    "Neha Tripathi", "Rohit Khanna", "Sunita Bose", "Manish Chatterjee", "Komal Mukherjee",
    "Sanjay Banerjee", "Priyanka Ghosh", "Vinay Sen", "Anjali Roy", "Gaurav Dasgupta",
    "Meera Chakraborty", "Tarun Rao", "Lakshmi Reddy", "Kiran Naidu", "Mohan Rajan",
    "Hema Krishnan", "Suresh Venkataraman", "Uma Balakrishnan", "Ravi Raghavan", "Chitra Swaminathan",
    "Suresh Natarajan", "Radha Agarwal", "Vivek Bansal", "Gita Goel", "Ashok Mittal",
    "Nidhi Singhal", "Abhijit Goyal", "Swati Jain", "Yash Maheshwari", "Rashi Poddar",
    "Himanshu Khandelwal", "Shweta Kohli", "Nikhil Chopra", "Archana Sethi", "Kunal Arora",
]

MUSLIM_NAMES = [
    "Mohd Ansari", "Fatima Khan", "Imran Sheikh", "Zara Siddiqui", "Amir Qureshi",
    "Sana Pathan", "Raza Shaikh", "Hina Mirza", "Salman Syed", "Shabana Chaudhary",
    "Farhan Malik", "Nazish Farooqui", "Iqbal Hashmi", "Saira Rizvi", "Waseem Baig",
    "Rukhsar Naqvi", "Asif Hussain", "Afreen Ali", "Tariq Ahmad", "Dilnoza Mohammed",
    "Javed Akhtar", "Mehnaz Raza", "Shahid Azmi", "Farzana Kidwai", "Adil Usmani",
    "Tabassum Quadri", "Yusuf Abbasi", "Mehwish Beg", "Irfan Chishti", "Rubina Fareedi",
    "Sajid Gilani", "Kaneez Hamdani", "Mujahid Islahi", "Sobia Jafri", "Shaukat Kazmi",
    "Gulnaz Lakhnavi", "Munawwar Moosavi", "Shazia Naeemi", "Toufiq Osmani", "Sabira Fakir",
    "Naeem Lashkar", "Shaheen Mewati", "Bilal Memon", "Jasmin Vohra", "Pervez Agha",
    "Rehana Diwan", "Rashid Suri", "Nadia Bahl", "Shakeel Purewal", "Asma Quadri",
]

SC_ST_NAMES = [
    "Raju Mahato", "Sunita Paswan", "Bhimrao Valmiki", "Meera Kori", "Suresh Dom",
    "Geeta Majhi", "Ramesh Murmu", "Poonam Hansda", "Bikash Soren", "Laxmi Besra",
    "Arun Tudu", "Kalpana Hembram", "Sanjay Kisku", "Rita Marndi", "Dinesh Baski",
    "Savitri Bodra", "Binod Oraon", "Champa Minz", "Anthony Tirkey", "Mary Kujur",
    "Jerome Lakra", "Rosetta Topno", "Sebastian Dungdung", "Agnes Ekka", "Philemon Xalxo",
    "Kamla Parmar", "Vikram Mahar", "Rekha Mang", "Damu Bhangi", "Lata Mehtar",
    "Bhola Regar", "Kamala Balai", "Ramesh Nayak", "Sushila Chamar", "Sunil Dhobi",
]

OBC_NAMES = [
    "Ramesh Yadav", "Sunita Patel", "Mahesh Kurmi", "Geeta Lodhi", "Suresh Chauhan",
    "Kavita Tomar", "Dinesh Kunbi", "Rekha Koli", "Ashok Prajapati", "Usha Kumhar",
    "Mohan Lohar", "Sita Sonar", "Ganesh Mali", "Pushpa Kahar", "Ravi Teli",
    "Laxmi Tamboli", "Prakash Shimpi", "Vandana Nhavi", "Raju Kumbhar", "Kamla Sutar",
    "Bhanu Gavli", "Sushila Dhotre", "Vijay Wanjari", "Anita Katkar", "Sanjay Jadhav",
    "Priya Shinde", "Dnyaneshwar Pawar", "Shalini More", "Amol Gaikwad", "Sunita Bhosale",
    "Pratap Chavan", "Lata Salunke", "Nitin Mohite", "Mangal Patil", "Pravin Deshmukh",
]

CHRISTIAN_NAMES = [
    "John DSouza", "Mary Fernandez", "Peter Pereira", "Grace Rodrigues", "Thomas Souza",
    "Angela Gomes", "Robert Pinto", "Christina Cardozo", "Michael Menezes", "Stella Lobo",
    "Paul Noronha", "Rosie DeSouza", "David Mathew", "Priscilla Thomas", "Stephen Philip",
    "Ruth Joseph", "James John", "Rebecca Paul", "Richard George", "Rachel Abraham",
]

SIKH_NAMES = [
    "Gurpreet Singh", "Harpreet Kaur", "Manpreet Gill", "Kulwinder Grewal", "Jaswinder Sandhu",
    "Paramjit Sidhu", "Balwinder Dhillon", "Sukhwinder Brar", "Jagdeep Randhawa", "Amarjit Virk",
    "Harjinder Bajwa", "Kuldeep Cheema", "Satinderpal Sekhon", "Ranjit Toor", "Gurjit Sohal",
]

COLLEGES_IIT = ["IIT Delhi", "IIT Bombay", "IIT Madras", "IIT Kanpur", "IIT Kharagpur", "IIM Ahmedabad", "IIM Bangalore"]
COLLEGES_NIT = ["BITS Pilani", "NIT Trichy", "NIT Warangal", "NIT Surathkal", "NIT Calicut", "NIT Rourkela"]
COLLEGES_STATE = ["Delhi University", "Mumbai University", "Anna University", "Osmania University",
                   "Punjab University", "Rajasthan University", "Kerala University", "Pune University",
                   "Jadavpur University", "Banaras Hindu University"]
COLLEGES_PVTRANK = ["Amity University", "Manipal University", "VIT University", "SRM University", "Christ University", "Symbiosis"]
COLLEGES_UNRANK = ["Amrapali Institute", "Sharda University", "Galgotias University",
                    "Noida International University", "GL Bajaj Group", "GLA University",
                    "Meerut Institute", "IIMT College", "Subharti University", "Invertis University"]

PINCODES_T1 = ["400001","400002","400003","110001","110002","110003","560001","560002","600001","600002","700001"]
PINCODES_T2 = ["400050","400051","400065","110031","110045","560025","560034","600028","700026","226001","500015"]
PINCODES_T3 = ["400100","400101","110093","560060","600050","743502","841301","841302","764001","500050","344001"]


def assign_hire(group: str, tier_pincode: str, college_tier: str, skill: float) -> str:
    """
    Determine hired/rejected. Base probability by most-biased factor.
    Skill score has a small but present effect.
    """
    base = 0.30  # neutral base

    # Surname/caste effect (dominant)
    surname_mod = {
        "upper_hindu": 0.15,
        "sikh": 0.10,
        "christian": 0.05,
        "obc": -0.05,
        "sc_st": -0.10,
        "muslim": -0.18,
    }.get(group, 0.0)

    # Pin code SES effect
    pin_mod = {"tier_1": 0.12, "tier_2": 0.0, "tier_3": -0.12}.get(tier_pincode, 0.0)

    # College effect
    college_mod = {
        "iit_iim": 0.40,
        "nit_bits": 0.20,
        "state_university": 0.0,
        "private_ranked": -0.05,
        "private_unranked": -0.18,
    }.get(college_tier, 0.0)

    # Small skill effect
    skill_mod = (skill - 70) / 200  # skill 40-100, effect ~-0.15 to +0.15

    prob = base + surname_mod + pin_mod + college_mod + skill_mod
    prob = max(0.04, min(0.95, prob))
    return "hired" if rng.random() < prob else "rejected"


def make_row(i):
    # Choose a name group with realistic distribution
    group_weights = [0.25, 0.20, 0.10, 0.25, 0.10, 0.10]
    group_pools = [UPPER_HINDU_NAMES, MUSLIM_NAMES, SC_ST_NAMES, OBC_NAMES, CHRISTIAN_NAMES, SIKH_NAMES]
    group_keys  = ["upper_hindu",     "muslim",      "sc_st",      "obc",      "christian",     "sikh"]
    g_idx = rng.choice(len(group_pools), p=group_weights)
    pool = group_pools[g_idx]
    group = group_keys[g_idx]
    name = pool[i % len(pool)]

    # College (7% IIT, 18% NIT, 38% state, 37% unranked — per spec)
    col_w = [0.07, 0.18, 0.38, 0.00, 0.37]
    col_pools = [COLLEGES_IIT, COLLEGES_NIT, COLLEGES_STATE, COLLEGES_PVTRANK, COLLEGES_UNRANK]
    col_tiers  = ["iit_iim",    "nit_bits",   "state_university", "private_ranked", "private_unranked"]
    c_idx = rng.choice(len(col_pools), p=col_w)
    college = col_pools[c_idx][rng.integers(len(col_pools[c_idx]))]
    col_tier = col_tiers[c_idx]

    # Pin code (30% T1, 35% T2, 35% T3 — per spec)
    pin_pool_choices = rng.choice([0, 1, 2], p=[0.30, 0.35, 0.35])
    pin_pool = [PINCODES_T1, PINCODES_T2, PINCODES_T3][pin_pool_choices]
    pin_tier = ["tier_1", "tier_2", "tier_3"][pin_pool_choices]
    pincode = pin_pool[rng.integers(len(pin_pool))]

    exp = int(rng.integers(0, 16))
    skill = int(rng.normal(70, 12))
    skill = max(40, min(100, skill))

    gender = rng.choice(["Male", "Female"], p=[0.60, 0.40])
    outcome = assign_hire(group, pin_tier, col_tier, skill)

    return {
        "candidate_name": name,
        "gender": gender,
        "college": college,
        "pincode": pincode,
        "years_experience": exp,
        "skill_score": skill,
        "outcome": outcome,
    }


if __name__ == "__main__":
    rows = [make_row(i) for i in range(500)]
    df = pd.DataFrame(rows)

    out = Path(__file__).parent / "synthetic_hiring_500.csv"
    df.to_csv(out, index=False)

    # Print summary stats
    print(f"Generated {len(df)} rows -> {out}")
    print(f"\nOverall hire rate: {(df.outcome=='hired').mean():.1%}")
    print("\nHire rate by surname group (derived):")
    for g, names, key in [
        ("Upper Hindu", UPPER_HINDU_NAMES, "upper_hindu"),
        ("Muslim",      MUSLIM_NAMES,      "muslim"),
        ("SC/ST",       SC_ST_NAMES,       "sc_st"),
        ("OBC",         OBC_NAMES,         "obc"),
    ]:
        surnames = [n.split()[-1] for n in names]
        mask = df["candidate_name"].apply(lambda x: x.split()[-1] in surnames)
        subset = df[mask]
        if len(subset):
            rate = (subset["outcome"] == "hired").mean()
            print(f"  {g:15s}: {rate:.1%} (n={len(subset)})")
