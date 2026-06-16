"""
Living Database Catalog — Dynamic Router for Cognitive Search Engine.

⚠️ DEPRECATED (v5.7): This module is not used by the current search pipeline.
   unified_search.coordinated_search() now handles all routing directly via
   search_streaming() + ENGINE_REGISTRY. The catalog_loader approach was
   designed for a graph-router architecture that was superseded.
   KEPT for reference / future multi-domain routing needs.

Routes species literature search queries across 65 databases organized into
8 domains with 4 tiers. Self-evolves weights based on feedback.

Architecture: