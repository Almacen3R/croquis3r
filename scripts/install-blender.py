"""Install a checksum-pinned portable Blender in .tools (Windows development)."""
import hashlib
from pathlib import Path
import urllib.request
import zipfile

VERSION = '4.5.15'
SHA256 = '52dd02fd74877fa08e74b67d7854cf32468a232c02aaa19b6844c91285574f8d'
ROOT = Path(__file__).resolve().parents[1] / '.tools'
NAME = f'blender-{VERSION}-windows-x64'


def main():
    archive = ROOT / (NAME + '.zip')
    ROOT.mkdir(exist_ok=True)
    if not archive.exists():
        print(f'Downloading official Blender {VERSION}...', flush=True)
        with urllib.request.urlopen(f'https://download.blender.org/release/Blender4.5/{NAME}.zip', timeout=60) as response, archive.open('wb') as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
    with archive.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != SHA256:
            raise SystemExit(f'Checksum mismatch: remove {archive} and retry. Nothing extracted.')
    print('SHA-256 verified. Extracting portable Blender...', flush=True)
    with zipfile.ZipFile(archive) as package:
        for entry in package.infolist():
            path = (ROOT / entry.filename).resolve()
            if not path.is_relative_to(ROOT.resolve()):
                raise SystemExit('Unsafe archive path')
        package.extractall(ROOT)
    print(ROOT / NAME / 'blender.exe', flush=True)


if __name__ == '__main__':
    main()
