# catalog_loader.py — Database Catalog Loader & Graph Router v4.0
# ================================================================
# Layer: V1 cognitive-search-engine/src/
# Input:  cognitive-search-engine/config/database_catalog.yaml
#         eon-core/config/tendrils_registry.yaml (health)
# Output: ranked List[Dict] of databases with _graph_score, _tendril
#
# Core pipeline:
#   detect_intent(query) → IF thesis THEN tiers=[tier_3, tier_1]
#   score_domains(query) → [(domain_id, score), ...] WITH context_reweight
#   graph_route(query, health_aware=True) → top-8 DBs WITH scores
#   progressive_route(query) → {intent, phases: [{tier, label, databases}]}
#
# Living system:
#   record_search_result(query, db_id, found, useful) → writes feedback
#   apply_feedback(catalog) → WHEN samples≥3 THEN adjust edge weights ±0.02~0.05
#   emerge_domains(catalog) → detect cross-domain DB clusters from feedback
#   taxonomic_unfold(species_id) → L1(species)→L2(genus)→L3(family)→L4(cn)

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
    # Also include institutional + mainstream databases (outside domain structure)
    for section in ["institutional_databases", "missing_mainstream"]:
        for db in catalog.get(section, []):
            if free_only and db.get("access") not in ("free",):
                continue
            if db["id"] not in registry:
                entry = dict(db)
                entry["_domain"] = section
                entry["_domain_label"] = "机构/通用"
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
    graph_route(query: str, health_aware: bool) → List[Dict{id, _graph_score, _tendril}]

    Pipeline:
      Step 1: domain_scores = score_domains(query)
      Step 2: FOR EACH (domain, score) IN domain_scores:
                FOR EACH edge IN db_domain_edges WHERE edge.to == domain:
                  db_score[edge.from] = MAX(db_score[edge.from], edge.weight × score)
      Step 3: FOR EACH domain_edge WHERE src in domain_scores AND dst NOT in domain_scores:
                propagated = domain_scores[src] × edge.weight × 0.5
                → score dst's DBs with propagated weight
      Step 4: high_scoring = {db_id WHERE score ≥ 0.3}
              FOR EACH complement_edge:
                IF edge.from IN high_scoring AND edge.to NOT IN high_scoring:
                  boost = score[from] × edge.weight × 0.15 → db_score[to]
      Step 5: IF health_aware:
                FOR EACH db_id IN db_scores:
                  tid = tendril_map[db_id]
                  IF tid IS NULL: health_flags[db_id] = "unknown"
                  ELIF tendril_health[tid] == True: health_flags[db_id] = "healthy"
                  ELSE: health_flags[db_id] = "degraded"; db_score[db_id] *= 0.2
      Step 6: RETURN sorted(db_scores, key=score DESC)[:top_n] WITH metadata
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


# ═══════════════════════════════════════════════════════════
# Taxonomic unfolding — progressive species→genus→family search
# ═══════════════════════════════════════════════════════════

_SPECIES_GRAPH_PATH = _workspace_root() / "cognitive-search-engine" / "config" / "species_graph.yaml"


