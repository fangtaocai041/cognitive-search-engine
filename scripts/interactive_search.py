#!/usr/bin/env python3
"""
交互式物种文献检索 — KB-First 两阶段搜索

用法:
  python scripts/interactive_search.py "鳤"              # 交互模式
  python scripts/interactive_search.py "鳤" --auto       # 自动全量
  python scripts/interactive_search.py "鳤" --kb-only    # 仅查知识库
"""
import sys, argparse, time
from pathlib import Path

REASONIX = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REASONIX))


def ask(prompt: str, default: bool = False) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        try:
            ans = input(f"  {prompt} [{hint}]: ").strip().lower()
            if ans in ("y", "yes"): return True
            if ans in ("", "n", "no"): return default if ans == "" else False
        except (EOFError, KeyboardInterrupt): return default


def main():
    parser = argparse.ArgumentParser(description="交互式物种文献检索")
    parser.add_argument("species", help="物种名")
    parser.add_argument("--auto", action="store_true", help="自动全量")
    parser.add_argument("--kb-only", action="store_true", help="仅查知识库")
    parser.add_argument("--max", type=int, default=15)
    args = parser.parse_args()
    species = args.species

    print("\n" + "=" * 60)
    print("  [Phase 1] f项目知识库查询")
    print("=" * 60)

    # KB query
    kb_found = False
    sci_name = species
    try:
        f_db = fish_ecology.parent / "fish-ecology-assistant" / "data" / "species.db"
        if f_db.exists():
            from fish_ecology_assistant.db import KnowledgeDB
            db = KnowledgeDB(f_db)
            info = db.lookup(species)
            if info:
                kb_found = True
                sci_name = info.get("scientific", species)
                print(f"  [OK] {info.get('chinese', '')} ({sci_name})")
                print(f"       科: {info.get('family', '')}")
                print(f"       保护: {info.get('conservation', '')}")
                lits = db.get_literature(info["id"])
                if lits:
                    print(f"       已有文献: {len(lits)}篇")
                    for lit in lits[:3]:
                        print(f"         - {lit.get('year','')} | {lit.get('title','')[:45]}")
            else:
                print(f"  [--] 知识库未收录: {species}")
            db.close()
    except Exception as e:
        print(f"  [!] {e}")

    if args.kb_only:
        return

    if not args.auto:
        go = ask("知识库已收录，是否启动全量搜索?" if kb_found else "是否启动全量搜索?", default=not kb_found)
        if not go:
            print("\n  已取消."); return

    # Search
    print("\n" + "=" * 60)
    print("  [Phase 2] c项目全量搜索")
    print("=" * 60)

    from src.search_coordinator import search
    from src.credibility_scorer import score_paper, credibility_symbol, source_authority_label

    t0 = time.time()
    result = search(sci_name, group="full", limit=args.max)
    elapsed = time.time() - t0

    print(f"  耗时: {elapsed:.1f}s | 论文: {len(result.papers)}篇 | 模式: {result.mode}")

    if not result.papers:
        print("  未找到文献."); return

    # Output by category
    for cat, papers in result.categories.items():
        if not papers: continue
        print(f"\n  [{cat}] ({len(papers)}篇)")
        for p in papers[:5]:
            journal = getattr(p, "journal", "")
            s = score_paper({"journal": journal})
            sym = credibility_symbol(s)
            label = source_authority_label(s)
            title = getattr(p, "title", "")[:60]
            authors = getattr(p, "authors", [])
            a = ", ".join(authors[:3]) if authors else ""
            doi = getattr(p, "doi", "")
            print(f"    {sym} {title}")
            if a: print(f"       {a}")
            print(f"       {journal} | {label}" + (f" | DOI:{doi}" if doi else ""))

    print(f"\n  --- 共 {len(result.papers)} 篇 ---")


if __name__ == "__main__":
    main()
