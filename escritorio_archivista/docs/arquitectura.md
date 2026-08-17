# Arquitectura técnica

## Resumen

El proyecto sigue **Clean Architecture** combinado con **MVVM** en la capa de
presentación:

```
┌────────────────────────────────────────────────────────────┐
│  Presentación (PySide6)   — vistas, viewmodels, widgets     │
├────────────────────────────────────────────────────────────┤
│  Aplicación (Use Cases)   — casos de uso y DTOs             │
├────────────────────────────────────────────────────────────┤
│  Dominio                  — entidades, puertos, servicios   │
├────────────────────────────────────────────────────────────┤
│  Infraestructura          — PDF, Excel, sesiones, jerarquía │
└────────────────────────────────────────────────────────────┘
```

- **Dominio**: lógica pura sin dependencias externas (entidades, analizadores,
  mapeo de folios, puertos como contratos).
- **Aplicación**: orquesta los casos de uso (cargar, analizar, fragmentar,
  gestionar exclusiones y sesiones) y define los DTOs.
- **Infraestructura**: implementaciones concretas de los puertos (PyMuPDF/pypdf,
  pandas/openpyxl, repositorio de sesiones, constructor de jerarquía).
- **Presentación**: vistas PySide6 que se comunican con el ViewModel a través
  de señales, manteniendo la UI desacoplada de la lógica.

## Estructura de directorios

```
escritorio_archivista/
├── main.py                      # Punto de entrada
├── requirements.txt
├── conftest.py
├── docs/                        # Documentación (este sitio)
├── resources/
│   ├── icons/                   # Íconos de la interfaz
│   └── mapa_maestro.json        # Config externa: dónde viven los datos en el Excel
├── sesiones/                    # Configuraciones guardadas (.json + adjuntos)
└── src/
    ├── domain/
    │   ├── entities.py          # InventoryRecord, AnalysisResult, ExclusionRule...
    │   ├── value_objects.py     # Constantes y vocabulario del dominio
    │   ├── ports/               # Contratos: PDFServicePort, HierarchyBuilderPort
    │   └── services/
    │       ├── folio_parser.py  # Parseo de folios notariales (r/v)
    │       ├── folio_mapper.py  # Mapeo folio → página PDF
    │       ├── suggestion_generator.py
    │       └── analyzers/       # 7 analizadores de calidad
    ├── application/
    │   ├── container.py         # Inyección de dependencias
    │   ├── dto.py               # Objetos de transferencia
    │   └── use_cases/
    │       ├── load_inventory.py
    │       ├── analyze_data.py
    │       ├── manage_exclusions.py
    │       ├── fragment_pdf.py
    │       └── manage_session.py
    ├── infrastructure/
    │   ├── excel_repository.py  # Lectura del inventario (pandas/openpyxl)
    │   ├── pdf_service.py       # Render y extracción de páginas
    │   ├── session_repository.py
    │   ├── hierarchy_builder.py # Jerarquía de 11 niveles
    │   └── mapeo_maestro.py     # Carga de resources/mapa_maestro.json
    └── presentation/
        ├── app.py               # Factory de la aplicación
        ├── main_window.py       # Ventana principal + navegación
        ├── constants.py         # ViewId, rutas, íconos
        ├── viewmodels/          # AppState, Workspace, Analyzer, Process, PDFEditor
        ├── views/               # workspace, analyzer, process, pdf_editor, docs, support
        ├── widgets/             # data_table, sidebar, pdf_preview, log_console...
        └── theme/               # Paleta, fuentes, íconos, hoja de estilo
```

## Capa de dominio

### Entidades (`entities.py`)

- `InventoryRecord`: fila del inventario (registro, escribano, protocolo,
  folios, pg_pdf, fecha, interesados, tópica, estado…).
- `AnalysisError`: incidencia con `tipo`, `descripcion`, `valor_actual`,
  `valor_esperado` y `fatal`.
- `AnalysisResult`: resultado de un analizador (errores + advertencias).
- `ExclusionRule`: justifica saltos (`SALTO`) o marca hojas a ignorar
  (`IGNORAR`).
- `SugerenciaCorreccion`: corrección propuesta a partir de un error.

### Puertos (`ports/`)

Contratos que la infraestructura implementa, para que el dominio no dependa de
librerías concretas:

- `PDFServicePort`: abrir/cerrar PDF, renderizar páginas, extraer páginas.
- `HierarchyBuilderPort`: construir la ruta jerárquica de un registro.

### Servicios

- `folio_parser`: `parse_folios`, `folio_to_int`, `int_to_folio`,
  `format_folio`, `calculate_suggested_range`.
- `folio_mapper`: mapea cada registro a su rango de páginas, en modo físico o de
  posición renumerada, respetando exclusiones, rangos manuales y
  `comparte_hoja`. Expone `to_physical_pages` para traducir posiciones a
  páginas físicas antes de extraer.
