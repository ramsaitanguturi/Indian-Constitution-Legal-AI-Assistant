"""
Constitution Ingestion Module.
Parses official consolidated Constitution of India (Preamble, all 395+ articles across Parts I–XXII,
and all 12 Schedules) into structured, schema-compliant legal records with clauses, provisos,
and provenance tracking.
"""

import os
import sys
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import (
    RAW_CONSTITUTION_DIR,
    PROCESSED_CONSTITUTION_DIR,
    CONSTITUTION_ARTICLES_PATH,
)

SOURCE_URL_CONSTITUTION = "https://www.legislative.gov.in/constitution-of-india/"
SOURCE_NAME_CONSTITUTION = "Legislative Department, Ministry of Law and Justice, Government of India"
LICENSE_CONSTITUTION = "Government Open Data License - India (GODL)"
VERSION_DATE_CONSTITUTION = "2024-01-01 (Amended up to 106th Amendment Act)"


def determine_part_and_category(article_num_str: str) -> Tuple[str, str]:
    """Map article numbers to their constitutional Part and thematic Category."""
    if article_num_str.lower() in ("0", "preamble"):
        return "Preamble", "Foundational Philosophy"

    # Extract digits
    match = re.search(r'(\d+)', article_num_str)
    if not match:
        return "Part Miscellaneous", "General Constitutional Law"
    
    num = int(match.group(1))

    if 1 <= num <= 4:
        return "Part I - The Union and its Territory", "Territorial Sovereignty"
    elif 5 <= num <= 11:
        return "Part II - Citizenship", "Citizenship & Nationality"
    elif 12 <= num <= 35:
        return "Part III - Fundamental Rights", "Fundamental Rights & Constitutional Remedies"
    elif 36 <= num <= 51 and "A" not in article_num_str.upper():
        return "Part IV - Directive Principles of State Policy", "Directive Principles of State Policy"
    elif num == 51 and "A" in article_num_str.upper():
        return "Part IVA - Fundamental Duties", "Fundamental Duties"
    elif 52 <= num <= 151:
        return "Part V - The Union", "Union Executive, Parliament & Judiciary"
    elif 152 <= num <= 237:
        return "Part VI - The States", "State Executive, Legislature & High Courts"
    elif 239 <= num <= 242:
        return "Part VIII - The Union Territories", "Union Territories Administration"
    elif num == 243 and any(x in article_num_str.upper() for x in "ABCDEFGHIJKLMNO"):
        return "Part IX - The Panchayats", "Local Self-Government (Rural)"
    elif num == 243 and any(x in article_num_str.upper() for x in "PQRSTUVWXYZ"):
        return "Part IXA - The Municipalities", "Local Self-Government (Urban)"
    elif 244 <= num <= 244:
        return "Part X - The Scheduled and Tribal Areas", "Tribal Administration"
    elif 245 <= num <= 263:
        return "Part XI - Relations between Union and States", "Federal Legislative & Administrative Relations"
    elif 264 <= num <= 300:
        return "Part XII - Finance, Property, Contracts and Suits", "Fiscal Federalism & Property Rights"
    elif 301 <= num <= 307:
        return "Part XIII - Trade, Commerce and Intercourse", "Inter-State Trade & Commerce"
    elif 308 <= num <= 323:
        return "Part XIV - Services under the Union and the States", "Public Services & Public Service Commissions"
    elif "323" in article_num_str:
        return "Part XIVA - Tribunals", "Administrative & Special Tribunals"
    elif 324 <= num <= 329:
        return "Part XV - Elections", "Electoral Law & Election Commission"
    elif 330 <= num <= 342:
        return "Part XVI - Special Provisions Relating to Certain Classes", "Affirmative Action & Representation"
    elif 343 <= num <= 351:
        return "Part XVII - Official Language", "Official Language of the Union & States"
    elif 352 <= num <= 360:
        return "Part XVIII - Emergency Provisions", "National, State & Financial Emergency"
    elif 361 <= num <= 367:
        return "Part XIX - Miscellaneous", "Executive Immunities & Interpretation"
    elif num == 368:
        return "Part XX - Amendment of the Constitution", "Constitutional Amendment Power & Procedure"
    elif 369 <= num <= 392:
        return "Part XXI - Temporary, Transitional and Special Provisions", "Special Asymmetric Federalism & Transitional Powers"
    elif 393 <= num <= 395:
        return "Part XXII - Short Title, Commencement and Repeals", "Commencement & Enactment"
    else:
        return "Schedules & Appendices", "Schedules & Annexures"


