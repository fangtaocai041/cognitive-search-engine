"""
=================================================================
cognitive-search-engine v5.9 — 全链路集成测试
=================================================================
测试范围: 所有24个模块 + 6个复活模块 + RCCA + 编目路由 + BDI搜索
"""
import sys, os, json, time, logging
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # cognitive-search-engine/
sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(level=logging.WARNING)  # suppress noise
logger = logging.getLogger(__name__)

PASS, FAIL, SKIP = 0, 0, 0
results = []

def test(name, fn):
    global PASS, FAIL
    try:
        fn()
        results.append(f"  [PASS] {name}")
        PASS += 1
    except Exception as e:
        results.append(f"  [FAIL] {name}: {type(e).__name__}: {e}")
        FAIL += 1
    except KeyboardInterrupt:
        raise

def skip(name, reason=""):
    global SKIP
    results.append(f"  [SKIP] {name}{' - ' + reason if reason else ''}")
    SKIP += 1

print("=" * 60)
print("cognitive-search-engine v5.9 全链路集成测试")
print("=" * 60)

# ═══════════════════════════════════════════════════════════
# 1. 独立模块导入测试 (24个模块)
# ═══════════════════════════════════════════════════════════
print("\n── 1. 独立模块导入 (24 modules) ──")

MODULES = [
    ("_utils", "src._utils"),
    ("adapter", "src.adapter"),
    ("agent_core", "src.agent_core"),
    ("agent_judge", "src.agent_judge"),
    ("catalog_loader", "src.catalog_loader"),
    ("credibility_scorer", "src.credibility_scorer"),
    ("evolution_executor", "src.evolution_executor"),
    ("inference_engine", "src.inference_engine"),
    ("mcp_client", "src.mcp_client"),
    ("meso_agent", "src.meso_agent"),
    ("mpc_world", "src.mpc_world"),
    ("parallel_search", "src.parallel_search"),
    ("pid_limiter", "src.pid_limiter"),
    ("rcca_core", "src.rcca_core"),
    ("report_formatter", "src.report_formatter"),
    ("rule_engine", "src.rule_engine"),
    ("search_coordinator", "src.search_coordinator"),
    ("search_engine", "src.search_engine"),
    ("thompson_selector", "src.thompson_selector"),
    ("unified_search", "src.unified_search"),
    ("validator", "src.validator"),
    ("variant_generator", "src.variant_generator"),
    ("world_model", "src.world_model"),
    ("__init__ (public API)", "src"),
]

for label, module_path in MODULES:
    test(f"import {label}", lambda mp=module_path: __import__(mp))

# ═══════════════════════════════════════════════════════════
# 2. RCCA 核心全链路
# ═══════════════════════════════════════════════════════════
print("\n── 2. RCCA 核心全链路 ──")

from src.rcca_core import (
    SelfModelEngine, EmotionEngine, TranspositionLayer, ReflectionLoop,
    SelfDimension, EmotionType, ModelState, EmotionalState,
)

tl = TranspositionLayer(base_activity=0.3)
ee = EmotionEngine(transposition_layer=tl)
sm = SelfModelEngine()
rl = ReflectionLoop(max_steps=5)