- `analyzers/`: `folio_analyzer`, `topica_analyzer`, `cronica_analyzer`,
  `coverage_analyzer`, `registro_analyzer`, `escribano_analyzer`,
  `protocolo_analyzer`.
- `suggestion_generator`: convierte errores en `SugerenciaCorreccion`.

## Capa de aplicación

### Casos de uso

| Caso de uso | Responsabilidad |
|---|---|
| `CargarInventarioUseCase` | Lee el Excel, detecta metadatos y construye los registros |
| `AnalizarDatosUseCase` | Crea el mapper, recalcula `pg_pdf` y ejecuta los 7 analizadores |
| `GestionarExclusionesUseCase` | Agrega/elimina reglas de exclusión (SALTO, IGNORAR) |
| `FragmentarPDFUseCase` | Calcula páginas, construye la jerarquía y extrae los fragmentos |
| `GestionarSesionUseCase` | Guarda/carga configuraciones con adjuntos |

### DTOs (`dto.py`)

- `ResultadoCarga`, `ResultadoAnalisis`, `InfoArchivo`, `ResultadoFragmentacion`.

### Contenedor (`container.py`)

Instancia única que crea la infraestructura y conecta los casos de uso. Las
vistas reciben el `Container` y acceden a los casos de uso a través de él.

## Capa de infraestructura

- `excel_repository.py`: lee el inventario con `pandas`/`openpyxl`, convierte
  filas en `InventoryRecord` y detecta acervo, escribano y siglo.
- `pdf_service.py`: usa `PyMuPDF`/`pypdf` para renderizar y extraer páginas.
- `session_repository.py`: persiste configuraciones JSON.
- `hierarchy_builder.py`: construye la ruta de 11 niveles (ver
  [Reglas de negocio](reglas-negocio.md)).
- `mapeo_maestro.py`: carga `resources/mapa_maestro.json` y devuelve un
  `MapeoMaestro` (dataclasses `UbicacionMetadato`, `MapeoColumna`). Si el
  archivo falta o es inválido, cae a `mapeo_por_defecto()` usando las
  constantes del dominio (`COLUMN_ALIASES`, `FALLBACK_COLUMNS`,
  `SIGLO_FILA`, `ESCRIBANO_FILA`, `ACERVO_FILA` de `value_objects.py`).
  El JSON solo **sobreescribe** los valores por defecto.

### Mapa maestro (`resources/mapa_maestro.json`)

Configuración externa que indica dónde vive cada dato del inventario Excel:

- **`metadatos`**: celda (fila/columna 1-based) de los datos globales del
  encabezado — `siglo`, `escribano` y `acervo`. Se leen una sola vez.
- **`columnas`**: por campo, una lista de **aliases** (sinónimos del nombre de
  la columna, p. ej. `registro` ← `["n° de registro", "expediente", ...]`) y un
  `indice_fallback` opcional (columna fija usada si ningún alias coincide).

Flujo: `resources/mapa_maestro.json` → `cargar_mapeo_maestro()` → `MapeoMaestro`
→ se inyecta en `ExcelRepository` (por defecto desde `container.py`), que lo usa
en `extraer_metadatos()`, `_mapear_columnas()` y `_get_col()`.

## Capa de presentación

### ViewModel (`app_state.py`)

Estado global observable: rutas de archivos, registros, configuración de mapeo,
tema, logs, historial de incidencias validadas. Emite señales
(`records_changed`, `pdf_changed`, `theme_changed`, …) que las vistas escuchan.

### Vistas

| Vista | Módulo |
|---|---|
| `WorkspaceView` | Carga de archivos, parámetros de mapeo, previsualización |
| `AnalyzerView` | Paneles de resumen, pestañas por analizador, corrección/validación |
| `ProcessView` | Fragmentación del PDF y resumen del resultado |
| `PDFEditorView` | Thumbnails con exclusión/reordenamiento |
| `DocsView` | Consulta de esta documentación |
| `SupportView` | Información de la app, atajos y diagnóstico (solo texto) |

### Flujo de datos

```
View → ViewModel (señal) → Use Case → Domain Service → Infraestructura
      ← resultado (DTO) ← Use Case ← ...
View ← ViewModel (señal con datos)
```

## Testing

Suites en `tests/` separadas por capa:

- `tests/domain/` — analizadores, mapeo de folios, parser.
- `tests/application/` — casos de uso (análisis, exclusiones, fragmentación).
- `tests/infrastructure/` — repositorios, servicio PDF, jerarquía.
- `tests/presentation/` — viewmodels y construcción de filas de la UI.

```bash
pytest tests/ -v
```

## Dependencias

| Librería | Uso |
|---|---|
| PySide6 | Interfaz gráfica |
| pandas / openpyxl | Lectura del inventario Excel |
| pypdf / PyMuPDF | Extracción y render de páginas PDF |
| Pillow | Procesamiento de imágenes |
| pytest | Testing |
