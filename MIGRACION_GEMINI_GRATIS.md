# Migración de OpenAI API a Google AI Studio (Gemini API)

**Se conserva intacto el código de Docker Metadata Action**: `src/`, `dist/`, `action.yml`,
Docker Bake y los workflows originales. El cambio ocurre en la capa consultiva de IA.

## Configuración (sin tarjeta para la modalidad gratuita, cuando esté disponible)

1. Abre https://aistudio.google.com/app/apikey y crea una clave de Gemini API.
2. En GitHub abre **Settings > Secrets and variables > Actions**.
3. Crea el secreto de repositorio `GEMINI_API_KEY` y pega la clave de AI Studio.
   El anterior secreto `OPENAI_API_KEY` ya no se usa por este asistente.
4. Haz push de estos archivos al repositorio, crea un Pull Request y verifica
   que la suite `ai-pruebas.yml` termine correctamente.
5. En **Actions > IA DevOps - informe consultivo > Run workflow**,
   deja `demo_sintetica=true` para demostrar **IA real** sobre un caso ficticio,
   sin compartir Issues privados. Para analizar los 9 temas del **repositorio real**,
   cambia `demo_sintetica=false`, elige `mode` y `target` cuando corresponda.
6. Si el repositorio es **privado** y desactivas el modo sintético, el checkbox
   `allow_private_data` debe marcarse
   **únicamente si autorizas enviar los datos consultados a Google**. Para nivel
   gratuito Google puede usar contenido para mejorar sus productos: no envíes
   secretos, información confidencial ni logs privados sensibles. Si NO lo autorizas,
   obtendrás `NO_EJECUTADA_PRIVACIDAD` (esto es intencional).
7. Consulta **Actions > último run > Summary** y descarga el artefacto
   `informe-ia-devops-...`. Busca la marca `IA_REAL_EJECUTADA`.

**Modelo predeterminado actualizado (16-nov-2026)**: `gemini-3.5-flash-lite` (nivel gratuito sujeto a cuota y disponibilidad del proyecto). Google restringe el acceso de nuevos usuarios a modelos de la familia 2.5. El endpoint `generateContent` sigue soportado, aunque Google recomienda migrar progresivamente a Interactions API.
No requiere activar Vertex AI ni Cloud Billing para su uso en modalidad gratis.
No se garantiza que funcione gratuitamente para todas las cuentas/regiones.

### Ejemplo sin enviar datos de un repositorio privado

```bash
export GEMINI_API_KEY='TU_CLAVE_SOLO_EN_TU_EQUIPO'
python3 tools/ai_devops.py --mode mantenimiento \
  --input-file examples/ia/issue-mantenimiento.json \
  --output artifacts/informe-ejemplo-ia-real.md
```

Este comando **sí** realiza una llamada real de IA si la clave funciona, pero
usa datos de ejemplo: repórtalo como ejemplo sintético, no como análisis de
incidencias reales del repositorio.

### Pruebas sin consumo de IA

```bash
python3 -m unittest discover -s tests_ai -v
```

### Posibles errores

- `403`: comprueba la clave y permisos del proyecto de Google AI Studio.
- `404`: comprueba el nombre y disponibilidad del modelo en tu cuenta.
- `429`: cuota de solicitudes o tokens agotada; revisa el panel de límites y espera.
- `NO_EJECUTADA_SIN_CLAVE`: falta secreto `GEMINI_API_KEY`.
- `NO_EJECUTADA_PRIVACIDAD`: no se autorizó compartir datos de repositorio privado.

Referencias: https://ai.google.dev/gemini-api/docs/pricing y
https://ai.google.dev/gemini-api/terms

## Incidencia real: modelo 2.5 ya no disponible para nuevas cuentas (HTTP 404)

En el workflow de GitHub Actions el error `NOT_FOUND` para `gemini-2.5-flash-lite` no era un problema del secreto ni del cupo por minuto: Google informó que el modelo anterior no está disponible para usuarios nuevos. Esta corrección actualiza el valor de `GEMINI_MODEL` y el valor predeterminado en `tools/ai_devops.py` a `gemini-3.5-flash-lite`, además de actualizar los tests. Debe validarse con una solicitud real a Gemini desde GitHub Actions.

Para la evidencia académica, conserva capturas del error anterior y del resultado posterior, distinguiendo respuesta real `IA_REAL_EJECUTADA` de pruebas offline. La corrida de GHCR de `main` es independiente del asistente IA.
