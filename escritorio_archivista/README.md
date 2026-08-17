# Sistema de Gestión y Fragmentación Documental (SGFD)

Aplicación profesional de escritorio para la **gestión, análisis, validación y fragmentación de documentos notariales históricos** digitalizados en PDF.

Organiza los fragmentos en una jerarquía archivística de 11 niveles de carpetas y detecta automáticamente inconsistencias en la numeración de folios, registros, escribanos y protocolos.

## Características

- **Carga de inventarios Excel** (`xlsx`): registros, folios, fechas, tópica e interesados con detección de metadatos (acervo, escribano, siglo).
- **Editor PDF maestro**: vista previa de página, miniaturas, exclusión y reordenamiento de hojas.
- **Mapeo folio → página PDF**:
  - Posición renumerada al excluir/reordenar hojas (coincide con el editor).
  - Rangos manuales de páginas y registros que comparten hoja.
  - Respeto de exclusiones y segmentos.
- **7 analizadores de calidad** de datos:
  | Analizador | Qué detecta |
  |---|---|
  | Folios | Formato, repetidos, solapamiento y saltos (con folio esperado r/v) |
  | Data Tópica | Lugares de la columna de tópica |
  | Data Crónica | Mes fuera de rango, años inválidos y regresión cronológica |
  | Cobertura PDF | PDF insuficiente para el inventario |
  | N° Registro | Vacíos, formato no numérico y fuera de orden |
  | Escribano | Vacíos y nombres anormales |
  | Protocolo | Vacíos, formato no numérico y regresión por escribano |
- **Sugerencias de corrección**: modal de edición, historial de deshacer/rehacer por analizador y validación de incidencias.
- **Fragmentación** del PDF maestro en documentos individuales con jerarquía de 11 niveles.
- **Consola de logs** en vivo, guardado de sesiones y tema claro/oscuro.

## Requisitos

- Python 3.13+
- Dependencias: ver [`requirements.txt`](requirements.txt)

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Arquitectura

Clean Architecture + MVVM:

```
Presentación (PySide6) → Aplicación (Use Cases) → Dominio (Entidades, Servicios) ← Infraestructura
```

```
src/
├── domain/          # Entidades, puertos y servicios puros (analizadores, mapeo folio→página)
├── application/     # Casos de uso y DTOs (carga, análisis, exclusiones, fragmentación)
├── infrastructure/  # Implementaciones (PDF, Excel, jerarquía de carpetas)
└── presentation/    # PySide6: vistas, viewmodels, widgets y tema
```

## Jerarquía de carpetas de fragmentación

Los documentos se organizan en 11 niveles (los niveles 1–9 en mayúsculas; 10 y 11 conservan la grafía de la columna):

```
ACERVO DOCUMENTAL NUMERO {n}/
└─ SIGLO {romano}/
   └─ FONDO DOCUMENTAL/
      └─ {ESCRIBANO}/
         └─ {año}/
            └─ PROTOCOLO {n}/
               └─ REGISTRO {n}/
                  └─ {TÍTULO}/
                     └─ {mes}/
                        └─ {interesado1}/
                           └─ {interesado2}.pdf
```

## Testing

```bash
pytest tests/ -v
```
