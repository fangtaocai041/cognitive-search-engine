"""Search 珠星三块鱼 (Tribolodon brandti) via c项目 cognitive engine."""
import sys, os, json

# Ensure the engine root is on sys.path
engine_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, engine_root)

os.chdir(engine_root)

from src.unified_search import coordinated_search as search

result = search("珠星三块鱼", group="full", limit=20)

# Extract structured data
if hasattr(result, "to_dict"):
    d = result.to_dict()
elif hasattr(result, "__dict__"):
    d = result.__dict__
elif isinstance(result, dict):
    d = result
else:
    d = {"raw": str(result)}

print(f"TOTAL_PAPERS: {d.get('total_papers', d.get('total', 0))}")
print(f"MODE: {d.get('mode', '?')}")
print(f"VARIANTS: {d.get('all_variants', [])}")
print(f"CATEGORIES: {json.dumps(d.get('categories', {}), ensure_ascii=False, indent=2)}")
print()

papers = d.get("papers", d.get("results", []))
print(f"PAPERS_FOUND: {len(papers)}")
print()

for i, p in enumerate(papers):
    cat = p.get("category", p.get("paper_category", ""))
    print(f"[{i+1}] [{cat}] {p.get('title', '?')}")
    print(f"    Authors: {p.get('authors', '?')}")
    print(f"    Year: {p.get('year', '?')}  Journal: {p.get('journal', p.get('venue', '?'))}")
    print(f"    DOI: {p.get('doi', '?')}")
    if p.get("credibility_score"):
        print(f"    Credibility: {p.get('credibility_score')}")
    print()

# Also print incidental count / taxonomy warnings
if d.get("incidental_count"):
    print(f"INCIDENTAL: {d['incidental_count']}")
if d.get("taxonomy_warning"):
    print(f"TAXONOMY_WARNING: {d['taxonomy_warning']}")
if d.get("citation_traversal_papers"):
    print(f"CITATION_TRAVERSAL: {d['citation_traversal_papers']} papers")
if d.get("variant_net_papers"):
    print(f"VARIANT_NEW: {d['variant_net_papers']} papers")
