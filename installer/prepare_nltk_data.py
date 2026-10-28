"""Stage official NLTK resources at BUILD time, with per-file SHA-256 provenance."""
import hashlib
import io
import json
from pathlib import Path
import sys
from urllib.request import urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_SHA256 = {'averaged_perceptron_tagger': 'e1f13cf2532daadfd6f3bc481a49859f0b8ea6432ccdcd83e6a49a5f19008de9', 'averaged_perceptron_tagger_eng': '6025f530624335c67d6547d44757b357b4e79bae030a0383e9887a92c1718f0b', 'cmudict': 'd07cca47fd72ad32ea9d8ad1219f85301eeaf4568f8b6b73747506a71fb5afd6'}
sys.path.insert(0, str(ROOT))
from server.nltk_resources import REQUIRED_FILES, configure_resources, verify_pronunciation


def main():
    target = ROOT / 'models/nltk_data'
    target.mkdir(parents=True, exist_ok=True)
    archives = {}
    for category, name in (('taggers', 'averaged_perceptron_tagger'),
                           ('taggers', 'averaged_perceptron_tagger_eng'), ('corpora', 'cmudict')):
        url = f'https://raw.githubusercontent.com/nltk/nltk_data/gh-pages/packages/{category}/{name}.zip'
        with urlopen(url, timeout=60) as response:
            raw = response.read()
        if hashlib.sha256(raw).hexdigest() != ARCHIVE_SHA256[name]:
            raise RuntimeError('Official NLTK archive hash changed; review required: ' + name)
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            if archive.testzip() is not None:
                raise RuntimeError('Damaged official NLTK resource: ' + name)
            if name.endswith('_eng'):
                # Only the three explicit JSON files are extracted; no arbitrary
                # archive path or runtime application file may be overwritten.
                for relative in REQUIRED_FILES:
                    if relative.startswith('taggers/averaged_perceptron_tagger_eng/'):
                        destination = target / relative
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(archive.read(relative.removeprefix('taggers/')))
            else:
                destination = target / category / (name + '.zip')
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(raw)
                if name == 'cmudict':
                    for member in ('cmudict/cmudict', 'cmudict/README'):
                        destination = target / category / member
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(archive.read(member))
        archives[name] = {'url': url, 'sha256': hashlib.sha256(raw).hexdigest()}
    files = {relative: hashlib.sha256((target / relative).read_bytes()).hexdigest()
             for relative in REQUIRED_FILES}
    manifest = {'filesSha256': files, 'officialArchives': archives}
    (target / 'resources_sha256.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    configure_resources(required=True, root=target)
    print(json.dumps(verify_pronunciation(), indent=2))
    print('Staged and verified offline NLTK resources, including English JSON tagger.')


if __name__ == '__main__':
    main()
