'use strict';

// Dashboard público: no se exponen credenciales ni se invoca Gemini desde el navegador.
// globalThis permite acceder al DOM sin alterar la configuración ESLint del proyecto Node.js.
const byId = id => globalThis.document.getElementById(id);

const stateIcon = state => {
  if (state === 'success') return '✓';
  if (state === 'failure') return '×';
  return '•';
};

const stateClass = state => {
  if (state === 'success') return '';
  if (state === 'failure') return ' failure';
  return ' other';
};

const statusText = state => {
  const statuses = {
    success: 'Exitoso',
    failure: 'Fallido',
    cancelled: 'Cancelado',
    skipped: 'Omitido',
    pending: 'Pendiente'
  };
  return statuses[state] || 'En curso';
};

function dateText(value) {
  if (!value) return 'Sin fecha';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Fecha no disponible';
  return date.toLocaleString('es-MX', {dateStyle: 'medium', timeStyle: 'short', timeZone: 'UTC'}) + ' UTC';
}

function setText(id, value) {
  const element = byId(id);
  if (element) element.textContent = String(value ?? '—');
}

function link(id, url) {
  if (typeof url !== 'string' || !url.startsWith('https://github.com/')) return;
  const element = byId(id);
  if (element) element.setAttribute('href', url);
}

function createElement(tag, className, text) {
  const node = globalThis.document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = String(text);
  return node;
}

function safeRun(run) {
  return Boolean(run && typeof run.url === 'string' && run.url.startsWith('https://github.com/'));
}

function renderRow(item, type) {
  let className = 'run-row';
  if (type === 'ai') className = 'ai-row';
  if (type === 'security') className = 'security-row';

  const row = createElement('div', className);
  const icon = createElement('div', 'row-state' + stateClass(item.conclusion), stateIcon(item.conclusion));
  const description = createElement('div', 'row-description');
  description.append(createElement('strong', '', item.name || 'Workflow de GitHub Actions'));

  const details = [statusText(item.conclusion), item.branch || 'rama desconocida', dateText(item.created_at)].join(' · ');
  description.append(createElement('small', '', details));

  const externalLink = createElement('a', 'row-link', '↗');
  externalLink.href = item.url;
  externalLink.target = '_blank';
  externalLink.rel = 'noopener noreferrer';
  externalLink.setAttribute('aria-label', 'Ver ejecución en GitHub');
  row.append(icon, description, externalLink);
  return row;
}

function rowsTo(target, runs, count, type) {
  const node = byId(target);
  if (!node) return;
  node.replaceChildren();

  const entries = runs.filter(safeRun).slice(0, count);
  if (!entries.length) {
    node.append(createElement('div', 'empty', 'No hay ejecuciones disponibles dentro de la muestra consultada.'));
    return;
  }

  for (const item of entries) {
    node.append(renderRow(item, type));
  }
}

function setSync(status) {
  const indicator = byId('sync-indicator');
  if (!indicator) return;

  let suffix = ' error';
  let message = '● Sin datos actualizados';
  if (status === 'synced') {
    suffix = '';
    message = '● Datos sincronizados';
  } else if (status === 'partial') {
    suffix = ' pending';
    message = '● Sincronización parcial';
  }

  indicator.className = 'sync-pill' + suffix;
  indicator.textContent = message;
}

function render(data) {
  const runs = Array.isArray(data.runs) ? data.runs : [];
  const stats = data.stats || {};
  const links = data.links || {};
  const image = data.image || {};
  const repository = data.repository || {};
  const synchronized = data.status === 'synced' || data.status === 'partial';

  setSync(data.status);
  setText('last-sync', 'Actualizado: ' + dateText(data.generated_at));
  setText('metric-total', synchronized && Number.isFinite(stats.total) ? stats.total : '—');
  setText('metric-success', synchronized && Number.isFinite(stats.success) ? stats.success : '—');
  setText('metric-failed', synchronized && Number.isFinite(stats.failure) ? stats.failure : '—');

  let successNote = 'Sin datos actualizados';
  if (runs.length) {
    successNote = Math.round(((stats.success || 0) / runs.length) * 100) + '% de la muestra consultada';
  }
  setText('metric-success-note', successNote);

  setText('metric-image', image.available ? 'Publicada' : 'Sin verificar');
  setText('image-badge', image.available ? 'Inspeccionada' : 'No verificada');
  const badge = byId('image-badge');
  if (badge) badge.className = 'badge' + (image.available ? '' : ' neutral');

  if (image.reference) setText('image-ref', image.reference);
  setText('image-arch', image.available ? [image.os, image.architecture].filter(Boolean).join(' / ') : 'Pendiente de inspección');
  setText('image-digest', image.digest || 'No disponible');

  const imageDescription = (image.labels || {})['org.opencontainers.image.description'];
  setText('image-description', imageDescription || 'Imagen OCI ejecutable de validación; la inferencia Gemini se realiza en GitHub Actions.');
  const shaTag = Array.isArray(image.tags) ? image.tags.find(tag => tag.startsWith('sha-')) : undefined;
  setText('sha-tag', shaTag || 'SHA pendiente');

  rowsTo(
    'run-list',
    runs.filter(run => ['ci', 'cd', 'other'].includes(run.category)),
    6,
    'run'
  );
  rowsTo(
    'ai-runs',
    runs.filter(run => run.category === 'ai'),
    4,
    'ai'
  );
  rowsTo(
    'security-runs',
    runs.filter(run => run.category === 'security'),
    4,
    'security'
  );

  const bindings = {
    'nav-repo': repository.url,
    'head-github': repository.url,
    'nav-actions': links.actions,
    'hero-actions': links.actions,
    'nav-package': links.package,
    'hero-package': links.package,
    'package-link': links.package,
    'ci-link': links.ci,
    'ai-link': links.ai,
    'security-link': links.security,
    'inspect-link': links.inspector
  };
  for (const [id, url] of Object.entries(bindings)) {
    link(id, url);
  }

  const warningContainer = byId('warnings');
  if (warningContainer) {
    warningContainer.replaceChildren();
    for (const warning of (data.warnings || []).slice(0, 3)) {
      warningContainer.append(createElement('p', '', `Aviso de datos: ${warning}`));
    }
  }
}

async function init() {
  try {
    const url = new URL('./data/dashboard.json', globalThis.location.href);
    const response = await fetch(url, {cache: 'no-store'});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    if (data.schema_version !== 1) throw new Error('Esquema desconocido');
    render(data);
  } catch {
    setSync('error');
    const message = 'Datos no disponibles. Ejecuta «Plataforma DevOps | Publicar dashboard GitHub Pages» desde Actions.';
    const warningContainer = byId('warnings');
    if (warningContainer) warningContainer.append(createElement('p', '', message));
  }
}

globalThis.addEventListener('DOMContentLoaded', init);