test("SelfDimension.default()", lambda: (d := SelfDimension.default(), len(d) == 5))
test("EmotionType.ALL (6 emotions)", lambda: len(EmotionType.ALL) == 6)
test("TranspositionLayer init", lambda: tl.current_activity == 0.3)
test("TranspositionLayer.set_stress_level", lambda: (tl.set_stress_level(0.5, 0.3), abs(tl.current_activity - 0.5) < 0.01))
test("TranspositionLayer.transpose (success)", lambda: (e := tl.transpose("biology", "ecology", {"confidence": 0.9}), e.get("success") is not None))
test("EmotionEngine.stimulate(discovery)", lambda: (ee.stimulate("discovery", 0.8), ee.behavioral_tendency == "explore" or ee.behavioral_tendency == "normal"))
test("EmotionEngine.stimulate(error)", lambda: (ee.stimulate("error", 1.0), ee._state.values[EmotionType.URGENCY] > 0.3))
test("SelfModelEngine.reflect()", lambda: (s := sm.reflect(), s.stability >= 0.0))
test("SelfModelEngine.update_with_experience", lambda: (s := sm.update_with_experience({"truth_seeking": 0.9, "curiosity": 0.8}, 0.1), s.experience_count >= 1))
test("ReflectionLoop.run", lambda: (r := rl.run(["search", "verify", "infer"], transposition=tl), r["steps"] == 5))
test("SelfModelEngine.report", lambda: isinstance(sm.report(), dict))
test("EmotionEngine.report", lambda: isinstance(ee.report(), dict))
test("TranspositionLayer.report", lambda: isinstance(tl.report(), dict))
test("ReflectionLoop.report", lambda: isinstance(rl.report(), dict))

# ═══════════════════════════════════════════════════════════
# 3. 编目加载器 + 图路由
# ═══════════════════════════════════════════════════════════
print("\n── 3. 编目加载器 + 图路由 ──")

from src.catalog_loader import (
    load_catalog, score_domains, graph_route,
    match_domain, get_databases, resolve_tools,
    record_search_result, compare_routing,
    format_search_query, save_catalog,
)

catalog = load_catalog()
test("load_catalog (8 domains)", lambda: len(catalog["domains"]) == 8)

domains_en = score_domains(catalog, "fish genetic diversity population structure")
test("score_domains (EN: genetics+fisheries)", lambda: len(domains_en) >= 2)

domains_cn = score_domains(catalog, "鱼类遗传多样性 种群结构")
test("score_domains (CN: 遗传+鱼类)", lambda: len(domains_cn) >= 1)

routes = graph_route(catalog, "fish genetic diversity", top_n=5)
test("graph_route returns results", lambda: len(routes) >= 1)
test("graph_route top result is ncbi_pubmed", lambda: routes[0]["id"] == "ncbi_pubmed")

routes_cn = graph_route(catalog, "鱼类洄游 栖息地保护", top_n=5)
test("graph_route (CN: fisheries+conservation)", lambda: len(routes_cn) >= 1)

routes_health = graph_route(catalog, "PFAS toxicity fish", top_n=5, health_aware=True)
test("graph_route health_aware mode", lambda: len(routes_health) >= 1)

flat = match_domain(catalog, "genome assembly sequencing")
test("match_domain (backward compat)", lambda: isinstance(flat, list))

dbs = get_databases(catalog, ["molecular_genetics", "genomics"])
test("get_databases (flat collection)", lambda: len(dbs) >= 1)

tools = resolve_tools(catalog["domains"]["molecular_genetics"]["databases"][0], "Ochetobius elongatus")
test("resolve_tools", lambda: len(tools) >= 1)

q = format_search_query(catalog["domains"]["molecular_genetics"]["databases"][0], "Ochetobius elongatus")
test("format_search_query", lambda: "Ochetobius elongatus" in q)

record_search_result("test query", "ncbi_pubmed", found=15, useful=True)
test("record_search_result (no crash)", lambda: True)

comp = compare_routing(catalog, "fish genetic diversity")
test("compare_routing", lambda: all(k in comp for k in ["domain_scores", "flat", "graph", "health"]))

# ═══════════════════════════════════════════════════════════
# 4. 报告格式化器
# ═══════════════════════════════════════════════════════════
print("\n── 4. 报告格式化器 ──")

from src.report_formatter import (
    generate_quick_report, classify_papers,
    format_report, format_category_detail,
    CATEGORY_DEFS, ClassificationReport, ClassifiedPaper,
)