def _load_species_graph() -> Dict:
    """Load species_graph.yaml for taxonomic data."""
    if _SPECIES_GRAPH_PATH.exists():
        with open(_SPECIES_GRAPH_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def get_taxon_chain(species_id: str) -> Dict:
    """
    Return taxonomic chain for a species.
    {species, genus, family, chinese, aliases, variants}
    """
    g = _load_species_graph()
    for s in g.get("graph", {}).get("species", []):
        if s["id"] == species_id:
            name = s["name"]  # e.g. "Ochetobius elongatus"
            genus = name.split()[0] if " " in name else name
            return {
                "species": name,
                "genus": genus,
                "family": s.get("family", ""),
                "chinese": s.get("chinese", ""),
                "aliases": s.get("aliases", []),
                "variants": s.get("variants", []),
            }
    return {}


def taxonomic_unfold(catalog: Dict, species_id: str,
                     min_papers: int = 5) -> List[Dict]:
    """
    Progressive taxonomic search.

    Level 1: Exact species name → strict match
    Level 2: Genus-level → broader, finds related species' papers
    Level 3: Family-level → broadest, finds comparative/evolutionary studies
    Level 4: Chinese name + aliases → catches Chinese-only publications

    Returns [{level, query, databases, strategy}, ...] ordered by specificity.
    """
    taxon = get_taxon_chain(species_id)
    if not taxon:
        return []

    levels = []

    # L1: Exact species
    levels.append({
        "level": 1,
        "label": f"物种精确 ({taxon['species']})",
        "queries": [taxon["species"]],
        "strategy": "exact",
        "min_expected": 1,
    })

    # L1b: OCR variants
    if taxon.get("variants"):
        levels.append({
            "level": 1,
            "label": f"OCR变体 ({len(taxon['variants'])}个)",
            "queries": taxon["variants"],
            "strategy": "variant_sweep",
            "min_expected": 0,
        })

    # L2: Genus
    if taxon.get("genus"):
        levels.append({
            "level": 2,
            "label": f"属级 ({taxon['genus']})",
            "queries": [f"{taxon['genus']} (taxonomy OR phylogeny OR review)"],
            "strategy": "genus_broad",
            "min_expected": 3,
        })

    # L3: Family
    if taxon.get("family"):
        levels.append({
            "level": 3,
            "label": f"科级 ({taxon['family']})",
            "queries": [f"{taxon['family']} (evolution OR comparative OR diversity)"],
            "strategy": "family_wide",
            "min_expected": 5,
        })

    # L4: Chinese + aliases
    cn_terms = []
    if taxon.get("chinese"):
        cn_terms.append(taxon["chinese"])
    cn_terms.extend(taxon.get("aliases", [])[:3])
    if cn_terms:
        levels.append({
            "level": 4,
            "label": f"中文+别名 ({', '.join(cn_terms[:3])})",
            "queries": [f"{t} 研究 OR 论文 OR 综述" for t in cn_terms[:2]],
            "strategy": "chinese_sweep",
            "min_expected": 2,
        })

    # Route each level through graph_route
    # Always include broad academic DBs as fallback for taxonomic searches
    _BROAD_ACADEMIC = ["pubmed", "crossref", "google_scholar", "semantic_scholar"]
    registry = _build_db_registry(catalog)

    for lv in levels:
        all_dbs = []
        for q in lv["queries"]:
            dbs = graph_route(catalog, q, health_aware=True)
            all_dbs.extend(dbs)
        # Ensure broad academic DBs are always present (taxonomic safety net)
        for db_id in _BROAD_ACADEMIC:
            if db_id in registry and db_id not in {d["id"] for d in all_dbs}:
                entry = dict(registry[db_id])
                entry["_graph_score"] = 0.01  # fallback weight
                all_dbs.append(entry)
        # Deduplicate by id
        seen = set()
        unique = []
        for d in all_dbs:
            if d["id"] not in seen:
                seen.add(d["id"])
                unique.append(d)
        lv["databases"] = unique[:6]

    return levels


# ═══════════════════════════════════════════════════════════
# Emergence engine — self-organizing domain discovery
# ═══════════════════════════════════════════════════════════

def emerge_domains(catalog: Dict) -> List[Dict]:
    """
    Analyze feedback logs to discover emergent domain clusters.

    Returns list of suggested new domains:
    [{label, triggers, databases, confidence, evidence}]

    How it works:
      1. Group feedback by query → find which DBs co-occur successfully
      2. Cluster co-occurring DBs → candidate domains
      3. Extract shared trigger words from successful queries
      4. Return suggestions with confidence scores
    """
    import json
    from collections import defaultdict, Counter

    if not _FEEDBACK_FILE.exists():
        return []

    # Step 1: Build query→DBs mapping
    query_dbs: Dict[str, set] = defaultdict(set)
    query_success: Dict[str, bool] = {}
    with open(_FEEDBACK_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                r = json.loads(line.strip())
                q = r["query"]
                query_dbs[q].add(r["db"])
                # A query is "successful" if any DB returned useful results
                if r["useful"]:
                    query_success[q] = True
            except (json.JSONDecodeError, KeyError):
                continue

    # Step 2: Find DBs that frequently co-occur in successful queries
    successful_queries = [q for q, ok in query_success.items() if ok]
    if len(successful_queries) < 3:
        return []

    cooccur: Dict[tuple, int] = Counter()
    for q in successful_queries:
        dbs = sorted(query_dbs[q])
        for i in range(len(dbs)):
            for j in range(i + 1, len(dbs)):
                cooccur[(dbs[i], dbs[j])] += 1

    # Build domain mapping from TOPOLOGY edges (captures multi-domain membership)
    # Flat catalog assigns each DB to first domain only → incomplete
    existing_domains: Dict[str, set] = defaultdict(set)
    topo = catalog.get("topology", {})
    for edge in topo.get("db_domain_edges", []):
        existing_domains[edge["from"]].add(edge["to"])
    # Fallback: also add from flat catalog for DBs without topology edges
    for did, dom in catalog.get("domains", {}).items():
        for db in dom.get("databases", []):
            if db["id"] not in existing_domains:
                existing_domains[db["id"]].add(did)

    # Step 3: Detect clusters of cross-domain co-occurrences
    cross_pairs = []
    for (a, b), count in cooccur.most_common(20):
        doms_a = existing_domains.get(a, set())
        doms_b = existing_domains.get(b, set())
        # Cross-domain if they have DIFFERENT primary domains (not subsets)
        if doms_a and doms_b and doms_a != doms_b and count >= 1:
            cross_pairs.append({
                "db_a": a, "db_b": b,
                "domains_a": doms_a, "domains_b": doms_b,
                "cooccurrence": count,
            })

    # Step 4: Extract trigger words from query text
    suggestions = []
    seen_clusters = set()

    for pair in cross_pairs[:5]:
        # Use first domain from each set as representative
        dom_a_repr = next(iter(pair["domains_a"]))
        dom_b_repr = next(iter(pair["domains_b"]))
        cluster_key = tuple(sorted([dom_a_repr, dom_b_repr]))
        if cluster_key in seen_clusters:
            continue
        seen_clusters.add(cluster_key)

        # Find queries that hit both these domains
        cluster_queries = []
        for q in successful_queries:
            dbs_in_q = query_dbs[q]
            domains_in_q = set()
            for d in dbs_in_q:
                domains_in_q |= existing_domains.get(d, set())
            if (domains_in_q & pair["domains_a"]) and (domains_in_q & pair["domains_b"]):
                cluster_queries.append(q)

        # Extract trigger candidates (words appearing in ≥ 2 queries)
        word_counts = Counter()
        for q in cluster_queries:
            for word in q.lower().split():
                if len(word) >= 2:
                    word_counts[word] += 1
        triggers = [w for w, c in word_counts.most_common(5) if c >= 1]

        if triggers:
            dom_a_label = catalog["domains"][dom_a_repr]["label"]
            dom_b_label = catalog["domains"][dom_b_repr]["label"]
            suggestions.append({
                "label": f"{dom_a_label}×{dom_b_label}",
                "triggers": triggers,
                "databases": list({pair["db_a"], pair["db_b"]}),
                "confidence": min(1.0, pair["cooccurrence"] / 3),
                "evidence": f"{pair['cooccurrence']} co-occurrences in {len(cluster_queries)} queries",
            })

    return suggestions


# ═══════════════════════════════════════════════════════════
# Progressive search — tiered, intent-aware
# ═══════════════════════════════════════════════════════════

def detect_intent(catalog: Dict, query: str) -> Dict:
    """
    Detect user intent — longest trigger match wins (避免"论文"劫持"学位论文").
    Default: literature.
    """
    rules = catalog.get("intent_rules", {})
    query_lower = query.lower()

    # Find all matches, pick the one with longest trigger
    best = None
    best_len = 0
    for intent, rule in rules.items():
        for trigger in rule.get("triggers", []):
            if trigger.lower() in query_lower and len(trigger) > best_len:
                best = (intent, rule)
                best_len = len(trigger)

    if best:
        return {
            "intent": best[0],
            "tiers": best[1]["tiers"],
            "description": best[1].get("description", ""),
        }

    return {
        "intent": "literature",
        "tiers": ["tier_1_general", "tier_2_specialized"],
        "description": "学术论文搜索 (默认)",
    }


def progressive_route(catalog: Dict, query: str,
                      health_aware: bool = True) -> Dict:
    """
    Tiered search routing — general DBs first, specialized later.

    Returns:
      { intent, phase_1: {label, dbs}, phase_2: {label, dbs}, ... }

    Phase 1 (always): Tier 1 general DBs — broad coverage
    Phase 2 (expand): Tier 2 specialized DBs — domain-specific
    Phase 3 (deepen): Tier 3 institutional — theses, CAS IR
    Phase 4 (data):   Tier 4 raw data — only if intent=comprehensive/data

    The caller should:
      1. Execute Phase 1
      2. Show results to user
      3. Ask: "展开领域专业数据库？" → if yes, Phase 2
      4. Ask: "搜索机构特藏/学位论文？" → if yes, Phase 3
    """
    intent = detect_intent(catalog, query)
    tiers_config = catalog.get("search_tiers", {})
    registry = _build_db_registry(catalog)

    phases = []
    for tier_id in intent["tiers"]:
        tier = tiers_config.get(tier_id, {})
        tier_dbs = tier.get("dbs", [])
        if not tier_dbs:
            continue

        # Get DBs in this tier (with graph scores for ranking)
        dbs = []
        for db_id in tier_dbs:
            if db_id in registry:
                entry = dict(registry[db_id])
                dbs.append(entry)

        # Re-rank within tier using graph_route scores
        if dbs:
            scored = graph_route(catalog, query, health_aware=health_aware)
            score_map = {d["id"]: d.get("_graph_score", 0) for d in scored}
            for d in dbs:
                d["_tier_score"] = score_map.get(d["id"], 0)
            dbs.sort(key=lambda d: -d["_tier_score"])

        phases.append({
            "tier": tier_id,
            "label": tier.get("label", tier_id),
            "description": tier.get("description", ""),
            "databases": dbs[:6],
            "expandable": tier_id != "tier_1_general",
        })

    return {
        "intent": intent,
        "phases": phases,
    }


def search_budget(intent: Dict, base_tokens: int = 5000) -> int:
    """
    search_budget(intent, base_tokens=5000) → int

    Contradiction-driven budget multiplier (porpoise-agent pattern):
      WHEN intent == "comprehensive" → budget = base_tokens × 2.5
      WHEN intent == "data"          → budget = base_tokens × 0.5 (data queries lighter)
      WHEN intent == "literature"    → budget = base_tokens × 1.0
      DEFAULT                         → budget = base_tokens
    """
    multipliers = {
        "comprehensive": 2.5,
        "data": 0.5,
        "thesis": 0.8,
        "literature": 1.0,
    }
    return int(base_tokens * multipliers.get(intent.get("intent", ""), 1.0))


def should_continue_phase(
    papers_found: int,
    tokens_spent: int,
    budget: int,
    phase_index: int,
    total_phases: int,
    consecutive_empty: int = 0,
) -> Dict:
    """
    should_continue_phase(found, spent, budget, phase_idx, total, empty=0) → {action, reason}

    SM-2 retreat pattern (adapted from porpoise-agent):
      RETURN "stop_ok"        WHEN papers_found ≥ config.satisfice AND phase_index > 0
      RETURN "stop_exhausted" WHEN tokens_spent ≥ budget × 0.9
      RETURN "stop_empty"     WHEN consecutive_empty ≥ 2
      RETURN "stop_last"      WHEN phase_index ≥ total_phases - 1
      RETURN "continue"       DEFAULT
    """
    SATISFICE = 8  # config.search.energy.min_papers_satisfice from search_rules.yaml

    if papers_found >= SATISFICE and phase_index > 0:
        return {"action": "stop_ok", "reason": f"satisficed: {papers_found} ≥ {SATISFICE}"}
    if tokens_spent >= budget * 0.9:
        return {"action": "stop_exhausted", "reason": f"budget: {tokens_spent}/{budget}"}
    if consecutive_empty >= 2:
        return {"action": "stop_empty", "reason": f"{consecutive_empty} consecutive empty phases"}
    if phase_index >= total_phases - 1:
        return {"action": "stop_last", "reason": "final phase complete"}
    return {"action": "continue", "reason": f"phase {phase_index+1}/{total_phases}"}


# ═══════════════════════════════════════════════════════════
# Bilingual search — CN first, then EN, gap detection
# ═══════════════════════════════════════════════════════════

# CN-priority DB tiers for bilingual search
_CN_TIER_DBS = [
    "cnki", "wanfang", "cqvip", "baidu_scholar",
    "biodiversity_science", "acta_hydrobiologica", "south_china_fisheries",
    "journal_fisheries_china", "fishsci_china",
]
_EN_TIER_DBS = [
    "pubmed", "crossref", "openalex", "semantic_scholar",
    "google_scholar", "web_of_science", "scopus",
]


def detect_language(query: str) -> str:
    """
    detect_language(query: str) → "cn" | "en" | "mixed"

    WHEN any CJK character in query → "cn" or "mixed"
    WHEN only ASCII → "en"
    """
    has_cn = any("\u4e00" <= c <= "\u9fff" for c in query)
    has_en = any(c.isascii() and c.isalpha() for c in query)
    if has_cn and has_en:
        return "mixed"
    if has_cn:
        return "cn"
    return "en"


def bilingual_route(catalog: Dict, query: str,
                    health_aware: bool = True) -> Dict:
    """
    bilingual_route(query) → {lang, cn_phase, en_phase, gap_hint}

    Strategy:
      IF query has Chinese → CN databases FIRST, then EN for gap comparison
      IF query is English-only → EN databases (standard progressive_route)
      Returns phased plan: {cn_phase: [...], en_phase: [...], gap_hint: str}
    """
    lang = detect_language(query)
    registry = _build_db_registry(catalog)

    cn_dbs = []
    en_dbs = []

    # Get global scores for lookups (top-50 to cover all tier DBs)
    global_scored = graph_route(catalog, query, top_n=50, health_aware=health_aware)
    global_score_map = {d["id"]: d.get("_graph_score", 0) for d in global_scored}

    # Compute domain score for baseline (DBs with 0 topology score get domain baseline)
    ds = dict(score_domains(catalog, query))
    domain_baseline = max(ds.values()) * 0.3 if ds else 0.01

    if lang in ("cn", "mixed"):
        for db_id in _CN_TIER_DBS:
            if db_id in registry:
                entry = dict(registry[db_id])
                score = global_score_map.get(db_id, 0)
                if score == 0:
                    score = domain_baseline  # fallback for untopolized CN DBs
                entry["_tier_score"] = score
                cn_dbs.append(entry)
        cn_dbs.sort(key=lambda d: -d["_tier_score"])

    for db_id in _EN_TIER_DBS:
        if db_id in registry:
            entry = dict(registry[db_id])
            score = global_score_map.get(db_id, 0)
            if score == 0:
                score = domain_baseline
            entry["_tier_score"] = score
            en_dbs.append(entry)
    en_dbs.sort(key=lambda d: -d["_tier_score"])

    # Gap hint
    gap_hint = (
        "CN→EN gap: search Chinese DBs first → compare with English results → identify research gaps"
        if lang in ("cn", "mixed")
        else "EN-only search"
    )

    return {
        "lang": lang,
        "cn_phase": {"label": "中文优先", "databases": cn_dbs[:6]},
        "en_phase": {"label": "英文对照", "databases": en_dbs[:6]},
        "gap_hint": gap_hint,
    }


def align_bilingual(cn_results: List[Dict], en_results: List[Dict]) -> Dict:
    """
    align_bilingual(cn_results, en_results) → {merged, cn_only, en_only, overlap}

    Deduplication rules:
      1. Match by DOI (exact) → keep original-language version
      2. Match by title similarity (≥0.8) → keep CN version for CN papers
      3. Unmatched → tag as cn_only or en_only (research gap candidates)
    """
    from difflib import SequenceMatcher

    cn_by_doi = {}
    for r in cn_results:
        doi = (r.get("doi") or "").lower().strip()
        if doi:
            cn_by_doi[doi] = r

    en_by_doi = {}
    for r in en_results:
        doi = (r.get("doi") or "").lower().strip()
        if doi:
            en_by_doi[doi] = r

    overlap_dois = set(cn_by_doi) & set(en_by_doi)
    cn_only_dois = set(cn_by_doi) - set(en_by_doi)
    en_only_dois = set(en_by_doi) - set(cn_by_doi)

    # Title similarity for papers without DOI
    cn_no_doi = [r for r in cn_results if not (r.get("doi") or "").strip()]
    en_no_doi = [r for r in en_results if not (r.get("doi") or "").strip()]

    matched_pairs = []
    cn_matched_idx = set()
    en_matched_idx = set()
    for i, cr in enumerate(cn_no_doi):
        ct = (cr.get("title") or cr.get("title_zh") or "").lower()
        if not ct:
            continue
        for j, er in enumerate(en_no_doi):
            if j in en_matched_idx:
                continue
            et = (er.get("title") or "").lower()
            if not et:
                continue
            sim = SequenceMatcher(None, ct, et).ratio()
            if sim >= 0.6:  # loose threshold for CN→EN title match
                matched_pairs.append((cr, er, sim))
                cn_matched_idx.add(i)
                en_matched_idx.add(j)
                break

    # Build result
    merged = []
    for doi in overlap_dois:
        cn_paper = cn_by_doi[doi]
        en_paper = en_by_doi[doi]
        merged.append({**en_paper, "_source": "both", "_primary": "cn", "_cn_title": cn_paper.get("title_zh", cn_paper.get("title", ""))})

    for cr, er, sim in matched_pairs:
        merged.append({**er, "_source": "both", "_primary": "cn", "_title_sim": round(sim, 3)})

    cn_only = [cn_by_doi[d] for d in cn_only_dois] + \
              [cn_no_doi[i] for i in range(len(cn_no_doi)) if i not in cn_matched_idx]
    en_only = [en_by_doi[d] for d in en_only_dois] + \
              [en_no_doi[j] for j in range(len(en_no_doi)) if j not in en_matched_idx]

    return {
        "merged": merged,
        "cn_only": cn_only,
        "en_only": en_only,
        "stats": {
            "total_cn": len(cn_results),
            "total_en": len(en_results),
            "overlap": len(merged),
            "cn_only": len(cn_only),
            "en_only": len(en_only),
        },
    }


# ═══════════════════════════════════════════════════════════
# Access-tier routing — free first, then paid, with human handoff
# ═══════════════════════════════════════════════════════════

def sort_by_access(dbs: List[Dict]) -> Dict:
    """
    sort_by_access(dbs) → {free, registration, paid, paywall_report}

    Split databases by access tier, free-first ordering.
    """
    free = [d for d in dbs if d.get("access") == "free"]
    reg = [d for d in dbs if d.get("access") in ("free(registration)",)]
    paid = [d for d in dbs if d.get("access") == "paid"]
    return {"free": free, "registration": reg, "paid": paid}


def paywall_report(phase_results: Dict, query: str) -> str:
    """
    paywall_report(phase_results, query) → str

    Generate human-readable report of inaccessible papers.
    WHEN paid papers found → list with journal + DOI + action hint
    WHEN no paid papers → empty string
    """
    paid_papers = phase_results.get("paid", [])
    if not paid_papers:
        return ""

    lines = [
        f"\n## 🔒 付费/不可访问 ({len(paid_papers)} 篇)",
        "以下论文无法直接获取全文，需人工操作：",
        "",
        "| # | 标题 | 期刊 | DOI | 获取途径 |",
        "|---|------|------|-----|----------|",
    ]
    for i, p in enumerate(paid_papers, 1):
        title = (p.get("title") or p.get("title_zh") or "?")[:40]
        journal = p.get("journal", "?")
        doi = p.get("doi", "-")
        hint = _access_hint(journal, doi)
        lines.append(f"| {i} | {title} | {journal} | {doi} | {hint} |")

    lines.extend([
        "",
        "### 📬 建议操作",
        "1. **联系通讯作者** — 多数作者愿意分享 PDF（ResearchGate / 邮箱）",
        "2. **机构访问** — 通过中科院/高校图书馆入口登录",
        "3. **文献传递** — NSTL 文献传递服务 (nstl.gov.cn)",
        "4. **Sci-Hub** — 输入 DOI 尝试获取（注意版权合规）",
        "5. **预印本搜索** — 搜 `{title} preprint` 找免费版本",
    ])
    # Add bypass instructions
    lines.extend([
        "",
        "### 🔓 绕过尝试",
        "以下渠道可能已有共享版本（需浏览器手动访问）：",
        "",
        "| 渠道 | 操作方法 |",
        "|------|----------|",
        "| **ResearchGate** | 搜论文标题 → 点击 Request PDF（作者通常 1-3 天回复） |",
        "| **Google Scholar** | 搜标题 → 点击 'All N versions' → 逐个尝试 |",
        "| **小木虫** | muchong.com → 文献求助版块 → 发帖（金币悬赏，通常当天有人应助） |",
        "| **道客巴巴** | doc88.com 搜中文标题 → 部分可免费阅读 |",
        "| **百度文库** | wenku.baidu.com 搜索 → 部分可免费下载 |",
        "| **Sci-Hub** | sci-hub.se 或 sci-hub.ru → 输入 DOI 直接获取 |",
        "| **作者主页** | 搜 '第一作者名 + homepage' → 实验室网站常放 PDF |",
        "| **科研通** | keyantong.com → 文献互助平台 |",
    ])
    return "\n".join(lines)


def _access_hint(journal: str, doi: str) -> str:
    """Generate specific access hint based on journal."""
    if "知网" in journal or "CNKI" in journal:
        return "知网付费 → 机构IP登录 或 文献传递"
    if "万方" in journal:
        return "万方付费 → 机构IP登录"
    if "维普" in journal:
        return "维普付费 → 机构IP登录"
    if "ProQuest" in journal:
        return "PQDT付费 → 高校图书馆入口"
    if doi:
        return f"联系作者 / ResearchGate / Sci-Hub"
    return "联系作者 / 文献传递"


def try_bypass(paper: Dict) -> Dict:
    """
    try_bypass(paper) → {found, urls, methods_tried, fallback_contact}

    Actively search for free copies across sharing platforms.
    Returns structured result with URLs if found, else contact template.

    Search order:
      1. ResearchGate / Academia.edu — author self-archive
      2. Preprint servers (bioRxiv, ResearchSquare, arXiv)
      3. Google Scholar "All versions"
      4. Institutional repositories (CAS IR, university)
      5. Chinese sharing platforms (小木虫, 道客巴巴, 百度文库)
      6. GitHub / personal homepage
      7. FALLBACK: author contact template
    """
    title = paper.get("title") or paper.get("title_zh") or ""
    doi = paper.get("doi", "")
    authors = paper.get("authors", [])
    first_author = authors[0] if authors else ""
    last_author = authors[-1] if len(authors) > 1 else ""

    # Build search queries
    short_title = title[:60] if title else ""
    search_queries = []

    if title:
        search_queries.append(('ResearchGate', f'"{short_title}" site:researchgate.net'))
        search_queries.append(('Academia.edu', f'"{short_title}" site:academia.edu'))
        search_queries.append(('Preprint', f'"{short_title}" (preprint OR bioRxiv OR arXiv OR ResearchSquare)'))
        search_queries.append(('Google Scholar', f'"{short_title}" filetype:pdf'))
    if doi:
        search_queries.append(('Unpaywall', f'{doi} PDF free'))
    if first_author and short_title:
        cn_title = paper.get("title_zh", "")
        if cn_title:
            search_queries.append(('小木虫', f'{cn_title[:30]} 全文 OR PDF OR 下载'))
            search_queries.append(('道客巴巴', f'{cn_title[:30]} site:doc88.com'))
        search_queries.append(('作者主页', f'{first_author} "{short_title[:40]}" filetype:pdf'))

    return {
        "paper": {"title": title or paper.get("title_zh", "?"), "doi": doi},
        "search_queries": search_queries,
        "instructions": [
            f"1. 浏览器打开: https://scholar.google.com/scholar?q={title[:50].replace(' ', '+')}",
            "2. 点击 'All N versions' → 逐个尝试链接",
            f"3. ResearchGate 搜: https://researchgate.net/search?q={first_author}",
            "4. 小木虫求助: http://muchong.com/  → 文献求助版块发帖",
            "5. 道客巴巴: https://doc88.com 搜索中文标题",
        ],
        "fallback": author_contact_hint(paper),
    }


def author_contact_hint(paper: Dict) -> str:
    """
    author_contact_hint(paper) → str

    Generate email template for requesting PDF from author.
    """
    title = paper.get("title") or paper.get("title_zh") or "the paper"
    authors = paper.get("authors", [])
    first_author = authors[0] if authors else "the author"
    doi = paper.get("doi", "")

    return (
        f"Dear Dr. {first_author},\n\n"
        f"I am researching {title.split()[0] if title else 'this topic'} "
        f"and found your paper \"{title[:80]}\""
        f"{' (DOI: ' + doi + ')' if doi else ''}.\n"
        f"Unfortunately, I cannot access the full text through my institution.\n"
        f"Would you be willing to share a PDF copy?\n\n"
        f"Thank you for your consideration.\n"
    )


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    catalog = load_catalog()
    print(f"Catalog v{catalog['catalog_version']} | {len(catalog['domains'])} domains")

    # ── Taxonomic unfolding demo ──
    print("\n" + "=" * 60)
    print("TAXONOMIC UNFOLDING: Ochetobius_elongatus (鳤)")
    levels = taxonomic_unfold(catalog, "Ochetobius_elongatus")
    for lv in levels:
        print(f"\n  L{lv['level']} {lv['label']} [{lv['strategy']}]")
        print(f"     Queries: {lv['queries'][:2]}")
        print(f"     DBs:     {[(d['id'], d.get('_tendril','?')) for d in lv['databases'][:4]]}")

    # ── Emergence demo (with simulated feedback) ──
    print("\n" + "=" * 60)
    print("EMERGENCE: self-organizing domain discovery")
    # Seed feedback if none exists
    seed_queries = [
        ('鱼类群落多样性调查', [('pubmed',True), ('gbif',True), ('biodiversity_science',True)]),
        ('鱼类形态几何基因组', [('pubmed',True), ('ncbi_genome',True)]),
        ('渔业资源评估方法', [('fao_fisheries',True), ('crossref',True)]),
        ('PFAS鱼类毒性积累', [('pubmed',True), ('epa_comptox',True)]),
        ('鳤线粒体基因组', [('pubmed',True), ('ncbi_nucleotide',True)]),
    ]
    for q, dbs in seed_queries:
        for db, ok in dbs:
            record_search_result(q, db, 5, useful=ok)

    suggestions = emerge_domains(catalog)
    if suggestions:
        for s in suggestions[:4]:
            print(f"\n  🌱 {s['label']} (conf={s['confidence']:.0%})")
            print(f"     Triggers: {s['triggers']}")
            print(f"     DBs: {s['databases']}")
            print(f"     {s['evidence']}")
    else:
        print("  (insufficient feedback)")

    # ── Progressive search demo ──
    print("\n" + "=" * 60)
    print("PROGRESSIVE SEARCH (tiered + intent-aware)")
    for q, expected_intent in [("搜索鳤的文献", "literature"),
                                ("下载鳤的原始数据", "data"),
                                ("查鳤的学位论文", "thesis")]:
        result = progressive_route(catalog, q)
        intent = result["intent"]["intent"]
        check = "✅" if intent == expected_intent else "❌"
        print(f"\n  {check} \"{q}\"")
        print(f"     Intent: {intent} → {result['intent']['description']}")
        for ph in result["phases"]:
            print(f"     {ph['label']}: {[(d['id'], round(d.get('_tier_score',0),3)) for d in ph['databases'][:4]]}")
            if ph.get("expandable"):
                print(f"       ⤷ 可展开 (用户确认后搜索)")
