    def _estimate_volume(self, species_id: str) -> int:
        """Estimate literature volume using multi-source (PubMed/Scholar/Web) or graph fallback.

        Implements fuzzy-species-search-rule v5.0:
          ncbi_esearch(scientific_name) → total_count
          scholar_search_literature_graph(scientific_name, limit=5) → rough_estimate
          web_search(chinese_name + " 论文 OR 综述", topK=5) → chinese_hits
          RETURN MAX(pubmed_count, scholar_count, chinese_hits * 0.5)
        """
        # ── Primary: WorldModel prediction ──
        if WorldModel is not None and self._world is None:
            try:
                from src.graph_updater import load_species_graph as lgs
                known = lgs(species_id)
                self._world = WorldModel()
                self._world.init_belief(species_id, len(known))
                prediction = self._world.predict(species_id)
                wm_volume = prediction.get("estimated_volume", len(known))
                if wm_volume > len(known):
                    return wm_volume
            except Exception:
                pass

        # ── Secondary: Multi-source HTTP estimation ──
        multi = self._estimate_literature_volume_multi(species_id)
        if multi > 0:
            return multi

        # ── Fallback: count known papers from graph ──
        known = self._load_known(species_id)
        return max(len(known), 8)

    def _estimate_literature_volume_multi(self, species_id: str) -> int:
        """Multi-source literature volume estimation via HTTP REST APIs.

        Uses PubMed E-utilities (esearch), Crossref, and Chinese web search
        to estimate total literature volume for adaptive search strategy.

        Returns:
            Estimated volume as MAX(pubmed_count, scholar_count, chinese_hits * 0.5).
            Returns 0 if all sources fail.
        """
        self._ensure_graph_loaded()
        species_info = self._species_map.get(species_id, {})
        scientific_name = species_info.get("name", species_id.replace("_", " "))
        chinese_name = species_info.get("chinese", "")

        from concurrent.futures import ThreadPoolExecutor, as_completed
        from urllib.parse import quote as _url_quote
        import urllib.request as _urlreq
        import json as _json

        pubmed_count: int = 0
        scholar_count: int = 0
        chinese_hits: int = 0

        def _fetch_pubmed():
            nonlocal pubmed_count
            try:
                url = (
                    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?"
                    f"db=pubmed&term={_url_quote(scientific_name)}&retmax=0&retmode=json"
                )
                with _urlreq.urlopen(url, timeout=10) as resp:
                    data = _json.loads(resp.read())
                pubmed_count = int(data.get("esearchresult", {}).get("count", "0") or "0")
            except Exception:
                pass

        def _fetch_crossref():
            nonlocal scholar_count
            try:
                url = (
                    "https://api.crossref.org/works?"
                    f"query={_url_quote(scientific_name)}&rows=0"
                )
                with _urlreq.urlopen(url, timeout=10) as resp:
                    data = _json.loads(resp.read())
                scholar_count = int(data.get("message", {}).get("total-results", 0) or 0)
            except Exception:
                pass

        def _fetch_chinese():
            nonlocal chinese_hits
            if not chinese_name:
                return
            try:
                # Use Bing web search for Chinese literature presence estimate
                bing_url = (
                    "https://www.bing.com/search?"
                    f"q={_url_quote(chinese_name + ' 论文 OR 综述')}&count=5"
                )
                req = _urlreq.Request(bing_url, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; Reasonix/1.0)",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                })
                with _urlreq.urlopen(req, timeout=10) as resp:
                    html = resp.read().decode("utf-8", errors="replace")
                # Count search result blocks as rough estimate
                import re
                blocks = re.findall(r'<li class="b_algo"', html)
                chinese_hits = len(blocks) * 3  # each Bing result ≈ 3 papers
            except Exception:
                pass

        with ThreadPoolExecutor(max_workers=3) as pool:
            futs = [pool.submit(f) for f in (_fetch_pubmed, _fetch_crossref, _fetch_chinese)]
            for fut in as_completed(futs):
                try:
                    fut.result(timeout=12)
                except Exception:
                    pass

        return max(pubmed_count, scholar_count, int(chinese_hits * 0.5))