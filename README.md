# Calendario de Ministerios · Iglesia Northwood

Calendario 2027 donde cada director agrega los eventos de su ministerio (ensayos, salidas, retiros)
sobre los eventos de la iglesia, con avisos de conflicto que no bloquean.

- **Sin contraseña:** cualquiera ve los eventos de todos los ministerios y de la iglesia.
- **Con la contraseña (una sola para todos los directores):** se ven los conflictos y los nombres,
  y el director elige su ministerio para crear, cambiar o borrar solo los eventos de ese ministerio.

## Estructura del repo `calendario-ministerios`

| Archivo | Qué es |
|---|---|
| `index.html` | La página |
| `ministerios.json` | Ministerios, colores, equipos de Planning Center que pertenecen a cada uno, horarios de servicio |
| `datos/<ministerio>.json` | Eventos de cada ministerio (un archivo por ministerio, para que nadie pise lo de otro) |
| `equipos.enc.json` | Quién sirve en qué equipo, **cifrado** con la contraseña. Lo genera la Action cada lunes |
| `editor.json` | Token de GitHub cifrado con la contraseña (se crea en el primer "Entrar") |
| `automatizacion/build.py` | Lee Planning Center y cifra la lista de equipos |
| `.github/workflows/actualizar.yml` | Corre `build.py` cada lunes (o a mano) |

Los eventos de la iglesia se leen en vivo de `danielsc1012/calendario-northwood/eventos.json`.

## Puesta en marcha

1. Crear el repo público `danielsc1012/calendario-ministerios` con estos archivos y activar GitHub Pages (rama `main`, raíz).
2. Secretos (Settings → Secrets and variables → Actions): `PCO_APP_ID`, `PCO_SECRET` (los mismos del Portal Voluntarios) y `EDIT_PASSWORD` (la contraseña de los directores).
3. Correr la Action "Actualizar equipos desde Planning Center" una vez a mano.
4. Abrir la página → Entrar → pegar un token fine-grained (solo este repo, Contents: Read and write, 1 año) y usar **la misma** contraseña de `EDIT_PASSWORD`.

## Agregar un ministerio
Añadirlo en `ministerios.json` con sus equipos de Planning Center, y crear `datos/<id>.json` con `{"ministerio":"<id>","eventos":[]}`.
