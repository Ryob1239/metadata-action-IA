#!/usr/bin/env python3
"""Genera un dashboard estático verificable a partir de metadatos públicos.

NO invoca Gemini ni descarga el contenido de sus reportes. Sólo publica
estados públicos, enlaces y datos de una imagen OCI pública.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPO_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
WORKFLOW_PATHS = {
    'ci': ('ci.yml', 'validate.yml', 'test.yml', 'ai-pruebas.yml'),
    'ai': ('ai-devops.yml',),
    'cd': ('demo-imagen-ghcr.yml', 'inspeccionar-imagen-ghcr.yml'),
    'security': ('codeql.yml', 'zizmor.yml'),
    'pages': ('publicar-dashboard.yml',),
}
LABELS_ALLOWLIST = (
    'org.opencontainers.image.title', 'org.opencontainers.image.description',
    'org.opencontainers.image.source', 'org.opencontainers.image.revision',
    'org.opencontainers.image.version', 'org.opencontainers.image.licenses',
    'org.opencontainers.image.url', 'org.opencontainers.image.documentation',
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def github_json(repo: str, path: str, token: str = '', *, opener=urlopen):
    url = f'https://api.github.com/repos/{repo}/{path.lstrip("/")}'
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'metadata-action-ia-dashboard/1.0',
               'X-GitHub-Api-Version': '2022-11-28'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = Request(url, headers=headers)
    try:
        with opener(req, timeout=18) as response:
            return json.load(response), None
    except HTTPError as error:
        # No se imprimen datos de autorización o cuerpos arbitrarios.
        return None, f'GitHub API HTTP {error.code} en {path.split("?")[0]}'
    except (URLError, TimeoutError, ValueError, OSError) as error:
        return None, f'GitHub API no disponible ({type(error).__name__})'


def run_category(run: dict) -> str:
    source = (run.get('path') or '').split('@')[0].split('/')[-1].lower()
    for group, filenames in WORKFLOW_PATHS.items():
        if source in filenames:
            return group
    name = (run.get('name') or '').lower()
    if 'inteligente devops' in name or 'ia devops' in name:
        return 'ai'
    if 'imagen oci' in name or 'ghcr' in name:
        return 'cd'
    if 'codeql' in name or 'zizmor' in name:
        return 'security'
    return 'other'


def normalize_runs(raw_runs: list[dict], limit: int = 30) -> list[dict]:
    result = []
    for r in raw_runs[:limit]:
        url = r.get('html_url') or ''
        if not url.startswith('https://github.com/'):
            continue
        result.append({
            'id': r.get('id'), 'name': str(r.get('name') or 'Sin nombre')[:130],
            'category': run_category(r),
            'conclusion': r.get('conclusion') or 'pending',
            'status': r.get('status') or 'unknown',
            'created_at': r.get('created_at') or '',
            'updated_at': r.get('updated_at') or '',
            'event': r.get('event') or '',
            'branch': r.get('head_branch') or '',
            'sha': str(r.get('head_sha') or '')[:12],
            'url': url,
        })
    return result


def summarize(runs: list[dict]) -> dict:
    totals = {'success': 0, 'failure': 0, 'other': 0}
    for r in runs:
        c = r['conclusion']
        totals[c if c in ('success', 'failure') else 'other'] += 1
    latest = {}
    for group in ('ci', 'ai', 'cd', 'security', 'pages'):
        latest[group] = next((r for r in runs if r['category'] == group), None)
    return {'total': len(runs), **totals, 'latest': latest}


def inspect_image(repo: str, *, runner=subprocess.run) -> tuple[dict, list[str]]:
    owner, name = repo.lower().split('/', 1)
    image = f'ghcr.io/{owner}/{name}-demo:latest'
    state = {'reference': image, 'package_url': f'https://github.com/{repo}/pkgs/container/{name}-demo',
             'available': False, 'digest': None, 'architecture': None, 'size_bytes': None,
             'labels': {}, 'tags': ['latest', 'main']}
    issues = []
    try:
        pull = runner(['docker', 'pull', image], capture_output=True, text=True, timeout=140, check=False)
        if pull.returncode:
            return state, ['No se pudo descargar la imagen GHCR pública en la actualización.']
        proc = runner(['docker', 'image', 'inspect', image, '--format', '{{json .}}'],
                      capture_output=True, text=True, timeout=20, check=False)
        if proc.returncode:
            return state, ['No se pudo inspeccionar la imagen publicada.']
        details = json.loads(proc.stdout)
        labels = (details.get('Config') or {}).get('Labels') or {}
        digests = details.get('RepoDigests') or []
        state.update({
            'available': True,
            'digest': digests[0].split('@')[-1] if digests else None,
            'architecture': details.get('Architecture'),
            'os': details.get('Os'), 'size_bytes': details.get('Size'),
            'labels': {k: str(labels[k])[:500] for k in LABELS_ALLOWLIST if labels.get(k)},
        })
        revision = state['labels'].get('org.opencontainers.image.revision')
        if revision:
            state['tags'].append('sha-' + revision[:7])
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError):
        issues.append('No se dispone de Docker o de metadatos completos en esta actualización.')
    return state, issues


def build_snapshot(repo: str, token: str = '', *, fetcher=github_json,
                   inspector=inspect_image) -> dict:
    if not REPO_PATTERN.fullmatch(repo):
        raise ValueError('Repo inválido: usa propietario/nombre')
    warnings = []
    payload, error = fetcher(repo, 'actions/runs?per_page=80', token)
    if error:
        warnings.append(error)
    records = (payload or {}).get('workflow_runs') or []
    runs = normalize_runs(records, limit=50)
    image, image_errors = inspector(repo)
    warnings.extend(image_errors)
    info, info_error = fetcher(repo, '', token)
    if info_error:
        warnings.append(info_error)
    return {
        'schema_version': 1,
        'generated_at': utc_now(),
        'source': 'GitHub REST API + docker image inspect (sin inferencia)',
        'repository': {'name': repo, 'url': f'https://github.com/{repo}',
                       'description': str((info or {}).get('description') or 'Metadata Action con análisis DevOps asistido por Gemini')[:240],
                       'visibility': 'public' if (info or {}).get('private') is False else 'no verificada'},
        'status': 'synced' if not error else 'partial',
        'runs': runs,
        'stats': summarize(runs),
        'image': image,
        'warnings': warnings,
        'links': {
            'actions': f'https://github.com/{repo}/actions',
            'ci': f'https://github.com/{repo}/actions/workflows/ci.yml',
            'ai': f'https://github.com/{repo}/actions/workflows/ai-devops.yml',
            'docker': f'https://github.com/{repo}/actions/workflows/demo-imagen-ghcr.yml',
            'inspector': f'https://github.com/{repo}/actions/workflows/inspeccionar-imagen-ghcr.yml',
            'issues': f'https://github.com/{repo}/issues',
            'security': f'https://github.com/{repo}/security',
            'package': image['package_url'],
        },
        'security_note': 'No se publican claves, logs internos ni contenido sin revisión de informes IA.',
    }


def write_site(snapshot: dict, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / 'data').mkdir(parents=True, exist_ok=True)
    for filename in ('index.html', 'styles.css', 'app.js'):
        shutil.copy2(ROOT / 'dashboard' / filename, output / filename)
    (output / '.nojekyll').write_text('', encoding='utf-8')
    (output / 'data' / 'dashboard.json').write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description='Publicar panel estático DevOps seguro')
    parser.add_argument('--repo', default=os.getenv('GH_REPOSITORY', 'Ryob1239/metadata-action-IA'))
    parser.add_argument('--output', default='_site')
    parser.add_argument('--fixture', help='JSON real capturado anteriormente para prueba local, no consulta API')
    parser.add_argument('--no-docker', action='store_true', help='No descargar la imagen (pruebas)')
    args = parser.parse_args()
    if args.fixture:
        snapshot = json.loads(Path(args.fixture).read_text(encoding='utf-8'))
    else:
        def mock_inspector(repo):
            return inspect_image_placeholder(repo), ['Inspección Docker desactivada para esta ejecución local.']
        snapshot = build_snapshot(args.repo, os.getenv('GH_TOKEN', ''),
                                  inspector=mock_inspector if args.no_docker else inspect_image)
    write_site(snapshot, Path(args.output))
    print(f'Panel generado en {args.output}; estado {snapshot.get("status")}; runs {len(snapshot.get("runs", []))}')
    return 0


def inspect_image_placeholder(repo):
    owner, name = repo.lower().split('/', 1)
    return {'reference': f'ghcr.io/{owner}/{name}-demo:latest',
            'package_url': f'https://github.com/{repo}/pkgs/container/{name}-demo',
            'available': False, 'digest': None, 'labels': {}, 'tags': [],
            'architecture': None, 'size_bytes': None}


if __name__ == '__main__':
    sys.exit(main())
