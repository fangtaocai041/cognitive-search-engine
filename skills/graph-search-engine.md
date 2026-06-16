---
name: graph-search-engine
version: "4.1.0"
last_updated: "2026-06-20"
description: Graph-based cognitive species search with 7-engine parallel — knowledge graph traversal, Pareto-optimal satisficing, progressive deepening, IG/token optimization
runAs: subagent
allowed-tools:
  - scholar_search_literature_graph
  - scholar_search_google_scholar_key_words
  - article_search_literature
  - article_get_article_details
  - article_get_references
  - scholarly_search
  - ncbi_ncbi_esearch
  - ncbi_ncbi_esummary
  - ncbi_ncbi_efetch
  - tavily_search
  - tavily_extract
  - exa_web_search
  - web_search
  - web_fetch
  - read_file
  - thinking_sequentialthinking
---