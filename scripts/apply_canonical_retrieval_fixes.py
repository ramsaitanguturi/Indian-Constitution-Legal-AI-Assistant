"""
Applies verified canonical document mappings to retrieval benchmarks, relevance labels, and parent store.
Records complete provenance and justifications for audit compliance.
"""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BENCHMARK_DIR = DATA_DIR / "benchmark"
ANNOTATIONS_DIR = DATA_DIR / "annotations"

ARTICLES_PATH = DATA_DIR / "constitution" / "articles.json"
AMENDMENTS_PATH = DATA_DIR / "constitution" / "amendments.json"
LANDMARKS_PATH = DATA_DIR / "judgments" / "supreme_court_landmarks.json"

RETRIEVAL_BENCHMARK_PATH = BENCHMARK_DIR / "retrieval_queries.json"
RELEVANCE_LABELS_PATH = ANNOTATIONS_DIR / "relevance_labels.json"
CANON_LABELS_PATH = ANNOTATIONS_DIR / "relevance_labels_v2_canonicalized.json"
PARENT_STORE_PATH = BASE_DIR / "parent_store.json"


def build_canonical_mapping():
    with open(ARTICLES_PATH, "r", encoding="utf-8") as f:
        articles = json.load(f)
    with open(AMENDMENTS_PATH, "r", encoding="utf-8") as f:
        amendments = json.load(f)
    with open(LANDMARKS_PATH, "r", encoding="utf-8") as f:
        landmarks = json.load(f)

    corpus_articles = {"parent_" + a["document_id"]: a for a in articles}
    corpus_amends = {"parent_" + m["document_id"]: m for m in amendments}
    corpus_judgments = {"parent_" + j["document_id"]: j for j in landmarks}

    all_corpus = set(corpus_articles.keys()) | set(corpus_amends.keys()) | set(corpus_judgments.keys())

    canonical_map = {}
    for p in all_corpus:
        canonical_map[p] = p

    # Articles canonical padding & case rules
    for p in corpus_articles:
        canonical_map[p.lower()] = p
        num_part = p.replace("parent_const_art_", "")
        if num_part.isdigit():
            n = int(num_part)
            canonical_map[f"parent_const_art_{n}"] = p
            canonical_map[f"parent_const_art_{str(n).zfill(3)}"] = p
        else:
            m = re.match(r"^(\d+)([a-zA-Z]+)$", num_part)
            if m:
                n, s = int(m.group(1)), m.group(2)
                canonical_map[f"parent_const_art_{n}{s.lower()}"] = p
                canonical_map[f"parent_const_art_{n}{s.upper()}"] = p
                canonical_map[f"parent_const_art_{str(n).zfill(3)}{s.lower()}"] = p
                canonical_map[f"parent_const_art_{str(n).zfill(3)}{s.upper()}"] = p

    canonical_map["parent_const_preamble"] = "parent_const_preamble"

    # Verified judgment mappings
    case_mappings = {
        # Legacy sample cases -> Production landmark IDs
        "parent_case_kesavananda": "parent_case_sc_kesavananda_1973",
        "parent_case_maneka": "parent_case_sc_maneka_gandhi_1978",
        "parent_case_puttaswamy": "parent_case_sc_puttaswamy_privacy_2017",
        "parent_case_minerva": "parent_case_sc_minerva_mills_1980",
        "parent_case_bommai": "parent_case_sc_sr_bommai_1994",

        # Official SCR Full-Text judgments
        "parent_case_sc_ak_gopalan_1950": "parent_sc_fulltext_1950insc13_1950_1_88_334",
        "parent_case_ak": "parent_sc_fulltext_1950insc13_1950_1_88_334",

        "parent_case_sc_romesh_thappar_1950": "parent_sc_fulltext_1950insc14_1950_1_594_605",
        "parent_case_romesh": "parent_sc_fulltext_1950insc14_1950_1_594_605",

        "parent_case_sc_brij_bhushan_1950": "parent_sc_fulltext_1950insc15_1950_1_605_620",
        "parent_case_brij": "parent_sc_fulltext_1950insc15_1950_1_605_620",

        "parent_case_sc_champakam_dorairajan_1951": "parent_sc_fulltext_1951insc26_1951_1_525_533",
        "parent_case_champakam": "parent_sc_fulltext_1951insc26_1951_1_525_533",

        "parent_case_sc_shankari_prasad_1951": "parent_sc_fulltext_1951insc47_1952_1_89_109",
        "parent_case_shankari": "parent_sc_fulltext_1951insc47_1952_1_89_109",

        # Landmark cases with naming / citation discrepancies
        "parent_case_sc_adr_voter_rights_2002": "parent_case_sc_adr_2002",
        "parent_case_adr": "parent_case_sc_adr_2002",

        "parent_case_sc_bennett_coleman_1972": "parent_case_sc_bennett_coleman_1973",
        "parent_case_bennett": "parent_case_sc_bennett_coleman_1973",

        "parent_case_sc_ep_royappa_1974": "parent_case_sc_royappa_1974",
        "parent_case_ep": "parent_case_sc_royappa_1974",

        "parent_case_sc_kharak_singh_1962": "parent_case_sc_kharak_singh_1963",
        "parent_case_kharak": "parent_case_sc_kharak_singh_1963",

        "parent_case_sc_m_nagaraj_2006": "parent_case_sc_nagaraj_2006",
        "parent_case_m": "parent_case_sc_nagaraj_2006",

        "parent_case_sc_njac_fourth_judges_2015": "parent_case_sc_fourth_judges_njac_2015",
        "parent_case_njac": "parent_case_sc_fourth_judges_njac_2015",

        "parent_case_sc_scara_second_judges_1993": "parent_case_sc_second_judges_1993",
        "parent_case_scara": "parent_case_sc_second_judges_1993",

        "parent_case_sc_sp_gupta_1981": "parent_case_sc_first_judges_1981",
        "parent_case_sp": "parent_case_sc_first_judges_1981",

        # Short aliases
        "parent_case_adm": "parent_case_sc_adm_jabalpur_1976",
        "parent_case_anuradha": "parent_case_sc_anuradha_bhasin_2020",
        "parent_case_aruna": "parent_case_sc_aruna_shanbaug_2011",
        "parent_case_bandhua": "parent_case_sc_bandhua_mukti_1984",
        "parent_case_bijoe": "parent_case_sc_bijoe_emmanuel_1986",
        "parent_case_common": "parent_case_sc_common_cause_2018",
        "parent_case_dk": "parent_case_sc_dk_basu_1997",
        "parent_case_francis": "parent_case_sc_francis_coralie_1981",
        "parent_case_golak": "parent_case_sc_golak_nath_1967",
        "parent_case_indira": "parent_case_sc_indira_gandhi_1975",
        "parent_case_indra": "parent_case_sc_indra_sawhney_1992",
        "parent_case_ir": "parent_case_sc_ir_coelho_2007",
        "parent_case_jallikattu": "parent_case_sc_jallikattu_2014",
        "parent_case_janhit": "parent_case_sc_janhit_abhiyan_2022",
        "parent_case_jarnail": "parent_case_sc_jarnail_singh_2018",
        "parent_case_joseph": "parent_case_sc_joseph_shine_2018",
        "parent_case_kihoto": "parent_case_sc_kihoto_hollohan_1992",
        "parent_case_lily": "parent_case_sc_lily_thomas_2013",
        "parent_case_navtej": "parent_case_sc_navtej_johar_2018",
        "parent_case_nct": "parent_case_sc_nct_delhi_2018",
        "parent_case_olga": "parent_case_sc_olga_tellis_1985",
        "parent_case_pucl": "parent_case_sc_pucl_nota_2013",
        "parent_case_sabarimala": "parent_case_sc_sabarimala_2018",
        "parent_case_sajjan": "parent_case_sc_sajjan_singh_1965",
        "parent_case_sakal": "parent_case_sc_sakal_papers_1962",
        "parent_case_selvi": "parent_case_sc_selvi_2010",
        "parent_case_shayara": "parent_case_sc_shayara_bano_2017",
        "parent_case_shirur": "parent_case_sc_shirur_mutt_1954",
        "parent_case_shreya": "parent_case_sc_shreya_singhal_2015",
        "parent_case_sr": "parent_case_sc_sr_bommai_1994",
        "parent_case_sunil": "parent_case_sc_sunil_batra_1978",
        "parent_case_third": "parent_case_sc_third_judges_1998",
        "parent_case_vishaka": "parent_case_sc_vishaka_1997",
        "parent_case_waman": "parent_case_sc_waman_rao_1981",
    }
    canonical_map.update(case_mappings)

    return canonical_map, all_corpus


