# Corrección de seguridad y diagnóstico Gemini (16 noviembre 2026)

El repositorio `metadata-action-IA` permanece **privado**. El fallo de los workflows `codeql` y `zizmor` observado en el PR #18 fue la imposibilidad de subir resultados a GitHub Code Scanning: **`Code scanning is not enabled for this repository`**. El análisis de CodeQL y la ejecución de Zizmor sí se realizaron hasta el paso de publicación del resultado. El error no era una vulnerabilidad confirmada ni el permiso `actions: read` por sí solo.

## Qué cambió

- `.github/workflows/codeql.yml`: en repositorios **públicos** conserva CodeQL; en repositorios **privados** el job CodeQL se omite y se ejecuta **Semgrep Community Edition** para analizar TypeScript y Python con reglas comunitarias. El reporte JSON se sube como *artifact*, sin usar Code Scanning. `--error` hace que el análisis falle si existen hallazgos; éstos deben revisarse y corregirse, no ocultarse.
- `.github/workflows/zizmor.yml`: sustituye un workflow reutilizable que intentaba subir SARIF por la acción oficial de Zizmor con `advanced-security: false`; muestra hallazgos en logs y anotaciones de GitHub Actions (hasta 10 por paso), sin subir SARIF. La ausencia de fallos del job **no prueba ausencia de riesgos**: leer las observaciones.
- `tools/ai_devops.py`: registra de forma limitada el campo `error.status` y `error.message` de respuestas HTTP como el **429**, sin imprimir API Key ni el contenido enviado al modelo.
- `tests_ai/test_ai_devops.py`: añade una prueba de diagnóstico 429 simulada.

## Cómo aplicar

Copiar los cuatro archivos a las mismas rutas del repositorio existente, abrir una rama `fix/seguridad-gemini`, hacer commit y Pull Request a `main`. Repetir los checks. **No** modificar `src/`, `dist/`, ni workflows de publicación. Ejecutar el análisis de IA después de comprobar la cuota real en Google AI Studio.

## Qué no cambió

Ni la generación determinista de `tags/labels`, ni la ejecución `uses: ./`, ni la publicación GHCR. Que el job GHCR salga `skipped` en un Pull Request **es intencional**: publica sólo tras un push válido a `main`.

## Correspondencia con el reporte académico

El PDF original nombra CodeQL. En el repositorio privado, **CodeQL queda condicionado a repositorio público**, y la revisión SAST se realiza con Semgrep CE. La documentación final debe reflejar esta diferencia; no se debe afirmar que CodeQL produjo un informe en el repositorio privado. Zizmor continúa analizando workflows, pero sus resultados se consultan en los logs/anotaciones, no en la pestaña Code Scanning.

## Sobre 429 de Gemini

HTTP 429 por sí solo no permite distinguir límite de solicitudes por minuto, de tokens, por día o cuota gratuita cero. Tras aplicar el parche, expandir `Analizar evidencia y generar informe` y consultar el detalle de la respuesta; revisar el mismo **proyecto de Google AI Studio** al que pertenece `GEMINI_API_KEY`. Si la cuota es cero, esperar no suele resolverlo; necesitarás un modelo/proyecto gratuito con cuota positiva o un servicio alternativo. No hay evidencia de inferencia real hasta que el informe muestre `IA_REAL_EJECUTADA`.
