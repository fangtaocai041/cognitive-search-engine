        taxonomy_warning=taxonomy_warning,
    )


# ═══════════════════════════════════════════════════════
# §8 KB-First 两阶段搜索 (f项目知识库 → c项目全量搜索)
# ═══════════════════════════════════════════════════════

@dataclass
class KbFirstSearchResult:
    """Result from search_with_kb_first() — wraps both stages.

    Stage 1 (kb_check): KB lookup result from f项目.
    Stage 2 (full_search): Only populated if user chose to continue.
    """
    stage: str                              # "kb_check" | "full_search"
    species_name: str                       # Original query
    kb_found: bool                          # Whether species found in f项目 KB
    kb_summary: str = ""                    # Human-readable KB result summary
    kb_recommendation: str = ""             # "stay_in_kb" | "continue_to_c"
    kb_data: Dict[str, Any] = field(default_factory=dict)  # Raw KB data
    full_search: Optional[CoordinatedSearchResult] = None  # Stage 2 result
    suggested_next: str = ""                # "ask_user" | "done"
    all_candidates: List[Dict[str, Any]] = field(default_factory=list)

    def ask_user_prompt(self) -> str:
        """Generate the user-facing prompt asking whether to continue."""
        if self.kb_found:
            return (
                f"📚 f项目知识库已收录「{self.species_name}」。\n\n"
                f"{self.kb_summary}\n\n"
                f"───\n"
                f"**是否继续？**\n"
                f"- **留步**：仅使用知识库数据（已足够）\n"
                f"- **继续搜索**：启动 c项目全量文献搜索（多引擎并行 + 引用回溯 + 变体安全网）"
            )
        else:
            candidates = ""
            if self.all_candidates:
                top = self.all_candidates[:3]
                candidates = "\n可能近缘种: " + ", ".join(
                    f"{c['chinese']}({c['scientific']})" for c in top
                )
            return (
                f"🔍 f项目知识库未收录「{self.species_name}」。{candidates}\n\n"
                f"**是否启动 c项目全量文献搜索？** (多引擎并行 + 引用回溯 + 变体安全网)"
            )


def _load_fish_kb() -> Any:
    """Lazy-load FishEcologyOrchestrator from fish-ecology-assistant.

    Returns the orchestrator instance, or None if the f项目 is unavailable.
    Uses cross-project import path: fish-ecology-assistant/src/orchestrator.py.
    """
    try:
        import sys
        from pathlib import Path

        # Find fish-ecology-assistant root relative to cognitive-search-engine
        cognitive_root = Path(__file__).resolve().parent.parent
        fish_root = cognitive_root.parent / "fish-ecology-assistant"
        fish_src = fish_root / "src"

        if not fish_src.is_dir():
            return None

        fish_str = str(fish_root)
        if fish_str not in sys.path:
            sys.path.insert(0, fish_str)

        # Import (handle src package namespace collision)
        import importlib
        _mod_name = f"_fish_orch_{id(fish_str).__abs__() % 10000}"
        spec = importlib.util.spec_from_file_location(
            _mod_name, str(fish_src / "orchestrator.py"))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[_mod_name] = mod
            spec.loader.exec_module(mod)
            factory = getattr(mod, "get_orchestrator", None)
            if factory:
                return factory()
        return None
    except Exception:
        return None


