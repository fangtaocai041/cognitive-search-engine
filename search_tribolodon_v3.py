"""Search 珠星三块鱼 via coordinated_search (HTTP fallback)."""
import sys, os, json

engine_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, engine_root)
os.chdir(engine_root)

# Direct import of coordinated_search with HTTP fallback
from src.unified_search import coordinated_search

result = coordinated_search(
    species_name="珠星三块鱼",
    scientific_name="Tribolodon brandti",
    chinese_name="珠星三块鱼",
    group="standard",
    limit=30,
)

d = result.to_dict() if hasattr(result, "to_dict") else result.__dict__

print(f"TOTAL_PAPERS: {d.get('total_papers', 0)}")
print(f"MODE: {d.get('mode', '?')}")
print(f"VARIANTS: {d.get('all_variants', [])}")
print(f"CATEGORIES: {json.dumps(d.get('categories', {}), ensure_ascii=False, indent=2)}")
print()

papers = d.get("papers", [])
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
