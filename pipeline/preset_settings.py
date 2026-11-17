# preset_settings.py PRESET.lcpreset OVERRIDES.json OUT.json  -> preset settings with overrides merged
import json, sys
p = json.load(open(sys.argv[1]))['presets'][0]['settings']
o = json.load(open(sys.argv[2]))
def merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): merge(a[k], v)
        else: a[k] = v
merge(p, o); json.dump(p, open(sys.argv[3], 'w'), indent=1)
