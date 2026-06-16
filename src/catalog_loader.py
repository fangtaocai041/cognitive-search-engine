# catalog_loader.py — Database Catalog Loader & Graph Router (v3.0)
# =================================================================
# Lives in cognitive-search-engine/src/ (V1 search layer).
# Catalog: cognitive-search-engine/config/database_catalog.yaml
# Tendrils: eon-core/config/tendrils_registry.yaml
#
# Usage:
#   from catalog_loader import load_catalog, score_domains, graph_route
#   catalog = load_catalog()
#   dbs = graph_route(catalog, "search query", health_aware=True)

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════
# Path resolution
# ═══════════════════════════════════════════════════════════

def _workspace_root() -> Path:
    """Resolve D:\\Reasonix\\ from any project."""
    return Path(__file__).resolve().parent.parent.parent


def _catalog_path() -> Path:
    path = _workspace_root() / "cognitive-search-engine" / "config" / "database_catalog.yaml"
    if path.exists():
        return path
    raise FileNotFoundError(f"Catalog not found at {path}")


def _tendrils_path() -> Optional[Path]:
    path = _workspace_root() / "eon-core" / "config" / "tendrils_registry.yaml"
    return path if path.exists() else None


# ═══════════════════════════════════════════════════════════
# I/O
# ═══════════════════════════════════════════════════════════

