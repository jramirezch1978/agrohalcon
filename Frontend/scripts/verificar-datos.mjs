// Verificación de honestidad del dato (corre antes de cada build: `npm run test:datos`).
// Falla si:
//  1) un archivo de datos de EJEMPLO (src/services/mocks) usa el nombre de un producto real de la NASA;
//  2) en cualquier parte de src/ aparece SMAP, MODIS o NDVI (no se integran en AgroShift);
//  3) se usa la capa propietaria de Esri en el mapa.
import { readFileSync, readdirSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'

const RAIZ = new URL('..', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1')
const SRC = join(RAIZ, 'src')

function archivos(dir) {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n)
    return statSync(p).isDirectory() ? archivos(p) : /\.(ts|vue)$/.test(n) ? [p] : []
  })
}

const errores = []
const revisar = (lista, patron, motivo) => {
  for (const f of lista) {
    readFileSync(f, 'utf8').split('\n').forEach((linea, i) => {
      if (patron.test(linea)) errores.push(`${relative(RAIZ, f)}:${i + 1}  ${motivo}\n    ${linea.trim()}`)
    })
  }
}

const todos = archivos(SRC)
const mocks = archivos(join(SRC, 'services', 'mocks'))

revisar(mocks, /NASA POWER|GPM IMERG|IMERG|MUR SST|SMAP|MODIS|NDVI/, 'un dato de EJEMPLO no puede llevar el nombre de un producto de la NASA (usa "Ejemplo")')
revisar(todos, /\bSMAP\b|\bMODIS\b|\bNDVI\b/, 'SMAP, MODIS y NDVI no se usan en AgroShift: no deben aparecer')
revisar(todos, /arcgisonline|\bEsri\b/, 'la capa de Esri es propietaria: usa OpenStreetMap o NASA GIBS')

if (errores.length) {
  console.error(`\n✗ Verificación de datos: ${errores.length} problema(s)\n\n${errores.join('\n\n')}\n`)
  process.exit(1)
}
console.log(`✓ Verificación de datos: ${mocks.length} mocks y ${todos.length} archivos sin etiquetas falsas`)
