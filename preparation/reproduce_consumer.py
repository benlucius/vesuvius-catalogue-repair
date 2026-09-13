#!/usr/bin/env python3
"""Run pinned, unmodified Villa catalogue consumers on the v1.0.0 fixtures.
Python 3.11+ and Node.js 18+. No package installation or CT data download.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release-dir', required=True, type=Path)
    parser.add_argument('--upstream-dir', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--fetch-upstream', action='store_true', help='Download only pinned source files; never install dependencies')
    args = parser.parse_args()
    lock = json.loads(Path(__file__).with_name('source-lock.json').read_text())
    upstream = args.upstream_dir.resolve()
    for name, meta in lock['files'].items():
        p = upstream / name
        if not p.exists() and args.fetch_upstream:
            url = f"https://raw.githubusercontent.com/{lock['repository']}/{lock['commit']}/{name}"
            with urllib.request.urlopen(url, timeout=40) as response:
                data = response.read()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        data = p.read_bytes()
        digest = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if digest != meta['git_blob_sha']:
            raise ValueError('Upstream source mismatch: ' + name)
    release = args.release_dir.resolve()
    for line in (release / 'SHA256SUMS.txt').read_text().splitlines():
        digest, name = line.split('  ', 1)
        if sha((release / name).read_bytes()) != digest:
            raise ValueError('Release checksum mismatch: ' + name)
    args.out.mkdir(parents=True, exist_ok=False)
    documents = [('before', release / 'evidence/metadata.original.json'), ('after_six', release / 'metadata.six.corrected.json')]
    outputs = {}
    logs = ['Unmodified Villa lasagna.manager.cli, local catalogue fixtures', 'Commit: ' + lock['commit'], 'Python: ' + sys.version.split()[0], 'Both commands are expected to exit 0; the defect is missing displayed dimensions, not a crash.', '']
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        for label, source in documents:
            data = source.read_bytes()
            cache = root / label / 'catalog'
            cache.mkdir(parents=True)
            (cache / 'metadata.json').write_bytes(data)
            # Local fixture cache, not a claim of an HTTP retrieval by this consumer.
            (cache / 'metadata.cache.json').write_text(json.dumps({'sha256': sha(data), 'validated_unix': time.time(), 'fixture': True}))
            config = root / (label + '.toml')
            config.write_text('cache_dir = ' + json.dumps(str(cache.parent)) + '\ncatalog_max_age_seconds = 86400\n')
            env = dict(os.environ, PYTHONPATH=str(upstream), PYTHONDONTWRITEBYTECODE='1', LAS_MANAGER_CONFIG=str(config), AGENTS_AGENT_MODE='1')
            base = [sys.executable, '-B', '-m', 'lasagna.manager.cli', 'volume', 'ls']
            for sample in ['PHerc0343P', 'PHerc0500P2']:
                process = subprocess.run(base + ['--sample', sample], env=env, capture_output=True, text=True, check=True)
                if process.stderr:
                    raise RuntimeError(process.stderr)
                logs += [label + ': python -m lasagna.manager.cli volume ls --sample ' + sample, process.stdout, 'Exit status: 0', '']
            process = subprocess.run(base + ['--json'], env=env, capture_output=True, text=True, check=True)
            if process.stderr:
                raise RuntimeError(process.stderr)
            outputs[label] = json.loads(process.stdout)
    before = {r['volume_id']: r for r in outputs['before']}
    after = {r['volume_id']: r for r in outputs['after_six']}
    assert before.keys() == after.keys()
    rows = []
    for rid, record in before.items():
        if record['shape'] != after[rid]['shape']:
            expected = json.loads((release / 'evidence' / (record['sample_id'] + '_' + rid + '.zarray.json')).read_text())['shape']
            assert record['shape'] == [] and after[rid]['shape'] == expected
            rows.append({'sample': record['sample_id'], 'volume': rid, 'before': record['shape'], 'after': after[rid]['shape']})
    assert len(rows) == 4
    # Negative control: execute the website's real pure index builder as well.
    # Empty optional overlays are identical in both conditions.
    js = "const fs=require('fs');const {buildIndex}=require(process.argv[1]);const a=JSON.parse(fs.readFileSync(process.argv[2]));process.stdout.write(JSON.stringify(buildIndex(a.samples,{})));"
    website = []
    for label, source in documents:
        result = subprocess.run(['node', '-e', js, str(upstream / 'scrollprize.org/src/components/atlas/buildIndex.js'), str(source)], capture_output=True, text=True, check=True)
        website.append(json.loads(result.stdout))
    same_index = website[0] == website[1]
    assert same_index, 'Website output changed; review before making any claim'
    result = {'upstream_commit': lock['commit'], 'python': sys.version.split()[0], 'node': subprocess.check_output(['node', '--version'], text=True).strip(), 'input_sha256': {label: sha(source.read_bytes()) for label, source in documents}, 'volume_count': len(before), 'volumes_with_dimensions_before': sum(len(r['shape']) == 3 for r in before.values()), 'volumes_with_dimensions_after': sum(len(r['shape']) == 3 for r in after.values()), 'changed_shapes': rows, 'website_index_unchanged': same_index, 'scope': 'Actual Lasagna catalogue listing and website index builder only; no GPU inference, VC3D GUI run, upstream deployment, or human-use claim.'}
    (args.out / 'consumer-result.json').write_text(json.dumps(result, indent=2) + '\n')
    (args.out / 'consumer-before-after.log').write_text('\n'.join(logs))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
