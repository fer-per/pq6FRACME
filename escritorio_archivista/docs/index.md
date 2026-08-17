# Sistema de Gestión y Fragmentación Documental (SGFD)

Documentación del **Escritorio Archivista** — aplicación de escritorio para la
gestión, análisis, validación y fragmentación de documentos notariales
históricos digitalizados en PDF.

## Índice de documentación

| Documento | Contenido |
|---|---|
| [Manual de usuario](manual-usuario.md) | Cómo usar la aplicación paso a paso |
| [Reglas de negocio](reglas-negocio.md) | Jerarquía de carpetas, mapeo folio→página y criterios de los analizadores |
| [Arquitectura](arquitectura.md) | Estructura del código, capas y flujos de datos |

## Resumen rápido

1. **Paso 1** — Cargar el inventario Excel y el PDF original.
2. **Paso 2** — Ajustar los parámetros de mapeo (fila inicial, página PDF inicial).
3. **Paso 3** — Revisar la previsualización del inventario.
4. **Analizador** — Ejecutar los 7 analizadores de calidad y corregir/validar incidencias.
5. **Editor PDF** — Excluir o reordenar hojas del PDF maestro (opcional).
6. **Fragmentar** — Generar los documentos individuales en la jerarquía de carpetas.

## Módulos de la aplicación

| Módulo | Función |
|---|---|
| Espacio de Trabajo | Carga de archivos, parámetros de mapeo y previsualización |
| Analizador | Detección de inconsistencias con sugerencias de corrección |
| Fragmentar | Generación de los fragmentos PDF |
| Editor PDF | Exclusión y reordenamiento de hojas del PDF maestro |
| Documentación | Esta documentación, consultable desde la aplicación |
| Soporte | Ayuda y contacto |
