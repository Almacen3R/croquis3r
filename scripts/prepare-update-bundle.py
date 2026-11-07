"""Prepare an exact, commit-scoped update and privileged installer. No local data."""
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])


def main():
    commit = git('rev-parse', 'HEAD').decode().strip()
    assert git('rev-parse', 'main').decode().strip() == commit
    short = commit[:12]
    dest = ROOT / '.deploy' / ('production-update-' + short)
    dest.mkdir(parents=True, exist_ok=True)
    subprocess.run(['git', '-C', str(ROOT), 'bundle', 'create', str(dest / 'croquis3r.bundle'), 'main'], check=True)
    subprocess.run(['git', '-C', str(ROOT), 'bundle', 'verify', str(dest / 'croquis3r.bundle')], check=True)
    (dest / 'update-server-lan.sh').write_bytes(git('show', f'{commit}:scripts/update-server-lan.sh'))
    expected = {name: hashlib.sha256((dest / name).read_bytes()).hexdigest()
                for name in ('croquis3r.bundle', 'update-server-lan.sh')}
    (dest / 'update.json').write_text(json.dumps({'commit': commit, 'files': expected}, indent=2)+'\n', encoding='utf-8')
    template = git('show', f'{commit}:scripts/install-approved-security-update.sh').decode('utf-8')
    template = template.replace('897308d80fbfe191da5590fd37983de567a16494', commit).replace('897308d80fbf', short)
    template = re.sub(r'expected=\{.*?\}\n', lambda _: 'expected='+repr(expected)+'\n', template, count=1, flags=re.S)
    template = re.sub(r'/usr/local/sbin/croquis3r-update(?![-\w])', '/usr/local/sbin/croquis3r-update-'+short, template)
    template = template.replace('/etc/sudoers.d/croquis3r-approved-update', '/etc/sudoers.d/croquis3r-approved-'+short)
    (dest / 'install-approved-update.sh').write_bytes(template.encode('utf-8'))
    print(json.dumps({'directory': str(dest), 'commit': commit, 'files': expected,
        'installer_sha256': hashlib.sha256(template.encode('utf-8')).hexdigest()}, indent=2))


if __name__ == '__main__':
    main()
