# Corrección del HTTP 404 de Gemini (16 de noviembre de 2026)

**Problema comprobado en los registros:** la API responde `404 NOT_FOUND` porque `gemini-2.5-flash-lite` no está disponible para usuarios nuevos.

**Cambios:** `gemini-3.5-flash-lite` en `tools/ai_devops.py` y `.github/workflows/ai-devops.yml`, pruebas adaptadas y documentación actualizada. Se mantiene el endpoint `generateContent` admitido por Google, con la posibilidad de migrar a Interactions API más adelante.

**Instalación:** desde la raíz de tu clon, copia los cinco archivos manteniendo rutas y sobrescribiendo sus versiones anteriores. Crea una rama nueva, ejecuta `python3 -m unittest discover -s tests_ai -v`, realiza commit, push, Pull Request hacia `main` y, cuando pase CI, fusiona. Luego entra en **Actions > IA DevOps - informe consultivo > Run workflow**, deja `demo_sintetica=true` y ejecuta el workflow de `main` para comprobar una inferencia real. La clave `GEMINI_API_KEY` ya existente no tiene que regenerarse por este cambio.

**Resultado esperado:** artefacto `artifacts/informe-ia.md` con el marcador `IA_REAL_EJECUTADA`. Las pruebas locales usan un simulador, NO prueban el acceso remoto a Gemini. Si aparece un nuevo error 429 o 403, leer el mensaje exacto antes de cambiar el modelo.

**GHCR:** La ejecución desde `main` correspondiente al merge del PR #20 es distinta de las ejecuciones de Pull Requests de Dependabot. La publicación GHCR depende del evento de `main` y no debe forzarse desde un PR.

Fuentes: https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite y https://aistudio.google.com/docs/get-started
