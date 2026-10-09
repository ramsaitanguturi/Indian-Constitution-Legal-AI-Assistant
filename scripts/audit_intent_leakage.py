"""
Audit script to inspect train/test leakage and near-duplicates in intent classification.
"""

import json
from sklearn.model_selection import train_test_split

with open("data/benchmark/classification_queries.json", "r", encoding="utf-8") as f:
    queries = json.load(f)

X = [q["query"] for q in queries]
y = [q["intent"] for q in queries]

X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.15, stratify=y, random_state=42)

def jaccard(s1, s2):
    w1 = set(s1.lower().split())
    w2 = set(s2.lower().split())
    union = w1.union(w2)
    return len(w1.intersection(w2)) / len(union) if union else 0.0

high_sim = []
for q_te, y_te_val in zip(X_te, y_te):
    for q_tr, y_tr_val in zip(X_tr, y_tr):
        sim = jaccard(q_te, q_tr)
        if sim >= 0.60:
            high_sim.append((sim, q_te, q_tr, y_te_val, y_tr_val))

print(f"Total test queries: {len(X_te)}")
print(f"Pairs with Jaccard >= 0.60: {len(high_sim)}")
for sim, q_te, q_tr, y1, y2 in sorted(high_sim, reverse=True)[:10]:
    print(f"  Sim: {sim:.2f} | Test ({y1}): '{q_te}' <-> Train ({y2}): '{q_tr}'")
