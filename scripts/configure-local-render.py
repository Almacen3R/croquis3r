"""Enable the installed portable renderer in local .env without printing secrets."""
from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
binary = root / '.tools/blender-4.5.15-windows-x64/blender.exe'
if not binary.is_file():
    raise SystemExit('Primero ejecute scripts/install-blender.py.')
target = root / '.env'
content = target.read_text(encoding='utf-8') if target.exists() else ''
for key, value in {'RENDER_ENABLED': '1', 'BLENDER_BINARY': binary.as_posix()}.items():
    pattern = rf'(?m)^\s*{key}\s*=.*$'
    line = f'{key}={value}'
    content = re.sub(pattern, lambda _: line, content) if re.search(pattern, content) else content.rstrip()+'\n'+line+'\n'
target.write_text(content.lstrip('\n'), encoding='utf-8')
print('Render local habilitado. Reinicie app y render_worker para aplicar.')
