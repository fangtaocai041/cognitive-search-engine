### Layer 11: LLM Cognitive Query Expansion [IG=0.02, Budget=8%, conditional]
```
FROM all Steps 0.1-0.4:
  USE thinking_sequentialthinking:
    Generate queries that leverage:
    - Semiotic knowledge (what the species IS, not what it's CALLED)
    - Ecological context (habitat, diet, behavior)
    - Taxonomic context (family, relatives)
    - Chinese domain knowledge (local names, regional research groups)

  OUTPUT: 5 queries that would find papers about this species
          WITHOUT using the genus or species name at all.
```

### Layer 12: New-Paper Detection [IG=N/A, Budget=0, ALWAYS] [v3.2 NEW]
```
FOR EACH paper IN all_papers:
  IF paper.year >= current_year - 1 AND paper.pmid IS NULL:
    paper.flag = "🆕 新论文，PubMed 尚未索引"
    paper.action = "直接通过 DOI 验证: https://doi.org/" + paper.doi
    paper.verification_status = "DOI 已注册但未进入 PubMed 索引管道"

OUTPUT: all papers with flags attached
```