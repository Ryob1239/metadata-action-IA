// Demostración de ejecución de un programa desde repositorio y dentro de Docker.
// El programa real de metadata-action se ejecuta por separado mediante 'uses: ./'.
const version = process.env.BUILD_VERSION || 'local';
const payload = {
  proyecto: 'Docker Metadata Action - ejemplo de consumo',
  versionGenerada: version,
  ejecutado: true,
  proposito: 'Verificar una imagen Docker con tags/labels de Metadata Action'
};
console.log(JSON.stringify(payload, null, 2));