def apply_fixes():
    canonical_map, all_corpus = build_canonical_mapping()

    with open(RETRIEVAL_BENCHMARK_PATH, "r", encoding="utf-8") as f:
        queries = json.load(f)
    with open(RELEVANCE_LABELS_PATH, "r", encoding="utf-8") as f:
        relevance_labels = json.load(f)
    with open(PARENT_STORE_PATH, "r", encoding="utf-8") as f:
        parent_store = json.load(f)

    audit_records = []
    updated_queries = []
    updated_labels = {}

    for q in queries:
        qid = q["query_id"]
        orig_docs = q.get("relevant_documents", [])
        orig_labels = relevance_labels.get(qid, {})

        # Map relevant documents
        new_docs = []
        for d in orig_docs:
            canon_d = canonical_map.get(d, d)
            if canon_d not in new_docs:
                new_docs.append(canon_d)

        # Build new graded relevance labels
        new_labels_dict = {}
        # First assign scores based on original labels mapped to canonical
        for d, score in orig_labels.items():
            canon_d = canonical_map.get(d, d)
            new_labels_dict[canon_d] = max(new_labels_dict.get(canon_d, 0.0), float(score))

        # Ensure all new_docs have a graded relevance score
        for idx, d in enumerate(new_docs):
            if d not in new_labels_dict:
                new_labels_dict[d] = 2.0 if idx == 0 else 1.0

        # Create updated query record
        q_copy = dict(q)
        q_copy["relevant_documents"] = new_docs
        updated_queries.append(q_copy)
        updated_labels[qid] = new_labels_dict

        # Audit if changes occurred
        if orig_docs != new_docs or orig_labels != new_labels_dict:
            audit_records.append({
                "query_id": qid,
                "query": q["query"],
                "original_relevant_docs": orig_docs,
                "canonical_relevant_docs": new_docs,
                "original_labels": orig_labels,
                "canonical_labels": new_labels_dict,
                "reason": (
                    "Resolved leading-zero / case / alias discrepancies and unified "
                    "redundant references into canonical corpus parent document IDs."
                )
            })

    # Update parent_store alias entries
    updated_parent_store = dict(parent_store)
    alias_count = 0
    for alias, canon in canonical_map.items():
        if canon in updated_parent_store:
            canon_entry = updated_parent_store[canon]
            # Ensure alias points to canonical entry with canonical parent_id
            if alias not in updated_parent_store or updated_parent_store[alias].get("parent_id") != canon:
                entry_copy = dict(canon_entry)
                entry_copy["parent_id"] = canon
                entry_copy["canonical_id"] = canon
                updated_parent_store[alias] = entry_copy
                alias_count += 1

    print(f"Total benchmark queries: {len(updated_queries)}")
    print(f"Queries with relevance label modifications: {len(audit_records)}")
    print(f"Parent store aliases updated/registered: {alias_count}")

    # Write files
    with open(RETRIEVAL_BENCHMARK_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_queries, f, indent=2)
    with open(RELEVANCE_LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_labels, f, indent=2)
    with open(CANON_LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_labels, f, indent=2)
    with open(PARENT_STORE_PATH, "w", encoding="utf-8") as f:
        json.dump(updated_parent_store, f, indent=2)

    # Save audit log
    audit_file = BASE_DIR / "evaluation" / "results" / "relevance_label_audit_log.json"
    audit_file.parent.mkdir(parents=True, exist_ok=True)
    with open(audit_file, "w", encoding="utf-8") as f:
        json.dump(audit_records, f, indent=2)
    print(f"Saved detailed audit log to {audit_file}")

    return audit_records


if __name__ == "__main__":
    apply_fixes()

