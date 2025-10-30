#!/usr/bin/env python3
import json, sys
fn = sys.argv[1] if len(sys.argv)>1 else "tools/fusion_analysis_ef64.json"
J = json.load(open(fn))
fails = J["failures"]
print("Total failures:", len(fails))
exists = sum(1 for f in fails if any(ed.get("exists") for ed in (f["expected_docs_info"])))
noexist = sum(1 for f in fails if all(not ed.get("exists") for ed in f["expected_docs_info"]))
have_chunks = sum(1 for f in fails if any((ed.get("exists") and ed.get("chunks")) for ed in f["expected_docs_info"]))
print("Failures where expected doc exists in DB:", exists)
print("Failures where expected doc does NOT exist:", noexist)
print("Failures where expected doc exists AND has sample chunks:", have_chunks)
print("\nSample failure details (first 5):")
for f in fails[:5]:
    print("QID:", f["qid"])
    print("Query:", f["query"][:200])
    print("Expected:", f["expected"])
    print("ANN top (sample):", f.get("ann_docs")[:10])
    print("FTS top (sample):", f.get("fts_docs")[:10])
    for ed in f["expected_docs_info"]:
        print("  Expected doc:", ed["doc_id"], "exists:", ed["exists"], "chunks:", len(ed.get("chunks") or []))
    print("-"*40)
