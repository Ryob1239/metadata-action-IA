# Plataforma Metadata Action IA: operación integral en GitHub

## Propósito

Este módulo complementa al repositorio original **sin sustituir `src/` ni `dist/index.cjs`**. Integra ejecución de imágenes OCI desde un runner, publicación de un dashboard en GitHub Pages y presentación de metadatos verificables de CI/CD, seguridad y Gemini. No requiere Docker Desktop local.

### Componentes

| Archivo | Función |
|---|---|
| `.github/workflows/inspeccionar-imagen-ghcr.yml` | Descarga la imagen pública, la ejecuta, inspecciona sus labels y conserva un artefacto. |
| `tools/inspeccionar_imagen.py` | Implementa la inspección con tags controlados, salida JSON y Markdown. |
| `.github/workflows/publicar-dashboard.yml` | Genera el dashboard y lo despliega con GitHub Pages (manual y cada seis horas). |
| `tools/generar_dashboard.py` | Consulta API de GitHub sólo con permisos de lectura; genera snapshot JSON estático. |
| `dashboard/` | Interfaz web responsive sin bibliotecas externas ni API Keys en navegador. |
| `tests_dashboard/` | Pruebas de categorización, validación, fallos de red y generación de sitio. |
| `examples/contenedor-demo/demo.mjs` | Salida profesional JSON del artefacto OCI, sin servidor HTTP. |
| `docs/GHCR_PACKAGE.md` | Descripción técnica profesional para el paquete GHCR. |

## Instalación

### Opción recomendada: instalador sobre tu clon actualizado

1. Descargar y extraer la actualización.
2. Tener un clon **actualizado** de `metadata-action-IA`. Antes de instalar, ejecutar en ese clon: `git switch main`, `git pull origin main` y `git switch -c feat/plataforma-github`.
3. Ejecutar en la carpeta de la actualización:
   ```bash
   python INSTALAR_PLATAFORMA.py --repo "RUTA/A/metadata-action-IA"
   ```
4. Revisar `git diff` antes de crear un commit. El instalador crea copias de seguridad de los archivos que modifica.
5. Ejecutar:
   ```bash
   python -m unittest discover -s tests_dashboard -v
   node examples/contenedor-demo/demo.mjs
   ```
6. Revisar el diff, hacer commit y push en la rama `feat/plataforma-github` ya creada; abrir PR hacia `main`, verificar CI, CodeQL y Zizmor, y fusionar sólo si todo está bien.

### Activar GitHub Pages (una sola vez)

En el repositorio público, abrir **Settings → Pages → Build and deployment → Source: GitHub Actions**. Sin esta configuración, el primer despliegue puede fallar aunque el proyecto esté correcto. Después ir a **Actions → Plataforma DevOps | Publicar dashboard GitHub Pages → Run workflow** con `main`.

Dirección prevista **después** de la publicación correcta: `https://ryob1239.github.io/metadata-action-IA/`.

La generación se ejecuta automáticamente tras cambios en el dashboard y a intervalos programados de seis horas (la programación puede retrasarse por GitHub); también se puede ejecutar manualmente. El dashboard **no es en tiempo real**: indica la hora de la última actualización.

### Ejecutar una imagen desde GitHub

Abrir **Actions → Docker | Ejecutar e inspeccionar imagen GHCR → Run workflow**. Elegir una etiqueta `latest`, `main` o `sha-<hash>`. El job devuelve salida JSON del programa, metadatos OCI y un artefacto descargable para tu reporte.

### Generar un análisis Gemini

Abrir **Actions → Análisis inteligente DevOps | Evidencia real → Run workflow**. Seleccionar `mode: ci` y un **run ID completo** (por ejemplo, `45536437337` para una ejecución histórica consultable). El informe se muestra en el Summary de esa ejecución y en sus Artifacts. La API Key se guarda en GitHub Secrets y nunca en Pages.

## Qué se muestra y qué no

**Visible en Pages:** estados públicos de los workflows, enlaces a ejecuciones, información de GHCR, digest, labels OCI permitidos, fecha de sincronización y accesos a informes de IA.

**No se publica en Pages:** claves API, tokens GitHub, texto completo de logs, datos privados, prompts, informes con contenido que no haya sido revisado, ni respuestas simuladas presentadas como reales.

Si la API de GitHub o Docker no responde, la interfaz lo indica como `sin verificar` o `sincronización parcial`. No se generan valores ficticios para ocultar fallos.

## Evidencias recomendadas (capturas)

| ID | Qué mostrar | Dónde |
|---|---|---|
| GH-01 | Página principal del dashboard con estado y hora de sincronización | **Settings → Pages → Visit site** |
| GH-02 | Workflows de CI con enlaces verificables | Dashboard → Integración continua |
| GH-03 | Imagen con tags, digest y descripción OCI | Dashboard → Entrega de contenedores |
| GH-04 | Ejecuciones IA y enlaces a reportes reales | Dashboard → Inteligencia artificial |
| GH-05 | Inspector `docker pull/run/inspect` exitoso | Actions → Docker | Ejecutar e inspeccionar imagen GHCR → Summary |
| GH-06 | Reporte descargable JSON/MD | Mismo run → Artifacts |
| GH-07 | Paquete publicado y versiones | Repositorio → Packages → metadata-action-ia-demo |
| GH-08 | Deploy de Pages exitoso | Actions → Plataforma DevOps → Desplegar sitio a GitHub Pages |

## Límites

La imagen existente sigue siendo una validación por terminal y **no expone un sitio web por un puerto**. El dashboard se aloja por separado mediante GitHub Pages; esto evita incluir secretos en una imagen pública. GitHub Pages es hosting estático y no realiza inferencia de IA directamente.
