# Analista DevOps asistido por IA — Especificación y operación

## 1. Propósito y alcance

La herramienta complementa a Docker Metadata Action con análisis consultivo para las **nueve áreas** del reporte académico: desarrollo, pruebas, integración, entrega, puesta en marcha, supervisión, infraestructura como código, mantenimiento y gestión Kanban. No cambia la generación determinista de etiquetas Docker. Su actividad es: **recopilar evidencia autorizada de GitHub, minimizarla, llamar a Gemini y elaborar recomendaciones explicables**.

## 2. Componentes

| Componente | Función | Tipo |
|---|---|---|
| `src/` y `dist/index.cjs` | Motor original de etiquetas/labels | Existente, sin cambios |
| `tools/ai_devops.py` | Cliente de lectura de GitHub, sanitización, consulta Gemini, informes | Actualizado |
| `.github/workflows/ai-devops.yml` | Ejecución manual con consentimiento y token de solo lectura | Actualizado |
| `.github/workflows/ai-pruebas.yml` | Verificación automática local de seguridad y resiliencia | Actualizado |
| `tests_ai/test_ai_devops.py` | Casos de prueba sin red ni claves | Actualizado |
| `.github/workflows/demo-imagen-ghcr.yml` | Construcción/publicación de la imagen OCI existente | Conservado |

## 3. Selección de fuente y objetivo

| Área | Evidencia | Parámetro `target` |
|---|---|---|
| `desarrollo`, `pruebas`, `mantenimiento` | Issue individual o lista de issues abiertos | Número de Issue o vacío |
| `ci`, `supervision` | Ejecución y pasos de workflow | ID de run o vacío = última ejecución completada excluyendo el propio asistente |
| `entrega`, `despliegue` | Release publicada | Tag o vacío = última release |
| `iac` | Pull Request y diff de YAML/HCL/Dockerfile | Número de PR obligatorio |
| `kanban` | Issues abiertos y etiquetas | Vacío |

## 4. Ejecución real en GitHub

- Accede a **Actions → Análisis inteligente DevOps → Run workflow**.
- Selecciona rama `main`, área y `target` si procede.
- El workflow verifica que exista el secreto `GEMINI_API_KEY` y consulta recursos con el token estándar `GITHUB_TOKEN`, sin permisos de escritura.
- Revisa la pestaña **Summary** y descarga `analisis-devops-<run_id>`. Debe incluir `informe-devops.md` y `informe-devops.json`.
- Solo considera completada la inferencia si aparece **`IA_REAL_EJECUTADA`**. El archivo conserva estado de error en caso de fallo y el job termina rojo.

## 5. Ejecución local y pruebas

```bash
python3 -m unittest discover -s tests_ai -v
python3 -m py_compile tools/ai_devops.py
```

Consulta sin red (solo para comprobar generación de archivos; no representa IA):

```bash
python3 tools/ai_devops.py --mode mantenimiento --input-file tests_ai/fixtures/issue.json --dry-run --output artifacts/control-local.md
```

Para análisis real en un equipo autorizado, utiliza variables de entorno `GITHUB_TOKEN`, `GITHUB_REPOSITORY`, `GEMINI_API_KEY` y opcional `GEMINI_MODEL`; **no** guardes credenciales en archivos de código ni las muestres en capturas.

## 6. Fallos y recuperación

| Código/condición | Comportamiento | Acción recomendada |
|---|---|---|
| Falta `GEMINI_API_KEY` | El job falla antes de invocar IA | Crear/renovar secreto en GitHub |
| HTTP 400 | Falla sin reintento | Revisar modelo y parámetros |
| HTTP 404 | Falla sin reintento | Revisar modelo permitido/proyecto |
| HTTP 429 con cuota cero | Falla sin reintento inútil | Consultar cuotas de AI Studio |
| HTTP 429 temporal | Reintentos limitados | Revisar RPM/RPD/TPM y frecuencia |
| HTTP 503, 502, 504, 500 | Reintentos con backoff/jitter | Revisar servicio y repetir tras estabilización |
| Sin output del modelo | Falla, sin reporte falsamente exitoso | Revisar disponibilidad, filtros y respuesta |
| Repo privado sin autorización | Falla antes de envío a Gemini | Revisar consentimiento y política de datos |
| Issue/PR/run inexistente | Falla con razón legible | Comprobar ID y permisos |

## 7. Seguridad y privacidad

- Solo lectura en GitHub (`contents`, `issues`, `pull-requests`, `actions`).
- Limita tamaño de evidencia y redacta patrones comunes de secretos; no garantiza detección exhaustiva.
- La entrada externa se trata como **contenido no confiable**: no se obedecen instrucciones del Issue, commit o PR.
- Un repositorio público también puede contener datos sensibles; el operador debe revisar la información que autoriza a enviar.
- En repositorios privados se requiere habilitar explícitamente `allow_private_data`. Consulta los términos de uso del nivel gratuito del proveedor antes de hacerlo.
- Nunca autoriza merges, releases, publicación de imágenes, cierre de alertas ni modificación de tags.

## 8. Política de mantenimiento y calidad

1. Registrar mejoras y defectos mediante Issues.
2. Agregar pruebas unitarias sin conexión para cada error corregido (especialmente HTTP 429/503 y privacidad).
3. Abrir PR a `main`, comprobar suite de IA y verificaciones originales.
4. No modificar `src/` ni `dist/index.cjs` salvo necesidad demostrada y controles separados.
5. Verificar luego con una ejecución real del workflow y conservar el enlace al run; nunca confundir simulación local con inferencia de proveedor.
6. Revisar periódicamente cuotas, cambios de modelo, dependencias y resultados de seguridad.

## 9. Definición de terminado

La mejora se considerará integrada cuando: el PR pase pruebas, se haga merge autorizado a `main`, el workflow real funcione al menos una vez con `IA_REAL_EJECUTADA`, el informe pueda descargarse y el pipeline de Docker/Metadata Action conserve sus resultados esperados.
