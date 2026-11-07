"""Download the pinned Three.js browser modules, verifying npm package integrity.

No npm install/build step or external CDN is required by the application.
Run manually when updating the dependency; review and commit the resulting files.
"""
import base64
import hashlib
import io
import json
from pathlib import Path
import tarfile
from urllib.request import urlopen

VERSION = "0.187.0"
INTEGRITY = "Qiu7R+Cmh8CstZsY1uJOSWnVlfo7ZtNLV7mF8Jltk3LB3AtDu9cRZlcnRKkAk8Y4z6KKw35z7Y7Urd7jWY8etA=="
URL = f"https://registry.npmjs.org/three/-/three-{VERSION}.tgz"
TARGET = Path(__file__).resolve().parents[1] / "src/static/croquis/vendor/three"


def main():
    with urlopen(URL, timeout=60) as response:
        archive = response.read()
    actual = base64.b64encode(hashlib.sha512(archive).digest()).decode()
    if actual != INTEGRITY:
        raise SystemExit("Three.js package integrity mismatch; no files written")
    files = {
        "package/build/three.core.js": "three.core.js",
        "package/build/three.module.js": "three.module.js",
        "package/examples/jsm/controls/OrbitControls.js": "OrbitControls.js",
        "package/LICENSE": "LICENSE",
    }
    TARGET.mkdir(parents=True, exist_ok=True)
    hashes = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as package:
        for source, destination in files.items():
            data = package.extractfile(source).read()
            if destination == "OrbitControls.js":
                data = data.replace(b"from 'three'", b"from './three.module.js'")
            (TARGET / destination).write_bytes(data)
            hashes[destination] = hashlib.sha256(data).hexdigest()
    (TARGET / "manifest.json").write_text(json.dumps({
        "name": "three", "version": VERSION, "source": URL,
        "integrity": "sha512-" + INTEGRITY, "license": "MIT",
        "patch": "OrbitControls bare import replaced with local ./three.module.js",
        "sha256": hashes,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"Three.js {VERSION}: {len(files)} verified files written")


if __name__ == "__main__":
    main()
