import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('registry_builder', ROOT/'scripts/build-index.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class RegistryTests(unittest.TestCase):
    def fixture(self, base):
        base.mkdir()
        (base/'payload').mkdir()
        (base/'payload/data').write_bytes(b'configuration\n')
        entry = {'path': 'payload/data', 'sha256': hashlib.sha256(b'configuration\n').hexdigest(), 'size': 14}
        value = {'schema_version': 1, 'kind': 'DevicePackage', 'id': 'device:fixture', 'version': '0.1.0',
                 'source': {'kind': 'local', 'path': 'fixture'}, 'compatibility': {}, 'components': [], 'files': [entry]}
        (base/'manifest.json').write_text(json.dumps(value))

    def test_production_draft_advertises_no_unsigned_package(self):
        index = json.loads((ROOT/'device-index.json').read_text())
        self.assertEqual(index['packages'], [])
        self.assertEqual(index['sequence'], 0)
        device = json.loads((ROOT/'devices/oxp3.json').read_text())
        self.assertEqual({item['status'] for item in device['compatibility_records']}, {'supported', 'experimental', 'blocked'})
        self.assertTrue(all(item['evidence'] and item['note'] for item in device['compatibility_records']))

    def test_local_index_uses_actual_manifest_bytes(self):
        with tempfile.TemporaryDirectory() as work:
            source = Path(work)/'package'
            self.fixture(source)
            result = builder.build(source, Path(work)/'out/index.json')
            entry = result['packages'][0]
            self.assertEqual(entry['sha256'], hashlib.sha256((source/'manifest.json').read_bytes()).hexdigest())
            self.assertEqual(entry['size'], (source/'manifest.json').stat().st_size)
            self.assertEqual(entry['source']['kind'], 'local')
            self.assertFalse(result['trust']['official_release'])

    def test_tampered_inventory_is_not_indexed(self):
        with tempfile.TemporaryDirectory() as work:
            source = Path(work)/'package'
            self.fixture(source)
            (source/'payload/data').write_bytes(b'changed')
            with self.assertRaises(ValueError):
                builder.build(source, Path(work)/'out/index.json')


if __name__ == '__main__':
    unittest.main()