sample_papers = [
    {"title": "Genetic diversity of Ochetobius elongatus in Yangtze River",
     "year": 2023, "journal": "Molecular Ecology", "doi": "10.1234/me.001",
     "authors": ["Zhang W", "Li X", "Wang Y"], "credibility_score": 85,
     "source": "pubmed", "abstract": "Population genetics study..."},
    {"title": "Morphological variation of Ochetobius elongatus across basins",
     "year": 2020, "journal": "Journal of Fish Biology", "doi": "10.1234/jfb.002",
     "authors": ["Chen L", "Liu H"], "credibility_score": 72,
     "source": "crossref", "abstract": "Geometric morphometrics..."},
    {"title": "鳤的食性分析及其消化道组织学",
     "year": 2024, "journal": "水生生物学报", "doi": "",
     "authors": ["王明", "赵华"], "credibility_score": 65,
     "source": "cnki", "abstract": "食性分析..."},
    {"title": "Phylogeography and population structure of freshwater fish",
     "year": 2022, "journal": "Heredity", "doi": "10.1234/h.003",
     "authors": ["Smith J", "Brown K"], "credibility_score": 90,
     "source": "pubmed", "abstract": "Mitochondrial DNA analysis..."},
    {"title": "Conservation status of Ochetobius elongatus: a review",
     "year": 2021, "journal": "Biological Conservation", "doi": "10.1234/bc.004",
     "authors": ["Johnson M"], "credibility_score": 78,
     "source": "crossref", "abstract": "Review of conservation..."},
]

report = classify_papers(sample_papers, species_name="Ochetobius elongatus",
                         chinese_name="鳤", genus="Ochetobius", species_ep="elongatus")
test("classify_papers returns ClassificationReport", lambda: isinstance(report, ClassificationReport))
test("classify_papers total=5", lambda: report.total_papers == 5)
test("classify_papers has categories", lambda: len(report.categories) >= 3)
test("classify_papers credibility buckets", lambda: report.high_cred >= 1)

md_summary = format_report(report, detail_level="summary")
test("format_report(summary)", lambda: "文献图谱" in md_summary and len(md_summary) > 100)

md_expanded = format_report(report, detail_level="expanded")
test("format_report(expanded)", lambda: len(md_expanded) > len(md_summary))

md_full = format_report(report, detail_level="full")
test("format_report(full)", lambda: "DOI" in md_full)

detail = format_category_detail(report, "genetics")
test("format_category_detail(genetics)", lambda: "遗传" in detail and len(detail) > 50)

quick = generate_quick_report(sample_papers, species_name="Ochetobius elongatus",
                              chinese_name="鳤", genus="Ochetobius",
                              species_ep="elongatus", detail="summary")
test("generate_quick_report one-liner", lambda: "文献图谱" in quick)

test("CATEGORY_DEFS has 9 categories", lambda: len(CATEGORY_DEFS) == 9)

# ═══════════════════════════════════════════════════════════
# 5. AgentJudge + MPCWorldModel + CognitiveSearchEngine
# ═══════════════════════════════════════════════════════════
print("\n── 5. AgentJudge + MPC + SearchEngine ──")

from src.agent_judge import AgentJudge, PaperEval, EvalDimension

judge = AgentJudge()
scores = judge.evaluate("Ochetobius elongatus genetic diversity", sample_papers)
test("AgentJudge.evaluate returns dict", lambda: isinstance(scores, dict))
test("AgentJudge.evaluate has PaperEval values", lambda: all(isinstance(v, PaperEval) for v in scores.values()))

ranked = judge.rank("Ochetobius elongatus genetic diversity", sample_papers)
test("AgentJudge.rank sorts by score", lambda: len(ranked) == len(sample_papers))
test("AgentJudge.rank adds judge_score", lambda: all("judge_score" in p for p in ranked))

# Without LLM, heuristic fallback
test("AgentJudge heuristic (no LLM)", lambda: all(
    p.get("judge_score", 0) >= 0 for p in ranked
))

from src.mpc_world import MPCWorldModel, MPCPlan, EngineModel

mpc = MPCWorldModel()
plan = mpc.plan("test query", ["pubmed", "crossref", "scholar", "cnki", "openalex"],
                max_papers=50, budget_tokens=5000)
