import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'eon-core', 'src'))
from unified_emergence import EmergenceEngine
import json

engine = EmergenceEngine()
data = {
    'years': [2018,2019,2020,2021,2022,2023,2024,2025,2026],
    'body_size': [15,15,16,15, 22,30,40,52,66],
    'diversity': [2.0,1.9,2.1,2.0, 2.2,2.3,2.5,2.6,2.8],
    'connected_lake_recovery': [0,0.01,0,0.01, 0.05,0.12,0.22,0.35,0.50],
    'isolated_lake_recovery':  [0,0.01,0,0.01, 0.02,0.04,0.06,0.08,0.10],
    'K_recovery_rate': [0.01,0,0.02,0.01, 0.05,0.12,0.25,0.40,0.60],
    'r_recovery_rate': [0.02,0.01,0.03,0.02, 0.04,0.06,0.08,0.10,0.12],
    'species': 'TestSpecies',
}

# Manual slope check
for k in ['body_size','diversity']:
    vals = data[k]
    n = len(vals)
    xm = sum(range(n))/n
    ym = sum(vals)/n
    slope = sum((i-xm)*(v-ym) for i,v in enumerate(vals)) / max(sum((i-xm)**2 for i in range(n)), 0.001)
    print(f'{k}: slope={slope:.3f}')

ratio = 5.69 / 0.106
print(f'body/diversity ratio: {ratio:.1f} (need >2.0)')

# Run engine
r = engine.scan(data=data)
print(f'\nDetection results: {len(r)}')
for rr in r:
    dt = rr.get('detection_type','?')
    desc = rr.get('description','')[:120]
    print(f'  [{dt}] {desc}')

signals = engine.signals_summary()
print(f'\nSignals summary: {json.dumps(signals, ensure_ascii=False, indent=2)}')