def search_with_kb_first(
    species_name: str,
    kb_result: Optional[Dict[str, Any]] = None,
    group: str = "standard",
    limit: int = 10,
    on_result: callable = None,
) -> KbFirstSearchResult:
    """KB-First 两阶段搜索 — 先查 f项目知识库，再决定是否启动 c项目。

    This is the RECOMMENDED entry point for species literature search.
    It implements the two-stage workflow:

      Stage 1 (kb_check): Query fish-ecology-assistant knowledge base.
        → Returns KbFirstSearchResult with stage="kb_check".
        → Caller presents ask_user_prompt() to user.

      Stage 2 (full_search): If user says "continue", call
        continue_full_search() → runs coordinated_search().

    Usage:
      # Stage 1: KB check
      result = search_with_kb_first("珠星三块鱼")
      if result.stage == "kb_check":
          print(result.ask_user_prompt())
          # ... wait for user input ...

      # Stage 2: Full search (only if user says continue)
      result = continue_full_search(result, group="full")

    Args:
        species_name: Chinese name or scientific name.
        kb_result: Optional pre-fetched KB result dict (from FishEcologyOrchestrator).
        group: Engine group for full search ("quick"/"standard"/"full").
        limit: Max results per engine.
        on_result: Streaming callback for Stage 2.

    Returns:
        KbFirstSearchResult with stage="kb_check" (first call) or "full_search".
    """
    # If kb_result is already provided (e.g. from a previous cross-project call),
    # use it directly
    if kb_result:
        kb_found = kb_result.get("found", False)
        return KbFirstSearchResult(
            stage="kb_check",
            species_name=species_name,
            kb_found=kb_found,
            kb_summary=kb_result.get("summary_text", ""),
            kb_recommendation=kb_result.get("search_recommendation", "continue_to_c"),
            kb_data=kb_result,
            all_candidates=kb_result.get("all_candidates", []),
            suggested_next="ask_user",
        )

    # Stage 1: Query fish-ecology-assistant KB
    orch = _load_fish_kb()
    if orch is None:
        # f项目不可用 → 直接跳到全量搜索
        full = coordinated_search(species_name, group=group, limit=limit, on_result=on_result)
        return KbFirstSearchResult(
            stage="full_search",
            species_name=species_name,
            kb_found=False,
            kb_summary="⚠️ f项目知识库不可用，已直接启动全量搜索。",
            kb_recommendation="continue_to_c",
            full_search=full,
            suggested_next="done",
        )

    try:
        kb = orch.kb_first_lookup(query=species_name)
    except Exception:
        # KB lookup failed → fall through to full search
        full = coordinated_search(species_name, group=group, limit=limit, on_result=on_result)
        return KbFirstSearchResult(
            stage="full_search",
            species_name=species_name,
            kb_found=False,
            kb_summary="⚠️ KB查询失败，已直接启动全量搜索。",
            kb_recommendation="continue_to_c",
            full_search=full,
            suggested_next="done",
        )

    kb_data = {
        "found": kb.found,
        "scientific_name": kb.scientific_name,
        "chinese_name": kb.chinese_name,
        "aliases": kb.aliases,
        "synonyms": kb.synonyms,
        "family": kb.family,
        "order": kb.order,
        "conservation": kb.conservation,
        "ecology": kb.ecology,
        "distribution": kb.distribution,
        "category": kb.category,
        "summary_text": kb.summary_text,
        "search_recommendation": kb.search_recommendation,
        "all_candidates": kb.all_candidates,
    }

    return KbFirstSearchResult(
        stage="kb_check",
        species_name=species_name,
        kb_found=kb.found,
        kb_summary=kb.summary_text,
        kb_recommendation=kb.search_recommendation,
        kb_data=kb_data,
        all_candidates=kb.all_candidates,
        suggested_next="ask_user",
    )


def continue_full_search(
    stage1_result: KbFirstSearchResult,
    group: str = "full",
    limit: int = 10,
    on_result: callable = None,
) -> KbFirstSearchResult:
    """Stage 2: Continue to full search with c项目, enriched by KB data.

    Takes the Stage 1 result (kb_check), enriches the search with KB-known
    synonyms/aliases/variants, and runs coordinated_search().

    Args:
        stage1_result: Result from search_with_kb_first() Stage 1.
        group: Engine group ("quick"/"standard"/"full").
        limit: Max results per engine.
        on_result: Streaming callback.

    Returns:
        KbFirstSearchResult with stage="full_search" and populated full_search.
    """
    # Build enriched species name: prefer KB scientific name
    kb = stage1_result.kb_data
    search_name = kb.get("scientific_name", "") or stage1_result.species_name

    # If KB has chinese_name, pass it through for Chinese search
    # (coordinated_search handles Chinese names natively via _load_species_info)

    # Run full coordinated search
    full = coordinated_search(
        species_name=search_name,
        group=group,
        limit=limit,
        on_result=on_result,
    )

    # Attach KB metadata to the full search result
    if kb:
        full._kb_enriched = True
        full._kb_family = kb.get("family", "")
        full._kb_aliases = kb.get("aliases", [])
        full._kb_synonyms = kb.get("synonyms", [])

    stage1_result.stage = "full_search"
    stage1_result.full_search = full
    stage1_result.suggested_next = "done"

    return stage1_result


# ──── Backward-compat: add attrs to CoordinatedSearchResult ────
# These are set dynamically by continue_full_search()
CoordinatedSearchResult._kb_enriched = False
CoordinatedSearchResult._kb_family = ""
CoordinatedSearchResult._kb_aliases = []
CoordinatedSearchResult._kb_synonyms = []