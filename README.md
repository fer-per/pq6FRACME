# pq6FRACME

Sistema de Gestión y Fragmentación Documental (SGFD).

Aplicación de escritorio del archivista para **gestionar, analizar, validar y fragmentar documentos históricos digitalizados** (protocolos notariales) en PDF, organizando el resultado en una jerarquía archivística de 11 niveles.

## Módulo

El código fuente se encuentra en [`escritorio_archivista/`](escritorio_archivista/):

- Aplicación de escritorio en **Python + PySide6**, con arquitectura **Clean Architecture + MVVM**.
- **7 analizadores de calidad** (folios, tópica, crónica, cobertura PDF, registro, escribano y protocolo) con sugerencias de corrección.
- **Editor PDF maestro** con exclusión/reordenamiento de hojas y mapeo folio → página.
- **Fragmentación del PDF** en documentos individuales.
- Suites de pruebas con `pytest` (dominio, aplicación, infraestructura y presentación).

Consulta la [documentación del módulo](escritorio_archivista/README.md) para requisitos, instalación, ejecución y arquitectura.