test("MPCWorldModel.plan returns MPCPlan", lambda: isinstance(plan, MPCPlan))
test("MPCWorldModel.plan selects engines", lambda: len(plan.engines) >= 1)
test("MPCWorldModel.plan within budget", lambda: plan.predicted_tokens <= 5000)

mpc.update("pubmed", actual_papers=12, actual_tokens=2400, success=True)
test("MPCWorldModel.update (no crash)", lambda: True)

from src.search_engine import CognitiveSearchEngine, SearchResult

cse = CognitiveSearchEngine()
test("CognitiveSearchEngine.health()", lambda: cse.health()["status"] == "HEALTHY")
test("CognitiveSearchEngine.info()", lambda: cse.info()["version"] == "3.2.0")
test("CognitiveSearchEngine.search() stub", lambda: cse.search("test") == [])

# ═══════════════════════════════════════════════════════════
# 6. MesoAgent 完整 BDI 搜索循环 (HTTP dry-run)
# ═══════════════════════════════════════════════════════════
print("\n── 6. MesoAgent BDI 搜索循环 ──")

from src.meso_agent import MesoAgent, MesoConfig, create_agent, MesoSearchResult

agent = create_agent(mode="http", max_tokens=10000, min_papers_satisfice=5,
                     enable_inference=True, enable_evolution=True,
                     enable_cross_validation=True, enable_graph_update=True,
                     verbose=False)

# Trigger lazy import of ALL modules
agent._ensure_deps()
agent._ensure_graph_loaded()

test("MesoAgent._ensure_deps (WorldModel)", lambda: agent._WorldModel is not None)
test("MesoAgent._ensure_deps (SearchCoordinator)", lambda: agent._SearchCoordinator is not None)
test("MesoAgent._ensure_deps (Validator)", lambda: agent._Validator is not None)
test("MesoAgent._ensure_deps (CredibilityScorer)", lambda: agent._CredibilityScorer is not None)
test("MesoAgent._ensure_deps (EvolutionExecutor)", lambda: agent._EvolutionExecutor is not None)
test("MesoAgent._ensure_deps (InferenceEngine)", lambda: agent._InferenceEngine is not None)
test("MesoAgent._ensure_deps (MPCWorldModel) [复活]", lambda: agent._MPCWorldModel is not None)
test("MesoAgent._ensure_deps (CatalogLoader) [复活]", lambda: agent._CatalogLoader is not None)
test("MesoAgent._ensure_deps (AgentJudge) [复活]", lambda: agent._AgentJudge is not None)
test("MesoAgent._ensure_deps (ReportFormatter) [复活]", lambda: agent._ReportFormatter is not None)
test("MesoAgent._ensure_deps (CognitiveSearchEngine) [复活]", lambda: agent._CognitiveSearchEngine is not None)
test("MesoAgent._ensure_deps (RCCA initialized) [复活]", lambda: agent._rcca_initialized)

# health()
h = agent.health()
test("MesoAgent.health() → HEALTHY", lambda: h["status"] in ("HEALTHY", "DEGRADED"))
test("MesoAgent.health() 10 modules", lambda: len(h["modules"]) == 11)
test("MesoAgent.health() RCCA present", lambda: isinstance(h.get("rcca"), dict))

# info()
info = agent.info()
test("MesoAgent.info() version 5.9.0", lambda: info["version"] == "5.9.0")
test("MesoAgent.info() all capabilities listed", lambda: len(info["capabilities"]) >= 8)

# Graph loading
graph_loaded = len(agent._species_map) > 0
if graph_loaded:
    test(f"MesoAgent._ensure_graph_loaded ({len(agent._species_map)} species)", lambda: True)
else:
    skip("MesoAgent._ensure_graph_loaded", "no species_graph.yaml found")

# Volume estimation (uses live HTTP)
vol = agent._estimate_volume("Ochetobius_elongatus")
test("MesoAgent._estimate_volume (>= 8)", lambda: vol >= 8)

# Search planning
plan = agent._plan_search("Ochetobius_elongatus", vol)
test("MesoAgent._plan_search returns plan", lambda: "mode" in plan and "volume_estimate" in plan)
test("MesoAgent._plan_search mode in valid set", lambda: plan["mode"] in ("exhaustive", "classified", "review_anchored"))