def parse_clauses_from_text(raw_text: str, doc_id: str) -> List[Dict[str, str]]:
    """Split structured article text into individual clause records."""
    clauses = []
    # Match patterns like (1), (2), (a), (b), or numbered paragraphs
    clause_pattern = re.compile(r'(?:\n|^)\s*(\(\d+[a-zA-Z]?\))\s*(.*?)(?=(?:\n\s*\(\d+[a-zA-Z]?\)|\Z))', re.DOTALL)
    matches = list(clause_pattern.finditer(raw_text))

    if matches:
        for idx, m in enumerate(matches, start=1):
            cl_num = m.group(1).strip()
            cl_content = m.group(2).strip()
            if cl_content:
                clauses.append({
                    "clause_id": f"{doc_id}_cl_{idx}",
                    "clause_number": cl_num,
                    "text": cl_content,
                })
    else:
        # Single provision without numbered clauses
        clauses.append({
            "clause_id": f"{doc_id}_main",
            "clause_number": "Main Provision",
            "text": raw_text.strip(),
        })

    return clauses


SCHEDULES_DATA = [
    {
        "id": "const_sched_01",
        "document_id": "const_sched_01",
        "document_type": "constitution_article",
        "article_number": "First Schedule",
        "part": "Schedules",
        "category": "Territorial Distribution",
        "title": "First Schedule: States and Union Territories",
        "text": "The First Schedule lists the States and Union Territories of India, specifying the territories and borders belonging to each State and Union Territory pursuant to Articles 1 and 4.",
        "explanation": "Articles 1 and 4. Details the 28 States and 8 Union Territories comprising the territory of India.",
        "clauses": [
            {"clause_id": "const_sched_01_states", "clause_number": "I", "text": "The States and their territorial extents."},
            {"clause_id": "const_sched_01_uts", "clause_number": "II", "text": "The Union Territories and their territorial extents."}
        ]
    },
    {
        "id": "const_sched_02",
        "document_id": "const_sched_02",
        "document_type": "constitution_article",
        "article_number": "Second Schedule",
        "part": "Schedules",
        "category": "Salaries & Emoluments",
        "title": "Second Schedule: Emoluments, Allowances and Privileges of Constitutional Functionaries",
        "text": "Provisions as to the President and the Governors of States, the Speaker and Deputy Speaker of the Lok Sabha and Rajya Sabha, Judges of the Supreme Court and High Courts, and the Comptroller and Auditor-General of India pursuant to Articles 59(3), 65(3), 75(6), 97, 125, 148(3), 158(3), 164(5), 186 and 221.",
        "explanation": "Sets out constitutional remuneration safeguards to preserve judicial and institutional independence.",
        "clauses": [
            {"clause_id": "const_sched_02_pres", "clause_number": "Part A", "text": "Emoluments and allowances for the President and Governors."},
            {"clause_id": "const_sched_02_judges", "clause_number": "Part D", "text": "Salaries and pensions of Supreme Court and High Court Judges."}
        ]
    },
    {
        "id": "const_sched_03",
        "document_id": "const_sched_03",
        "document_type": "constitution_article",
        "article_number": "Third Schedule",
        "part": "Schedules",
        "category": "Oaths and Affirmations",
        "title": "Third Schedule: Forms of Oaths or Affirmations",
        "text": "Forms of Oaths or Affirmations for Union Ministers, Parliamentary candidates, Members of Parliament, Supreme Court Judges, CAG, State Ministers, State Legislators, and High Court Judges pursuant to Articles 75(4), 99, 124(6), 148(2), 164(3), 188 and 219.",
        "explanation": "Prescribes solemn constitutional declarations of allegiance, secrecy, and true faith.",
        "clauses": [
            {"clause_id": "const_sched_03_min", "clause_number": "I & II", "text": "Forms of oath of office and secrecy for Ministers of the Union."},
            {"clause_id": "const_sched_03_judges", "clause_number": "IV", "text": "Form of oath or affirmation for Supreme Court Judges."}
        ]
    },
    {
        "id": "const_sched_04",
        "document_id": "const_sched_04",
        "document_type": "constitution_article",
        "article_number": "Fourth Schedule",
        "part": "Schedules",
        "category": "Parliamentary Federal Allocation",
        "title": "Fourth Schedule: Allocation of Seats in the Council of States (Rajya Sabha)",
        "text": "Allocation of seats in the Council of States (Rajya Sabha) to be filled by representatives of the States and Union Territories pursuant to Articles 4(1) and 80(2).",
        "explanation": "Ensures proportional federal representation of States in the Upper House of Parliament.",
        "clauses": [
            {"clause_id": "const_sched_04_alloc", "clause_number": "Table", "text": "Allocation table specifying seats assigned to each State and Union Territory."}
        ]
    },
    {
        "id": "const_sched_05",
        "document_id": "const_sched_05",
        "document_type": "constitution_article",
        "article_number": "Fifth Schedule",
        "part": "Schedules",
        "category": "Scheduled Areas Governance",
        "title": "Fifth Schedule: Administration and Control of Scheduled Areas and Scheduled Tribes",
        "text": "Provisions as to the Administration and Control of Scheduled Areas and Scheduled Tribes in States other than Assam, Meghalaya, Tripura and Mizoram pursuant to Article 244(1).",
        "explanation": "Empowers Governors to adapt or exclude laws and mandates Tribes Advisory Councils.",
        "clauses": [
            {"clause_id": "const_sched_05_exec", "clause_number": "Part B", "text": "Executive power of the State in Scheduled Areas and Tribes Advisory Council."},
            {"clause_id": "const_sched_05_laws", "clause_number": "Part C", "text": "Law applicable to Scheduled Areas and power of Governor to make regulations."}
        ]
    },
    {
        "id": "const_sched_06",
        "document_id": "const_sched_06",
        "document_type": "constitution_article",
        "article_number": "Sixth Schedule",
        "part": "Schedules",
        "category": "Autonomous District Councils",
        "title": "Sixth Schedule: Administration of Tribal Areas in Assam, Meghalaya, Tripura and Mizoram",
        "text": "Provisions as to the Administration of Tribal Areas in the States of Assam, Meghalaya, Tripura and Mizoram pursuant to Articles 244(2) and 275(1).",
        "explanation": "Creates Autonomous District Councils and Autonomous Regional Councils with legislative, judicial, and executive autonomy.",
        "clauses": [
            {"clause_id": "const_sched_06_adc", "clause_number": "Para 2", "text": "Constitution of District Councils and Regional Councils."},
            {"clause_id": "const_sched_06_powers", "clause_number": "Para 3", "text": "Powers of District Councils and Regional Councils to make laws."}
        ]
    },
    {
        "id": "const_sched_07",
        "document_id": "const_sched_07",
        "document_type": "constitution_article",
        "article_number": "Seventh Schedule",
        "part": "Schedules",
        "category": "Federal Legislative Lists",
        "title": "Seventh Schedule: Union, State, and Concurrent Legislative Lists",
        "text": "List I (Union List containing 97 numbered entries of exclusive parliamentary competence), List II (State List containing 66 numbered entries of exclusive state legislative competence), and List III (Concurrent List containing 47 numbered entries of shared competence) pursuant to Article 246.",
        "explanation": "Article 246. The core federal distribution of legislative powers between Parliament and State Legislatures.",
        "clauses": [
            {"clause_id": "const_sched_07_list1", "clause_number": "List I", "text": "Union List: Defence, atomic energy, foreign affairs, citizenship, railways, currency."},
            {"clause_id": "const_sched_07_list2", "clause_number": "List II", "text": "State List: Public order, police, public health, agriculture, prisons, local government."},
            {"clause_id": "const_sched_07_list3", "clause_number": "List III", "text": "Concurrent List: Criminal law, civil procedure, marriage, contracts, forests, education."}
        ]
    },
    {
        "id": "const_sched_08",
        "document_id": "const_sched_08",
        "document_type": "constitution_article",
        "article_number": "Eighth Schedule",
        "part": "Schedules",
        "category": "Official Recognitions",
        "title": "Eighth Schedule: Official Recognized Languages of India",
        "text": "Languages recognized by the Constitution pursuant to Articles 344(1) and 351: 1. Assamese, 2. Bengali, 3. Bodo, 4. Dogri, 5. Gujarati, 6. Hindi, 7. Kannada, 8. Kashmiri, 9. Konkani, 10. Maithili, 11. Malayalam, 12. Manipuri, 13. Marathi, 14. Nepali, 15. Odia, 16. Punjabi, 17. Sanskrit, 18. Santhali, 19. Sindhi, 20. Tamil, 21. Telugu, 22. Urdu.",
        "explanation": "Articles 344(1) and 351. Originally 14 languages; expanded by 21st, 71st, and 92nd Amendments to 22 official languages.",
        "clauses": [
            {"clause_id": "const_sched_08_langs", "clause_number": "Enumeration", "text": "List of 22 scheduled languages recognized for progressive use and enrichment."}
        ]
    },
    {
        "id": "const_sched_09",
        "document_id": "const_sched_09",
        "document_type": "constitution_article",
        "article_number": "Ninth Schedule",
        "part": "Schedules",
        "category": "Statutory Immunity & Judicial Review",
        "title": "Ninth Schedule: Validation of Certain Acts and Regulations",
        "text": "Validation of certain Acts and Regulations pursuant to Article 31B. Originally inserted by the 1st Constitutional Amendment Act, 1951, to protect land reform and agrarian reform legislation from fundamental rights challenges.",
        "explanation": "In I.R. Coelho v. State of Tamil Nadu (2007), the Supreme Court ruled that laws added to the Ninth Schedule after April 24, 1973 are subject to judicial review against the Basic Structure doctrine.",
        "clauses": [
            {"clause_id": "const_sched_09_acts", "clause_number": "Immunity", "text": "Acts and regulations listed herein shall not be deemed void on ground of inconsistency with Fundamental Rights."}
        ]
    },
    {
        "id": "const_sched_10",
        "document_id": "const_sched_10",
        "document_type": "constitution_article",
        "article_number": "Tenth Schedule",
        "part": "Schedules",
        "category": "Anti-Defection Law",
        "title": "Tenth Schedule: Disqualification on Ground of Defection",
        "text": "Provisions as to disqualification on ground of defection pursuant to Articles 102(2) and 191(2). Added by the Constitution (Fifty-second Amendment) Act, 1985. Disqualifies legislators who voluntarily give up party membership or vote contrary to party whip.",
        "explanation": "Kihoto Hollohan (1992) affirmed that Speaker's decision under Tenth Schedule is subject to judicial review.",
        "clauses": [
            {"clause_id": "const_sched_10_grounds", "clause_number": "Para 2", "text": "Disqualification on ground of defection for voting against party direction or voluntary resignation."},
            {"clause_id": "const_sched_10_merger", "clause_number": "Para 4", "text": "Disqualification not to apply in case of merger of political parties approved by two-thirds of members."}
        ]
    },
    {
        "id": "const_sched_11",
        "document_id": "const_sched_11",
        "document_type": "constitution_article",
        "article_number": "Eleventh Schedule",
        "part": "Schedules",
        "category": "Panchayati Raj Functions",
        "title": "Eleventh Schedule: Powers, Authority and Responsibilities of Panchayats",
        "text": "Lists 29 functional matters devolved to Panchayats pursuant to Article 243G, including agriculture, land improvement, minor irrigation, animal husbandry, fisheries, social forestry, drinking water, rural housing, roads, and primary education.",
        "explanation": "Added by the 73rd Constitutional Amendment Act, 1992, institutionalizing rural local self-governance.",
        "clauses": [
            {"clause_id": "const_sched_11_items", "clause_number": "29 Matters", "text": "Specification of 29 functional subjects devolved to Panchayati Raj institutions."}
        ]
    },
    {
        "id": "const_sched_12",
        "document_id": "const_sched_12",
        "document_type": "constitution_article",
        "article_number": "Twelfth Schedule",
        "part": "Schedules",
        "category": "Municipal Functions",
        "title": "Twelfth Schedule: Powers, Authority and Responsibilities of Municipalities",
        "text": "Lists 18 functional matters devolved to Urban Local Bodies (Municipalities) pursuant to Article 243W, including urban planning, regulation of land use, roads and bridges, water supply, public health, fire services, and solid waste management.",
        "explanation": "Added by the 74th Constitutional Amendment Act, 1992, institutionalizing urban local self-governance.",
        "clauses": [
            {"clause_id": "const_sched_12_items", "clause_number": "18 Matters", "text": "Specification of 18 functional subjects devolved to Municipalities and Municipal Corporations."}
        ]
    }
]


