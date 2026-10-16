# CI de la demo web

El workflow `.github/workflows/web-checks.yml` propone el check `Web / Node 24`
en PR hacia main, push a main y ejecución manual, sin filtros por ruta.
Usa Ubuntu 24.04, Node 24.13.1 y acciones fijadas por SHA. Checkout no conserva
credenciales y el workflow solo solicita contents:read.

Instala el workspace web desde el package-lock raíz mediante npm ci, sin incluir
el paquete raíz ni instalar el CLI de Supabase para estas comprobaciones.
Ejecuta TypeScript sin emitir archivos, las tres pruebas del snapshot y el build
completo de Next con webpack. OETI_LOW_MEMORY=1 limita concurrencia y memoria
del compilador; no desactiva errores de TypeScript. Telemetría deshabilitada.

No consulta Supabase ni requiere secretos. Tampoco despliega, captura datos,
publica PDF o llama al LLM. El build contiene el snapshot local, como la demo.

El check de snapshot verifica integridad/procedencia de los datos congelados,
no calidad epidemiológica. El workflow no automatiza inspección visual ni el
diálogo de impresión. La CI del worker sigue separada. Agregar este archivo no
configura checks obligatorios ni protección de main.

Node está fijado a la versión usada para la validación local. Las actualizaciones
de runtime y de acciones deben revisarse explícitamente. npm ci usa las versiones
y hashes del lockfile; no congela el sistema operativo del runner.

## Validación local de la propuesta

El 16 de octubre de 2026 aprobaron TypeScript, las tres pruebas del snapshot
y el build completo Next 16.3.3 con webpack y Node 24.13.1, incluida generación
estática. El primer build no pudo crear subprocesos dentro del sandbox; la
repetición con permiso de ejecución aprobó. No se ejecutó npm ci sobre las
dependencias compartidas del equipo. La instalación limpia y la ejecución del
workflow en Ubuntu quedan por verificar en el PR. El archivo generado
next-env.d.ts se devolvió a su contenido previo tras el build.
