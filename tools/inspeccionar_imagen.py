#!/usr/bin/env python3
"""Descarga, ejecuta e inspecciona una etiqueta de la imagen GHCR del repositorio.

Diseñado para GitHub Actions: sólo acepta tags seguros, nunca evalúa shell.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

TAG_RE = re.compile(r'^(latest|main|sha-[0-9a-f]{7,40})$')
REPO_RE = re.compile(r'^[\w.-]+/[\w.-]+$')


def execute(image: str, *, runner=subprocess.run) -> dict:
    def run(args, timeout=100):
        result = runner(args, capture_output=True, text=True, check=False, timeout=timeout)
        if result.returncode != 0:
            raise RuntimeError(f'Fallo en {args[1] if len(args)>1 else "docker"} (exit={result.returncode}); consultar logs de Docker')
        return result.stdout

    run(['docker', 'pull', image], timeout=180)
    raw = run(['docker', 'image', 'inspect', image, '--format', '{{json .}}'])
    details = json.loads(raw)
    output = run(['docker', 'run', '--rm', image], timeout=70)
    # El programa de este repo imprime JSON; no fingimos éxito si produce otra cosa.
    try:
        program = json.loads(output)
    except json.JSONDecodeError as e:
        raise RuntimeError('El contenedor no produjo el JSON esperado') from e
    if not isinstance(program, dict) or program.get('ejecutado') is not True:
        raise RuntimeError('La salida JSON no confirma la ejecución del contenedor')
    files = run(['docker', 'run', '--rm', '--entrypoint', 'sh', image, '-c',
                 'printf "Directorio: "; pwd; printf "\\nArchivos:\\n"; ls -la; printf "\\nPrograma:\\n"; sed -n "1,45p" demo.mjs'])
    return {
        'date_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'image': image, 'program': program,
        'architecture': details.get('Architecture'), 'os': details.get('Os'),
        'size_bytes': details.get('Size'),
        'digests': details.get('RepoDigests') or [],
        'labels': (details.get('Config') or {}).get('Labels') or {},
        'files_output': files[:10000],
    }


def report_md(data: dict) -> str:
    p = data['program']
    lines = ['# Ejecución e inspección de imagen OCI', '',
             f"**Fecha (UTC):** {data['date_utc']}",
             f"**Imagen publicada:** `{data['image']}`",
             '**Estado:** ejecución comprobada (JSON validado)',
             f"**Plataforma:** `{data.get('os')}/{data.get('architecture')}`", '',
             '## Resultado del programa', '', '```json', json.dumps(p, ensure_ascii=False, indent=2), '```', '',
             '## Digest y metadatos', '', '```json',
             json.dumps({'digests': data['digests'], 'labels': data['labels']}, ensure_ascii=False, indent=2),
             '```', '', '## Contenido del contenedor', '', '```text', data['files_output'], '```', '',
             '> El contenedor es una validación ejecutable de la imagen; el asistente Gemini se ejecuta separadamente en GitHub Actions.']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', required=True)
    parser.add_argument('--tag', default='latest')
    parser.add_argument('--out', default='artifacts/inspeccion-imagen.json')
    parser.add_argument('--markdown', default='artifacts/inspeccion-imagen.md')
    args = parser.parse_args()
    if not TAG_RE.fullmatch(args.tag) or not REPO_RE.fullmatch(args.repo):
        parser.error('Etiqueta no permitida; usa latest, main o sha-<hash>')
    image = 'ghcr.io/' + args.repo.lower() + '-demo:' + args.tag
    data = execute(image)
    for path, content in [(args.out, json.dumps(data, indent=2, ensure_ascii=False)),
                          (args.markdown, report_md(data))]:
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content + ('\n' if path == args.out else ''), encoding='utf-8')
    print(f'OK: {image} | {data["program"]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
