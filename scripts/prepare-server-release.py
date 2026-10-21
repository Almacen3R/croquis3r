"""Empaqueta código y una instantánea SQLite consistente; no modifica el origen."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import shutil
import sys
import tarfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".deploy" / "croquis3r-20261021"
DEST.mkdir(parents=True, exist_ok=True)
snapshot = DEST / "local-snapshot.sqlite3"
with sqlite3.connect(f"file:{ROOT / 'db.sqlite3'}?mode=ro", uri=True) as source:
    with sqlite3.connect(snapshot) as target:
        source.backup(target)
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
from django.conf import settings
settings.DATABASES["default"]["NAME"] = snapshot
import django
django.setup()
from django.core.management import call_command
fixture = DEST / "initial-data.json"
with fixture.open("w", encoding="utf-8") as output:
    call_command("dumpdata", "catalog", "sketches", natural_foreign=True, indent=2,
                 stdout=output, verbosity=0)
records = json.loads(fixture.read_text(encoding="utf-8"))
counts = {}
for record in records:
    counts[record["model"]] = counts.get(record["model"], 0) + 1
archive = DEST / "croquis3r-source.tar.gz"
paths = ["manage.py", "Dockerfile", "compose.yaml", "compose.production.yaml", "compose.server-lan.yaml",
         ".dockerignore", ".gitignore", ".env.example", "requirements.txt", "requirements.lock", "Makefile", "README.md",
         "src", "scripts", "tests", "docs"]
def include(info):
    return None if "__pycache__" in Path(info.name).parts or info.name.endswith((".pyc", ".sqlite3")) else info
with tarfile.open(archive, "w:gz") as tar:
    for relative in paths:
        tar.add(ROOT / relative, arcname=relative, filter=include)
bootstrap = DEST / "deploy-server-lan.sh"
shutil.copyfile(ROOT / "scripts/deploy-server-lan.sh", bootstrap)
files = {}
for path in (fixture, archive, bootstrap):
    files[path.name] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
manifest = {"release": "20261021", "source_database": "SQLite snapshot", "counts": counts, "files": files}
(DEST / "release.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
print(json.dumps({"directory": str(DEST), "counts": counts, "files": files}, indent=2))