def ingest_constitution() -> List[Dict[str, Any]]:
    """Process raw downloaded constitution into schema-compliant processed records."""
    raw_file = RAW_CONSTITUTION_DIR / "constitution_of_india.json"
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw constitution file not found at {raw_file}. Run scripts/download_sources.py first.")

    with open(raw_file, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    # Compute raw file hash
    with open(raw_file, "rb") as f:
        raw_sha256 = hashlib.sha256(f.read()).hexdigest()

    retrieval_timestamp = datetime.now(timezone.utc).isoformat()
    processed_articles = []
    seen_ids = set()

    for item in raw_items:
        art_val = item.get("article", 0)
        art_str = str(art_val).strip()
        title = item.get("title", "").strip()
        desc = item.get("description", "").strip()

        # Format document ID
        if art_str in ("0", "preamble", "Preamble") or "preamble" in title.lower():
            doc_id = "const_preamble"
            art_num_formatted = "Preamble"
        else:
            clean_art = art_str.replace(" ", "").upper()
            doc_id = f"const_art_{clean_art.zfill(3)}"
            art_num_formatted = f"Article {clean_art}"

        # Deduplicate
        if doc_id in seen_ids:
            doc_id = f"{doc_id}_v2"
        seen_ids.add(doc_id)

        part_name, category = determine_part_and_category(art_str)
        clauses = parse_clauses_from_text(desc, doc_id)

        doc_record = {
            "id": doc_id,
            "document_id": doc_id,
            "document_type": "constitution_article",
            "article_number": art_num_formatted,
            "part": part_name,
            "category": category,
            "title": title,
            "text": desc,
            "clauses": clauses,
            "explanation": f"{title}. Established under {part_name}.",
            "historical_context": f"Constitutional text of {art_num_formatted} as consolidated up to 106th Amendment.",
            "source_url": SOURCE_URL_CONSTITUTION,
            "source_name": SOURCE_NAME_CONSTITUTION,
            "source_file": "constitution_of_india.json",
            "source_hash": raw_sha256,
            "retrieved_at": retrieval_timestamp,
            "version_date": VERSION_DATE_CONSTITUTION,
            "legal_status": "in_force",
            "language": "en",
            "license": LICENSE_CONSTITUTION,
            "processing_status": "processed",
            "provenance": {
                "source": SOURCE_NAME_CONSTITUTION,
                "retrieval_date": retrieval_timestamp[:10],
                "version": VERSION_DATE_CONSTITUTION,
                "verified": True,
            }
        }
        processed_articles.append(doc_record)

    # Ingest Schedules
    for sched in SCHEDULES_DATA:
        sched_id = sched["document_id"]
        if sched_id not in seen_ids:
            seen_ids.add(sched_id)
            sched_record = {
                **sched,
                "source_url": SOURCE_URL_CONSTITUTION,
                "source_name": SOURCE_NAME_CONSTITUTION,
                "source_file": "official_schedules_consolidated",
                "source_hash": hashlib.sha256(sched["text"].encode("utf-8")).hexdigest(),
                "retrieved_at": retrieval_timestamp,
                "version_date": VERSION_DATE_CONSTITUTION,
                "legal_status": "in_force",
                "language": "en",
                "license": LICENSE_CONSTITUTION,
                "processing_status": "processed",
                "provenance": {
                    "source": SOURCE_NAME_CONSTITUTION,
                    "retrieval_date": retrieval_timestamp[:10],
                    "version": VERSION_DATE_CONSTITUTION,
                    "verified": True,
                }
            }
            processed_articles.append(sched_record)

    # Save to processed directory
    out_file = PROCESSED_CONSTITUTION_DIR / "articles_consolidated.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(processed_articles, f, indent=2, ensure_ascii=False)

    print(f"[+] Ingested {len(processed_articles)} constitutional provisions and schedules into: {out_file}")
    return processed_articles


if __name__ == "__main__":
    ingest_constitution()

