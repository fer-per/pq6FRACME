# Reglas de negocio del dominio

Reglas archivísticas implementadas en el Escritorio Archivista: jerarquía de
carpetas, mapeo de folios a páginas PDF y criterios de los analizadores.

---

## 1. Jerarquía de fragmentación (11 niveles)

Los fragmentos se organizan en una jerarquía de **11 niveles de carpetas**.
Los niveles 1 a 9 se escriben **en mayúsculas**; los niveles 10 y 11
(interesados) conservan la grafía original de la columna.

```
1.  ACERVO DOCUMENTAL NUMERO {acervo_num}     ← metadato (fila del Excel)
2.  SIGLO {siglo_romano}                       ← metadato romano
3.  FONDO DOCUMENTAL                           ← constante
4.  {escribano}                                ← metadato (fila del Excel)
5.  {año}                                      ← de la fecha de inicio
6.  PROTOCOLO {protocolo}                      ← del registro
7.  REGISTRO {registro}                        ← número real del catálogo
8.  {titulo}                                   ← valor literal de la columna
9.  {mes}                                      ← de la fecha de inicio
10. {interesado1}                              ← 1er interesado
11. {interesado2}.pdf                          ← nombre del archivo
```

### Detalles

- **Siglo**: se muestra el siglo romano (ej. `SIGLO XIX`). Si no hay metadato,
  se deriva del año y se convierte a romano.
- **Registro**: usa el N° de registro del catálogo, no el ID interno.
- **Mes**: nombres de `MONTH_NAMES` con numeración (ej. `3. MARZO`).
- **Interesados**: el nombre de carpeta y archivo solo considera el texto
  anterior al primer separador — **coma, guion o paréntesis** — sin incluirlo
  (ej. `Luis de Rueda, Juan de Mendoza` → `Luis de Rueda`).
- **Respaldo por nivel**: cuando falta el dato se usa `SIN {NIVEL}`.
  Si no hay interesados, `DATOS DE LOS INTERESADOS ILEGIBLES`.

### Colisiones de archivo

Si dos PDFs comparten nombre en la misma carpeta, se numeran sucesivamente:
`{nombre}.pdf`, `{nombre}_2.pdf`, `{nombre}_3.pdf`, …

---

## 2. Mapeo folio → página PDF

Cada registro del inventario mapea su rango de folios a páginas del PDF maestro.

### Folios notariales

- Formato `NNNr` (recto) / `NNNv` (verso), y rangos `NNNr-NNNv`.
- Conversión interna a entero: `1r=1`, `1v=2`, `2r=3`, `2v=4`, …
- Marcas de **sin foliación** (`S/F`, `sf`, `sin folio`, …) se reconocen como
  decisión intencional del inventario, no como error de formato.

### Modos de mapeo

| Modo | Cuándo se usa | Comportamiento |
|---|---|---|
| **Físico** | Sin editor activo | `pg_pdf` = página física con offset `pag_pdf_inicio` |
| **Posición renumerada** | Editor activo (`active_pages`) | `pg_pdf` = posiciones 1, 2, 3… tras excluir/reordenar hojas |

- **Rango manual** (`pg_pdf_manual`): anula el cálculo y usa el rango indicado.
  En modo posición se interpreta como posiciones de la grilla.
- **Compartir hoja** (`comparte_hoja`): el registro arranca en la misma hoja
  donde terminó el anterior.
- **Exclusiones**: saltos aprobados por reglas `SALTO` e hojas marcadas como
  `IGNORAR` no cuentan en la secuencia.

### Navegación

Al hacer clic en una fila, la vista previa navega a `first_page` del `pg_pdf`
(posición renumerada o página física, ambas coinciden sin editor).

---

## 3. Analizadores de calidad

Cada analizador devuelve un `AnalysisResult` con **errores** (fatales) y
**advertencias**. Los registros con errores fatales se marcan como `REVISAR`.

### 3.1 Folios

| Código | Tipo | Descripción |
|---|---|---|
| FORMATO | Error fatal | El folio no tiene formato válido (`NNNr-NNNv`) |
| REPETIDO | Advertencia | Folio de inicio ya usado en otro registro |
| SOLAPAMIENTO | Error fatal | Rango que se solapa con el anterior |
| SALTO | Advertencia | Salto no justificado por exclusiones; la descripción indica el folio esperado con r/v (ej. `se esperaba el folio 003r`) |
| SIN_FOLIO | Advertencia | Registro marcado como sin foliación (S/F) |

- La secuencia se **reinicia por protocolo**.
- Los registros que comparten hoja (`comparte_hoja`) no generan REPETIDO,
  SOLAPAMIENTO ni SALTO.

### 3.2 Data Tópica

Analiza la columna de tópica (lugares). Todas las detecciones son advertencias.

### 3.3 Data Crónica

| Condición | Tipo | Descripción |
|---|---|---|
| Mes fuera de rango 1-12 | Error fatal | Posible fecha en formato m/d/y ingresada como d/m/y |
| Año no extraíble | Advertencia | No se pudo obtener el año |
| Año fuera de [YEAR_MIN, YEAR_MAX] | Error fatal | Año fuera del rango histórico |
| Regresión de año | Error fatal | Año actual < año anterior |
| Regresión de mes (mismo año) | Advertencia | Mes anterior al del registro previo |

### 3.4 Cobertura PDF

Compara las páginas requeridas por el inventario con el total del PDF. Si el
PDF tiene menos páginas de las requeridas → error fatal global.

### 3.5 Número de Registro

| Condición | Tipo | Descripción |
|---|---|---|
| Vacío o `0` | Advertencia | Fila de índice, sub-encabezado u hora mal interpretada |
| Formato no numérico | Advertencia | Ej. `00:00:00` o palabras |
| Fuera de orden | Advertencia | Un número menor que el anterior dentro del mismo protocolo |

- Se admite **una sola letra final**: `11`, `11A`, `11B`, `5A` son válidos.
  Orden de comparación: `11 < 11A < 11B < 12`.
- **El mismo número puede repetirse** si la secuencia dentro del protocolo no
  desciende (no se advierte `11, 11, 12`; sí se advierte `11, 12, 11`).

### 3.6 Escribano

| Condición | Tipo |
|---|---|
| Vacío | Advertencia |
| Nombre < 3 caracteres | Advertencia |
| Nombre > 60 caracteres | Advertencia |

### 3.7 Protocolo

| Condición | Tipo | Descripción |
|---|---|---|
| Vacío | Advertencia | Sin número de protocolo |
| Formato no numérico | Advertencia | Ej. valores con letras |
| Regresión por escribano | Error fatal | Protocolo menor que el último del mismo escribano |

- Cada escribano tiene su propia secuencia de protocolos.

---

## 4. Estado de los registros

| Estado | Significado |
|---|---|
| *(vacío)* | Sin incidencias |
| REVISAR | Errores fatales sin corregir o incidencias sin validar |
| VALIDADO | Incidencia validada manualmente |
| FRAGMENTADO | Fragmento PDF generado |

En la fragmentación, los registros en estado `REVISAR` cuya incidencia no fue
validada se omiten y se listan en `logs/pendientes.csv`.