def load_catalog() -> Dict:
    """Load the full database catalog."""
    with open(_catalog_path(), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_tendril_health() -> Dict[str, bool]:
    """Load tendril health from eon-core. Returns {tendril_id: is_healthy}."""
    path = _tendrils_path()
    if not path:
        return {}
    try:
        with open(path, encoding="utf-8") as f:
            tendrils = yaml.safe_load(f)
        return {t["id"]: t.get("status", "healthy") == "healthy"
                for t in tendrils.get("tendrils", [])}
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════
# Domain scoring (v2.0 — weighted, context-aware)
# ═══════════════════════════════════════════════════════════

def score_domains(catalog: Dict, query: str) -> List[Tuple[str, float]]:
    """
    Weighted domain matching. Returns [(domain_id, score), ...] sorted desc.

    Algorithm:
      - Each trigger hit = 1/N where N = total triggers in domain
      - Context rules reweight overlapping domains
      - Built-in: generic subjects (fisheries) penalized vs deep domains
    """
    query_lower = query.lower()
    raw: Dict[str, float] = {}

    for did, dom in catalog.get("domains", {}).items():
        triggers = dom.get("triggers", [])
        if not triggers:
            continue
        hits = sum(1 for t in triggers if t.lower() in query_lower)
        if hits:
            raw[did] = hits / len(triggers)

    if not raw:
        return []

    return sorted(_reweight(raw, catalog).items(), key=lambda x: -x[1])


def _reweight(scores: Dict[str, float], catalog: Dict) -> Dict[str, float]:
    """Apply context_rules + built-in heuristics."""
    s = dict(scores)
    rules = catalog.get("topology", {}).get("context_rules", [])

    for r in rules:
        conds = r.get("if", [])
        target = r.get("target", "")
        if not (all(c in s for c in conds) and target in s):
            continue
        if r["type"] == "boost":
            s[target] *= r.get("factor", 1.5)
        elif r["type"] == "suppress":
            s[target] *= r.get("factor", 0.3)

    # Built-in: deep-domain dominance over fisheries
    deep = {"molecular_genetics", "toxicology", "biomedical", "morphology"}
    deep_hits = [d for d in deep if d in s]
    if "fisheries_ichthyology" in s and deep_hits:
        if s["fisheries_ichthyology"] <= max(s[d] for d in deep_hits) * 0.33:
            s["fisheries_ichthyology"] *= 0.4

    return s


# ═══════════════════════════════════════════════════════════
# DB registry (shared between flat + graph routing)
# ═══════════════════════════════════════════════════════════

def _build_db_registry(catalog: Dict, free_only: bool = True) -> Dict[str, Dict]:
    """Build {db_id: {metadata, _domain, _domain_label}} index."""
    registry: Dict[str, Dict] = {}
    for did, dom in catalog.get("domains", {}).items():
        for db in dom.get("databases", []):
            if free_only and db.get("access") not in ("free",):
                continue
            if db["id"] not in registry:
                entry = dict(db)
                entry["_domain"] = did
                entry["_domain_label"] = dom.get("label", did)
                registry[db["id"]] = entry
    return registry


# ═══════════════════════════════════════════════════════════
# Flat routing (backward-compatible)
# ═══════════════════════════════════════════════════════════

def match_domain(catalog: Dict, query: str) -> List[str]:
    """DEPRECATED — use score_domains(). Returns domain IDs with score > 0."""
    return [d for d, s in score_domains(catalog, query)]


def get_databases(catalog: Dict, domain_ids: List[str],
                  free_only: bool = True, max_total: int = 10) -> List[Dict]:
    """Flat database collection (no graph, no weights)."""
    registry = _build_db_registry(catalog, free_only)
    result = []
    for did in domain_ids:
        dom = catalog.get("domains", {}).get(did, {})
        for db in dom.get("databases", []):
            if free_only and db.get("access") not in ("free",):
                continue
            if db["id"] not in {d["id"] for d in result}:
                db_copy = dict(db)
                db_copy["_domain"] = did
                db_copy["_domain_label"] = dom.get("label", did)
                result.append(db_copy)
    return result[:max_total]


# ═══════════════════════════════════════════════════════════
# Graph routing (v3.0 — weighted + health-aware)
# ═══════════════════════════════════════════════════════════

def graph_route(catalog: Dict, query: str, top_n: int = 8,
                health_aware: bool = False) -> List[Dict]:
    """
    Graph-topology-aware weighted routing.

    Pipeline:
      1. score_domains(query) → weighted domain scores
      2. For each domain, db_score = db_domain_edge.weight × domain_score
      3. Cross-domain propagation (decay 0.5)
      4. Complementarity boost (factor 0.15)
      5. Tendril health filter (if health_aware=True)
      6. Return top-N ranked DBs with metadata
    """
    topo = catalog.get("topology", {})
    if not topo:
        return get_databases(catalog, match_domain(catalog, query))

    domain_scores = dict(score_domains(catalog, query))
    if not domain_scores:
        return get_databases(catalog, [], free_only=True)[:top_n]

    db_edges = topo.get("db_domain_edges", [])
    dom_edges = topo.get("domain_edges", [])
    comp_edges = topo.get("db_complement_edges", [])

    # Step 1: Direct scoring
    db_scores: Dict[str, float] = {}
    for e in db_edges:
        if e["to"] in domain_scores:
            db_scores[e["from"]] = max(
                db_scores.get(e["from"], 0),
                e["weight"] * domain_scores[e["to"]],
            )

    # Step 2: Cross-domain propagation
    decay = 0.5
    for e in dom_edges:
        src, dst = e["from"], e["to"]
        if src in domain_scores and dst not in domain_scores:
            propagated = domain_scores[src] * e["weight"] * decay
            for de in db_edges:
                if de["to"] == dst:
                    db_scores[de["from"]] = max(
                        db_scores.get(de["from"], 0),
                        de["weight"] * propagated,
                    )

    # Step 3: Complementarity
    boost_threshold, boost_factor = 0.3, 0.15
    high = {db for db, s in db_scores.items() if s >= boost_threshold}
    for e in comp_edges:
        for a, b in [(e["from"], e["to"]), (e["to"], e["from"])]:
            if a in high and b not in high:
                db_scores[b] = max(db_scores.get(b, 0),
                                   db_scores[a] * e["weight"] * boost_factor)

    # Step 4: Tendril health
    health_flags: Dict[str, str] = {}
    if health_aware:
        th = load_tendril_health()
        tm = topo.get("tendril_map", {})
        penalty = topo.get("tendril_unhealthy_penalty", 0.2)
        for db_id in list(db_scores):
            tid = tm.get(db_id)
            if tid is None:
                health_flags[db_id] = "unknown"
            elif th.get(tid, True):
                health_flags[db_id] = "healthy"
            else:
                health_flags[db_id] = "degraded"
                db_scores[db_id] *= penalty

    # Step 5: Build result
    registry = _build_db_registry(catalog)
    ranked = []
    for db_id, score in sorted(db_scores.items(), key=lambda x: -x[1]):
        if db_id in registry:
            entry = registry[db_id]
            entry["_graph_score"] = round(score, 3)
            if health_aware and db_id in health_flags:
                entry["_tendril"] = health_flags[db_id]
            ranked.append(entry)

    return ranked[:top_n]


# ═══════════════════════════════════════════════════════════
# Tool resolution
# ═══════════════════════════════════════════════════════════

TOOL_MAP = {
    "ncbi_ncbi_esearch":           lambda q: {"tool": "ncbi_ncbi_esearch", "params": {"query": q, "maxResults": 20}},
    "ncbi_ncbi_efetch":            lambda q: {"tool": "ncbi_ncbi_efetch", "params": {"pmid": "FROM_ESEARCH"}},
    "scholar_search_literature_graph": lambda q: {"tool": "scholar_search_literature_graph", "params": {"query": q, "limit": 10}},
    "scholar_search_google_scholar_key_words": lambda q: {"tool": "scholar_search_google_scholar_key_words", "params": {"query": q, "num_results": 10}},
    "article_search_literature":   lambda q: {"tool": "article_search_literature", "params": {"keyword": q, "max_results": 10}},
    "article_get_article_details": lambda q: {"tool": "article_get_article_details", "params": {"pmcid": "FROM_SEARCH"}},
    "tavily_tavily_search":        lambda q: {"tool": "tavily_tavily_search", "params": {"query": q, "max_results": 5}},
    "web_search":                  lambda q: {"tool": "web_search", "params": {"query": q, "topK": 5}},
    "github_search_code":          lambda q: {"tool": "github_search_code", "params": {"q": q}},
    "github_search_repositories":  lambda q: {"tool": "github_search_repositories", "params": {"query": q}},
}


def format_search_query(db: Dict, user_query: str) -> str:
    template = db.get("search_template", "{keyword}")
    return template.replace("{keyword}", user_query).replace("{species_name}", user_query)


def resolve_tools(db: Dict, query: str) -> List[Dict]:
    """Return concrete tool calls for a database."""
    tools = db.get("search_tools", ["web_search"])
    formatted = format_search_query(db, query)
    resolved = []
    for t in tools:
        factory = TOOL_MAP.get(t)
        if factory:
            resolved.append(factory(formatted if t == "web_search" else query))
    return resolved


# ═══════════════════════════════════════════════════════════
# Living system: search feedback → weight auto-update
# ═══════════════════════════════════════════════════════════

_FEEDBACK_FILE = _workspace_root() / "logs" / "catalog_feedback.jsonl"


def record_search_result(query: str, db_id: str, found: int,
                         useful: bool = True) -> None:
    """
    Log search result for later weight tuning.
    Appends one JSON line to logs/catalog_feedback.jsonl.
    """
    import json, datetime
    _FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": datetime.datetime.now().isoformat(),
        "query": query,
        "db": db_id,
        "found": found,
        "useful": useful,
    }
    with open(_FEEDBACK_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def apply_feedback(catalog: Dict, min_samples: int = 3) -> Dict:
    """
    Adjust db_domain_edge weights based on logged search feedback.
    - If a DB consistently returns useful results → edge weight +0.02
    - If a DB consistently returns nothing → edge weight -0.05
    Only applied when ≥ min_samples logged for that DB+domain pair.
    Returns updated catalog (caller should save).
    """
    import json
    if not _FEEDBACK_FILE.exists():
        return catalog

    # Aggregate feedback
    stats: Dict[str, Dict[str, list]] = {}  # db_id → {domain: [bool]}
    with open(_FEEDBACK_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line.strip())
                db = r["db"]
                if db not in stats:
                    stats[db] = {}
                # Guess domain from query via scoring
                ds = dict(score_domains(catalog, r["query"]))
                top_domain = max(ds, key=ds.get) if ds else None
                if top_domain:
                    stats[db].setdefault(top_domain, []).append(r["useful"])
            except (json.JSONDecodeError, KeyError):
                continue

    # Apply adjustments
    topo = catalog.setdefault("topology", {})
    edges = topo.setdefault("db_domain_edges", [])
    adjustments = 0

    for edge in edges:
        db, dom = edge["from"], edge["to"]
        signals = stats.get(db, {}).get(dom, [])
        if len(signals) < min_samples:
            continue
        success_rate = sum(signals) / len(signals)
        if success_rate >= 0.7:
            edge["weight"] = min(1.0, round(edge["weight"] + 0.02, 3))
            adjustments += 1
        elif success_rate <= 0.2:
            edge["weight"] = max(0.1, round(edge["weight"] - 0.05, 3))
            adjustments += 1

    if adjustments > 0:
        catalog["last_updated"] = max(
            r["ts"] for r in [json.loads(l) for l in
            open(_FEEDBACK_FILE, encoding="utf-8").readlines() if l.strip()]
            if isinstance(r, dict)
        )

    return catalog


def save_catalog(catalog: Dict) -> None:
    """Persist catalog back to YAML (with backup)."""
    import shutil
    original = _catalog_path()
    backup = original.with_suffix(".yaml.bak")
    shutil.copy(original, backup)
    with open(original, "w", encoding="utf-8") as f:
        yaml.dump(catalog, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False)
    backup.unlink()


# ═══════════════════════════════════════════════════════════
# Diagnostic
# ═══════════════════════════════════════════════════════════

def compare_routing(catalog: Dict, query: str) -> Dict:
    """Compare flat vs graph vs health-aware routing."""
    ds = score_domains(catalog, query)
    flat_domains = [d for d, _ in ds]
    return {
        "query": query,
        "domain_scores": [(d, round(s, 3)) for d, s in ds],
        "flat": [(d["id"], d.get("_domain_label", ""))
                 for d in get_databases(catalog, flat_domains)],
        "graph": [(d["id"], d.get("_graph_score", 0))
                  for d in graph_route(catalog, query)],
        "health": [(d["id"], d.get("_tendril", "?"), d.get("_graph_score", 0))
                   for d in graph_route(catalog, query, health_aware=True)],
    }


if __name__ == "__main__":
    catalog = load_catalog()
    print(f"Catalog v{catalog['catalog_version']} | {len(catalog['domains'])} domains")

    for q in ["搜索鳤的遗传多样性", "PFAS对鱼类的毒性", "深度学习图像识别"]:
        r = compare_routing(catalog, q)
        print(f"\n{'—'*50}\n{q}")
        print(f"  Domains: {r['domain_scores']}")
        print(f"  Graph:   {[(d, s) for d, s in r['graph']]}")
        print(f"  +Health: {[(d, t, s) for d, t, s in r['health']]}")
