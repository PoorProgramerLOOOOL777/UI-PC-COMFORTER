# UI-PC-COMFORTER

Asistente de escritorio para Windows: avatar personalizable, activación por voz **«oye PC»**, voces Edge TTS, personalidad y tarea/atajos configurables.

## Privacidad
- La escucha de la palabra de activación usa Vosk **localmente**. El audio de reconocimiento no se guarda en archivos ni se envía a servidores.
- Edge TTS sintetiza la voz usando el servicio de Microsoft: para generar el audio, el texto de respuesta se envía a ese servicio. El audio generado se reproduce desde un archivo temporal y se elimina al terminar.
- Si quieres síntesis completamente offline, selecciona **Voz local (Windows)**; utiliza las voces instaladas en Windows.
- No se graba audio de forma permanente. El programa muestra un indicador «Escuchando localmente».

## Instalación rápida
1. Extrae el ZIP.
2. Ejecuta `INSTALAR.bat` (no requiere administrador).
3. El instalador crea un entorno Python y descarga el modelo español pequeño de Vosk.
4. Ejecuta el acceso directo **PC Comforter** que se crea en el escritorio.

Requisitos: Windows 10/11, Python 3.10–3.12 instalado y marcado `Add Python to PATH`, micrófono y conexión durante la instalación (para descargar dependencias/modelo y usar Edge TTS). Para voz local, configura una voz de Windows.

## Uso
- Di **«oye PC»**. El asistente abre una ventana y escucha un comando durante unos segundos.
- También puedes escribir en la caja de texto.
- Comandos de ejemplo: «abre el bloc de notas», «abre calculadora», «abre navegador», «qué hora es», «apaga la escucha».
- Personaliza avatar (selecciona PNG/JPG/GIF), nombre, voz, personalidad y tarea favorita en Ajustes.
- El campo «Tarea personalizada» sirve como prompt de estilo/contexto; este prototipo no conecta con un modelo de IA remoto ni interpreta tareas libres complejas. Las órdenes locales son una lista segura de acciones.

## Seguridad
- El proyecto incluye comprobaciones de integridad SHA-256 para sus archivos principales. Si detecta cambios inesperados, los señala y evita el modo de escucha automática hasta que confirmes.
- Las acciones locales están limitadas a una lista de aplicaciones y no ejecutan comandos arbitrarios, PowerShell, scripts ni borrado de archivos.
- Antes de acciones sensibles no hay ejecución automática. No se realizan cambios de sistema, no se instala como servicio y no crea persistencia oculta.
- Puedes desactivar el inicio automático desde Ajustes.

## Desinstalación
Ejecuta `DESINSTALAR.bat`. Elimina el entorno, el modelo y el acceso directo; conserva `config.json` y el avatar. Borra la carpeta manualmente si quieres eliminar los ajustes.

## Compilar ejecutable (opcional)
`BUILD_EXE.bat` intenta generar un ejecutable con PyInstaller. La versión Python instalada por el instalador es la ruta recomendada.
