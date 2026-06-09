"""Search 珠星三块鱼 via MesoAgent (统一入口，12阶段管线)."""
import sys, os, json, time

engine_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, engine_root)

from src.meso_agent import MesoAgent, MesoConfig

# ── Auto-detect: MCP mode (Reasonix runtime) vs HTTP mode (standalone) ──
_mcp_available = callable(globals().get("tavily_tavily_search"))
_search_mode = "mcp" if _mcp_available else "http"
print(f"   模式: {'🟢 MCP (Reasonix runtime)' if _mcp_available else '🟡 HTTP (standalone)'}")

species_id = "Pseudaspius_hakonensis"  # 珠星三块鱼 (旧名 Tribolodon brandti)

print(f"🔍 MesoAgent.search('{species_id}') — 12 阶段认知搜索")
print("=" * 60)
start = time.time()

# ── 唯一入口：MesoAgent.search() ──
agent = MesoAgent(MesoConfig(mode=_search_mode))
result = agent.search(species_id)

elapsed = time.time() - start

# ── Stats ──
print(f"✅ 搜索完成 ({elapsed:.1f}s)")
print(f"   论文: {len(result.papers)} 篇")
print(f"   新发现: {result.new_papers} 篇")
print(f"   成本: {result.total_cost:.0f} tokens")
print(f"   阶段: {result.phase_count}")
print(f"   停止原因: {result.stop_reason}")
if result.errors:
    print(f"   错误: {len(result.errors)}")
    for e in result.errors[:3]:
        print(f"     - {e}")

# ── 12 阶段日志摘要 ──
if result.meso_log:
    print(f"\n📋 阶段执行日志:")
    for entry in result.meso_log:
        phase = entry.get("phase", "?")
        if phase == "bdi":
            print(f"   [{phase}] 量估算={entry.get('volume_estimate')} full={entry.get('full_pipeline')}")
        elif phase == "search":
            print(f"   [{phase}] 找到 {entry.get('papers_found', 0)} 篇, 运行 {entry.get('phases_run', 0)} 阶段")
        elif phase == "graph_update":
            print(f"   [{phase}] 图谱新增 {entry.get('new_papers_added', 0)} 篇")
        elif phase == "cross_validation":
            print(f"   [{phase}] 独立={entry.get('independence_passed')} 验证={entry.get('verified')}/{entry.get('unique_projects')}项目")
        elif phase == "evolution":
            adaptations = entry.get("adaptations", [])
            if adaptations:
                for a in adaptations:
                    print(f"   [{phase}] {a['param']}: {a['old']} → {a['new']}")
        elif phase == "inference":
            print(f"   [{phase}] 缺口={entry.get('gaps_found')} 追问={entry.get('followup_queries')}")

# ── Papers with credibility ──
print(f"\n📚 论文列表 (含可信度评分):")
for i, p in enumerate(result.papers):
    cs = p.get("credibility_score", p.get("trust_score", 50))
    emoji = "🟢" if cs >= 80 else "🟡" if cs >= 60 else "🟠" if cs >= 40 else "🔴"
    title = p.get("title", "?")[:80]
    author = (p.get("authors", ["?"]) or ["?"])[0]
    year = p.get("year", "?")
    journal = p.get("journal", "?")[:35]
    doi = p.get("doi", "")
    print(f"  [{i+1}] {emoji} {title}")
    print(f"       {author} ({year}) — {journal}")
    if doi:
        print(f"       DOI: {doi}")
    print(f"       评分: {cs} | 来源: {p.get('source', '?')}")

# ── Report (optional) ──
print(f"\n📊 分类报告:")
try:
    from src.report_formatter import generate_quick_report
    report = generate_quick_report(
        result.papers,
        species_name="Pseudaspius hakonensis",
        chinese_name="珠星三块鱼",
        genus="Pseudaspius",
        species_ep="hakonensis",
        detail="expanded",
    )
    print(report)
except ImportError:
    print("   (report_formatter 未加载)")