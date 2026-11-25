# Imagen OCI · Metadata Action IA

## Ficha del artefacto publicado

| Campo | Descripción |
|---|---|
| **Producto** | Metadata Action IA |
| **Nombre del paquete** | `metadata-action-ia-demo` (nombre conservado por compatibilidad con las versiones publicadas) |
| **Registro** | GitHub Container Registry (`ghcr.io`) |
| **Referencia** | `ghcr.io/ryob1239/metadata-action-ia-demo:latest` |
| **Origen del código** | Repositorio `Ryob1239/metadata-action-IA`, rama principal `main` |
| **Tipo** | Imagen OCI ejecutable para validación de integración y entrega continua |
| **Entorno** | Node.js en una imagen Alpine; usuario sin privilegios de root |
| **Actualización** | Publicación automatizada desde `main` una vez validado el flujo |
| **Trazabilidad** | Tags de rama/commit, digest inmutable y labels OCI |
| **Licencia del repositorio** | Apache-2.0 |

## Descripción profesional

**Metadata Action IA — OCI Runtime Validation** es un artefacto de verificación publicado mediante el pipeline de entrega continua. Durante la construcción, la Action de metadatos genera tags y etiquetas OCI a partir del contexto de Git y GitHub. El contenedor valida de forma reproducible que la imagen publicada es ejecutable y muestra un resultado JSON comprobable.

**Alcance:** este contenedor no funciona como una API, un servidor HTTP ni un cliente de Google Gemini. La inteligencia artificial analiza información de GitHub mediante un workflow independiente con autorización controlada; el sitio web de GitHub Pages visualiza metadatos públicos y enlaza a los informes.

## Ejecutar directamente desde GitHub (sin Docker Desktop)

1. Abrir [Docker | Ejecutar e inspeccionar imagen GHCR](https://github.com/Ryob1239/metadata-action-IA/actions/workflows/inspeccionar-imagen-ghcr.yml).
2. Seleccionar **Run workflow**, rama `main` y etiqueta `latest` (o `main` / `sha-<commit>`).
3. Abrir el job **Descargar, ejecutar e inspeccionar imagen OCI**.
4. Consultar su **Summary** y descargar el artefacto `inspeccion-ghcr-*` que contiene JSON y Markdown.

Se comprueban el `docker pull`, el arranque del contenedor y la presencia del campo `ejecutado: true`, el contenido no sensible del sistema de archivos y la inspección de los labels/digest.

## Uso local opcional

```bash
docker pull ghcr.io/ryob1239/metadata-action-ia-demo:latest
docker run --rm ghcr.io/ryob1239/metadata-action-ia-demo:latest
docker image inspect --format '{{json .Config.Labels}}' ghcr.io/ryob1239/metadata-action-ia-demo:latest
```

## Identificación y estados

- `latest` y `main` corresponden a referencias móviles que pueden cambiar con la siguiente publicación.
- `sha-...` identifica la revisión de Git utilizada para etiquetar un build.
- Un digest `sha256:...` identifica un artefacto OCI inmutable.
- La imagen se considera disponible cuando se puede descargar e inspeccionar desde GHCR.
- No se presentan métricas ni números falsos cuando GitHub API / Docker no responden.

## Seguridad y trazabilidad

El pipeline de publicación utiliza `packages: write` **únicamente** en el job de entrega autorizado de `main`. Las verificaciones de Pull Request no publican. La consulta y la ejecución de imagen tienen permisos de lectura. No se incluyen tokens de GitHub ni claves de Gemini en la imagen o el dashboard.

## Evidencias para el reporte académico

**CD-01**: Ejecución exitosa de entrega continua en Actions.  
**CD-02**: Página del paquete GHCR con `latest`, `main` y tags SHA.  
**CD-03**: Summary del workflow del inspector con salida JSON del contenedor.  
**CD-04**: Digest y etiquetas de la imagen desde `docker image inspect`.