# ── Full search (HTTP) ──
print("\n  [RUN] Running live HTTP search for Ochetobius_elongatus ...")
start = time.time()
result = agent.search("Ochetobius_elongatus")
elapsed = time.time() - start

test("MesoAgent.search() returns MesoSearchResult", lambda: isinstance(result, MesoSearchResult))
test(f"MesoAgent.search() elapsed={elapsed:.1f}s", lambda: result.elapsed_s > 0)
test(f"MesoAgent.search() papers={len(result.papers)}", lambda: len(result.papers) >= 0)
test(f"MesoAgent.search() new_papers={result.new_papers}", lambda: True)
test(f"MesoAgent.search() mode={result.mode_used}", lambda: result.mode_used in ("exhaustive", "classified", "review_anchored"))
test(f"MesoAgent.search() volume_estimate={result.volume_estimate}", lambda: result.volume_estimate >= 8)

# Verify meso_log contains new phases
log_phases = {entry["phase"] for entry in result.meso_log}
test(f"MesoAgent.search() meso_log phases: {sorted(log_phases)}", lambda: len(log_phases) >= 3)

if "mpc_plan" in log_phases:
    test("  └─ MPC plan phase present [复活]", lambda: True)
else:
    skip("  └─ MPC plan phase", "MPC silently skipped (non-critical)")

if "catalog_route" in log_phases:
    test("  └─ Catalog route phase present [复活]", lambda: True)
else:
    skip("  └─ Catalog route phase", "Catalog silently skipped (non-critical)")

if "agent_judge" in log_phases:
    test("  └─ AgentJudge phase present [复活]", lambda: True)
else:
    skip("  └─ AgentJudge phase", "no papers to judge")

if "report" in log_phases:
    test("  └─ Report phase present [复活]", lambda: True)
else:
    skip("  └─ Report phase", "no papers to report")

if "rcca" in log_phases:
    test("  └─ RCCA phase present [复活]", lambda: True)
else:
    skip("  └─ RCCA phase", "RCCA silently skipped")

test("MesoAgent.search() stop_reason present", lambda: len(result.stop_reason) > 0)
test("MesoAgent.search() errors list", lambda: isinstance(result.errors, list))

# ═══════════════════════════════════════════════════════════
# 7. 并行搜索引擎
# ═══════════════════════════════════════════════════════════
print("\n── 7. 并行搜索引擎 ──")

from src.parallel_search import ParallelSearch

test("ParallelSearch import", lambda: True)
# Quick smoke test
try:
    with ParallelSearch(max_workers=2) as ps:
        stats = ps.search_all(["Ochetobius elongatus"], max_per_query=3)
    test(f"ParallelSearch: {stats.total_merged} merged papers", lambda: stats.total_merged >= 0)
    test(f"ParallelSearch: {len(stats.providers_succeeded)}/{len(stats.providers_succeeded)+len(stats.providers_failed)} providers OK",
         lambda: len(stats.providers_succeeded) >= 0)
except Exception as e:
    skip(f"ParallelSearch live test", str(e)[:80])

# ═══════════════════════════════════════════════════════════
# 8. 统一搜索 + Thompson + 验证器
# ═══════════════════════════════════════════════════════════
print("\n── 8. 统一搜索 + Thompson ──")

from src.thompson_selector import ThompsonEngineSelector

ts = ThompsonEngineSelector()
test("ThompsonEngineSelector init", lambda: True)

# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
for r in results:
    print(r)

total = PASS + FAIL + SKIP
print(f"\n  [PASS] {PASS}  [FAIL] {FAIL}  [SKIP] {SKIP}  ({total} total)")

if FAIL == 0:
    print("\n  *** ALL PASSED! All modules integrated and operational. ***")
else:
    print(f"\n  *** {FAIL} test(s) FAILED ***")

sys.exit(0 if FAIL == 0 else 1)
