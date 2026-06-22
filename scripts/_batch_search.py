import json, sys, time
sys.path.insert(0, '.')
from scripts.search_api import run_search

results = {}
for sp in ['Tribolodon brandti', 'Pseudaspius hakonensis', 'Ochetobius elongatus']:
    t0 = time.time()
    r = run_search(sp, max_results=8, group='full')
    elapsed = time.time() - t0
    srcs = {}
    for p in r['papers']:
        s = p.get('source', '?')
        srcs[s] = srcs.get(s, 0) + 1
    top = r['papers'][:4] if r['papers'] else []
    results[sp] = {
        'raw': r['stats']['total_raw'],
        'merged': r['stats']['total_merged'],
        'elapsed': elapsed,
        'sources': srcs,
        'top': [
            {
                'title': p.get('title', '?'),
                'year': p.get('year', '?'),
                'doi': p.get('doi', '?'),
                'source': p.get('source', '?'),
                'cred': p.get('credibility_score', '?'),
                'authors': p.get('authors', [])[:3],
                'journal': p.get('journal', '?'),
            }
            for p in top
        ],
    }

print(json.dumps(results, ensure_ascii=False, indent=2))
