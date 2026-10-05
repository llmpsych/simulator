#!/usr/bin/env python3
"""Deterministic publication gate; Python standard library only."""
import json
from pathlib import Path
import re
import sys
import tomllib
import unittest
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def strings(obj, keys):
    require(isinstance(obj, dict), 'expected an object')
    for key in keys:
        require(isinstance(obj.get(key), str) and obj[key].strip(), f'missing/empty string: {key}')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'duplicate JSON key: {key}')
        result[key] = value
    return result


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=unique_object,
                      parse_constant=lambda value: require(False, f'invalid JSON constant: {value}'))


def check_data(root):
    cases = sorted((root / 'cases').glob('*.json'))
    prompts = sorted((root / 'prompts/content').glob('*.md'))
    transcripts = sorted((root / 'transcripts').glob('*.json'))
    require(cases and prompts and transcripts, 'case, prompt and transcript collections must be nonempty')
    for path in cases:
        case = read_json(path)
        strings(case, ['id', 'name', 'title', 'description', 'vulnerability', 'variant'])
        require(path.stem == f"{case['id']}_{case['name']}", f'{path.name}: case ID/name mismatch')
        strings(case.get('patient_profile'), ['presentation', 'current_state', 'masking'])
        strings(case.get('the_bind'), ['objective', 'subjective', 'tension'])
        dimensions = case.get('scoring_dimensions')
        require(isinstance(dimensions, list) and dimensions, f'{path.name}: no scoring dimensions')
        ids = set()
        for dimension in dimensions:
            strings(dimension, ['id', 'name', 'description'])
            require(dimension['id'] not in ids, f'{path.name}: duplicate scoring dimension')
            ids.add(dimension['id'])
    case_ids = {p.stem for p in cases}
    prompt_ids = {p.stem for p in prompts}
    for path in prompts:
        require(re.fullmatch(r'.+_v\d{3}', path.stem), f'{path.name}: invalid prompt version')
        require(path.stem.rsplit('_', 1)[0] in case_ids, f'{path.name}: unknown case')
        require(path.read_text(encoding='utf-8').strip(), f'{path.name}: empty prompt')
        meta = root / 'prompts/meta' / path.name
        require(meta.is_file() and meta.read_text(encoding='utf-8').strip(), f'{path.name}: missing/empty prompt metadata')
    require({p.stem for p in (root / 'prompts/meta').glob('*.md')} == prompt_ids,
            'prompt content/metadata sets differ')
    for path in transcripts:
        data = read_json(path)
        require(isinstance(data, dict), f'{path.name}: expected an object')
        meta = data.get('metadata')
        strings(meta, ['patient_model', 'bot_model', 'timestamp', 'case', 'prompt'])
        require(meta['case'] in case_ids, f'{path.name}: unknown case')
        require(meta['prompt'] in prompt_ids, f'{path.name}: unknown prompt')
        require(meta['prompt'].rsplit('_', 1)[0] == meta['case'], f'{path.name}: prompt/case mismatch')
        require(re.fullmatch(r'\d{8}_\d{6}', meta['timestamp']), f'{path.name}: timestamp format')
        datetime.strptime(meta['timestamp'], '%Y%m%d_%H%M%S')
        rows = data.get('transcript')
        require(isinstance(rows, list) and rows and len(rows) % 2 == 0,
                f'{path.name}: expected complete patient/bot pairs')
        for index, row in enumerate(rows):
            strings(row, ['role', 'content'])
            require(row['role'] == ('patient' if index % 2 == 0 else 'bot'),
                    f'{path.name}: row {index}: expected alternating patient/bot roles')


def main():
    # Fail closed if future tests accidentally attempt real transport or subprocesses.
    def offline(event, args):
        if event.startswith('socket.') or event in {'subprocess.Popen', 'os.system', 'os.posix_spawn'}:
            raise RuntimeError(f'offline gate forbids {event}')
    sys.addaudithook(offline)
    try:
        for path in sorted(ROOT.glob('*.py')) + sorted((ROOT / 'scripts').glob('*.py')) + sorted((ROOT / 'tests').glob('*.py')):
            compile(path.read_text(encoding='utf-8'), str(path), 'exec')
        project = tomllib.loads((ROOT / 'pyproject.toml').read_text())['project']
        lock = tomllib.loads((ROOT / 'uv.lock').read_text())
        require(project['dependencies'] == [], 'new dependencies require an explicit offline gate setup')
        require(lock['requires-python'] == project['requires-python'], 'lock Python constraint drift')
        require(len(lock['package']) == 1 and lock['package'][0]['name'] == project['name']
                and lock['package'][0]['version'] == project['version'], 'lock package drift')
        require((ROOT / project['readme']).is_file(), 'project readme missing')
        check_data(ROOT)
        sys.path.insert(0, str(ROOT))
        suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'))
        require(suite.countTestCases() > 0, 'no regression tests discovered')
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        if not result.wasSuccessful():
            return 1
    except (ValueError, OSError, SyntaxError, KeyError, TypeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    print('PASS: offline source, fixture, lock and regression checks')
    return 0


if __name__ == '__main__':
    sys.exit(main())
