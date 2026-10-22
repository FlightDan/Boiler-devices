"""Build an unsigned local DeviceIndex from an inventoried device package."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


def build(package, output):
    package, output = Path(package).resolve(), Path(output)
    if output.exists():
        raise ValueError('Index destination already exists')
    manifest_path = package/'manifest.json'
    if manifest_path.is_symlink():
        raise ValueError('Manifest cannot be a symlink')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    if manifest.get('schema_version') != 1 or manifest.get('kind') != 'DevicePackage':
        raise ValueError('Unsupported device package')
    actual = set()
    for path in package.rglob('*'):
        if path.is_symlink() or (hasattr(path, 'is_junction') and path.is_junction()):
            raise ValueError('Package links are forbidden')
        if path.is_file():
            actual.add(path.relative_to(package).as_posix())
    seen = set()
    for entry in manifest['files']:
        name = entry['path']
        if not isinstance(name, str) or '\\' in name or ':' in name or name.startswith('/') or any(p in ('', '.', '..') for p in name.split('/')):
            raise ValueError('Unsafe inventory path')
        if name.casefold() in seen:
            raise ValueError('Duplicate inventory path')
        seen.add(name.casefold())
        path = package/name
        if not path.is_file() or path.stat().st_size != entry['size'] or digest(path) != entry['sha256']:
            raise ValueError('Package inventory mismatch')
    if actual != {'manifest.json', *(entry['path'] for entry in manifest['files'])}:
        raise ValueError('Uninventoried package content')
    index = json.loads((ROOT/'device-index.json').read_text(encoding='utf-8'))
    index['generated_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    index['packages'] = [{
        'id': manifest['id'], 'version': manifest['version'],
        'source': {'kind': 'local', 'path': Path(os.path.relpath(package, output.parent.resolve())).as_posix(), 'repository': manifest['source'].get('repository', '')},
        'sha256': digest(manifest_path), 'size': manifest_path.stat().st_size,
        'compatibility': manifest['compatibility'], 'status': 'experimental',
        'notes': ['Unsigned local snapshot; requires an explicit development trust grant.']
    }]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(index, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return index


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    value = build(args.package, args.output)
    print(json.dumps({'status': 'unsigned-development', 'packages': len(value['packages'])}))
