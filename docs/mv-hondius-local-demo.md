# Demo local readonly de MV Hondius

Ficha React en `apps/web/src/app/page.tsx`, con selección de cinco señales,
ocho citas literales, dos publicaciones, tres relaciones dirigidas y cinco
membresías al evento. Permite descargar el snapshot e imprimir todas las señales
y citas, independientemente de la selección actual. No importa el cliente Supabase.

## Datos y procedencia

`apps/web/src/data/mv-hondius.snapshot.json` se capturó el 14 de octubre de 2026
a las 10:57 hora argentina en una transacción READ ONLY / REPEATABLE READ.
El exportador verifica el proyecto, el ID del evento, las cinco membresías y los
extremos de las tres relaciones, y selecciona columnas explícitas. No incluye
credenciales, usuarios revisores, payloads ni textos completos de documentos.

Los datos provienen de eventos, señales, evidencia, relaciones y raw_items
persistidos. Los ocho fragmentos conservan su texto literal; no hay página ni
posición registradas. La captura no contrastó nuevamente las citas contra las
versiones actuales de las páginas externas. El resumen de ocho casos no implica
ocho confirmados: una cita distingue seis confirmados y dos probables.

Las fechas desconocidas siguen como no disponibles. La cronología ordena por
publicación, no por ocurrencia ni primera detección. El estado activo, confianza
baja, prioridad P3 y revisión pendiente son valores del registro capturado.
No se afirma convergencia independiente entre sectores ni prioridad calibrada.
El commit base integrado `caa2598` no es el commit de las extracciones históricas,
que no está disponible en las filas. Se preservan sus extractores y modelos.

## Ejecución y controles

Con las dependencias del package-lock instaladas en la raíz:

```powershell
node node_modules/typescript/bin/tsc --project apps/web/tsconfig.json --incremental false
node --test --test-isolation=none apps/web/scripts/snapshot.test.cjs
npm run dev:web -- --hostname 127.0.0.1 --port 3015
```

En este equipo se reutilizaron las dependencias ya instaladas mediante una
junction local de node_modules hacia oeti-dev/node_modules; no se instalaron
paquetes ni se cambiaron archivos de ese directorio compartido.

La compilación webpack de Next aprobó; su build completo falló por falta de
memoria en el proceso de TypeScript y el dev server también falló por memoria.
El typecheck ejecutado por separado aprobó. No se omitió el control de tipos ni
se habilitó ignoreBuildErrors. `OETI_LOW_MEMORY=1` permite probar opciones locales
de menor concurrencia, sin alterar la configuración global del equipo.

Para revisar la misma página React con menor consumo, sin procesos de Next:

```powershell
node --max-old-space-size=256 apps/web/scripts/preview_demo.cjs
```

Sirve únicamente `127.0.0.1:3015`, index.html, CSS y el bundle. Compila el mismo
page.tsx y usa el mismo snapshot; los archivos generados van a out/ (ignorado).
`--build-only` compila sin abrir el puerto. Este helper usa el webpack incluido
en Next 16.3.3 para verificación local; no sustituye un build de producción y
puede requerir adaptación al actualizar Next. Ctrl+C detiene el servidor.

También genera `apps/web/out/demo/ficha-mv-hondius.html`, una ficha autónoma
con CSS y JavaScript incorporados que se puede abrir en un navegador sin servidor.
No hace peticiones a Supabase; los enlaces a fuentes solo se abren al seleccionarlos.
Comando abreviado desde la raíz: `npm --workspace apps/web run demo:preview`.

Las pruebas de snapshot comprueban conjuntos de IDs, extremos, evidencia por
señal, fechas desconocidas, procedencia y ausencia de campos sensibles.
No se repitió la suite worker porque no cambió su código.

## Recaptura deliberada

El navegador no consulta Supabase. Recapturar requiere acceso adecuado y una
lectura autorizada; no se hace automáticamente al arrancar o compilar la demo.
Con el Python y dependencias del worker, PYTHONPATH apuntando a su src:

```powershell
python apps/web/scripts/capture_demo_snapshot.py <ruta-env-local> <ruta-snapshot-json>
```

El script usa credenciales solo en memoria, suprime detalles potencialmente
sensibles de errores y tiene una transacción de solo lectura con timeout.
No verifica las opciones de signup ni el acceso efectivo de otros usuarios.

## Alcance pendiente

La implementación es local, sin commit, nueva rama ni publicación. Los ejemplos
de veto del benchmark están fuera de esta primera ficha del evento persistido;
no se mezclaron pares sintéticos con relaciones reales. Antes de una demo en
vivo o publicada quedan por verificar signup, acceso restringido y RLS desplegada.
La protección de main y el segundo caso holdout siguen pendientes por separado.
