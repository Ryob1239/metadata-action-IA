/**
 * Verificador OCI de Metadata Action IA.
 * Esta imagen valida ejecución y metadatos; no es un servicio web ni aloja Gemini.
 */
const version = process.env.BUILD_VERSION || 'sin-versión-específica';
const payload = {
  proyecto: 'Metadata Action IA',
  componente: 'Validación ejecutable de imagen OCI',
  versionGenerada: version,
  ejecutado: true,
  tipoDeArtefacto: 'contenedor OCI versionado en GitHub Container Registry',
  finalidad: 'Comprobar que la imagen publicada arranca y produce una salida verificable',
  integracion: {
    metadatos: 'Etiquetas y labels generados por Metadata Action (GitHub Actions)',
    inteligenciaArtificial: 'Análisis consultivo independiente mediante Google Gemini API'
  },
  entorno: {
    runtime: process.version,
    plataforma: process.platform,
    arquitectura: process.arch
  },
  observacion: 'El contenedor no expone puertos ni realiza inferencias de IA; esas funciones se ejecutan desde workflows independientes.'
};
console.log(JSON.stringify(payload, null, 2));
