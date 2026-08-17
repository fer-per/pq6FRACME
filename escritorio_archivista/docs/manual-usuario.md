# Manual de usuario

Esta guía explica el flujo completo de trabajo con el Escritorio Archivista:
desde la carga del inventario hasta la generación de los fragmentos PDF.

---

## Flujo de trabajo general

```
1. Cargar inventario (Excel) y PDF original
2. Configurar el mapeo de páginas
3. Ejecutar el análisis de calidad
4. Corregir o validar incidencias
5. (Opcional) Excluir/reordenar hojas en el Editor PDF
6. Fragmentar el PDF en documentos individuales
```

---

## 1. Espacio de Trabajo

### Paso 1 — Carga de Archivos

- **INVENTARIO EXCEL**: arrastrá y soltá (o hacé clic) el archivo `.xlsx` con el
  inventario notarial. Se detectan automáticamente los metadatos: acervo,
  escribano y siglo.
- **PDF ORIGINAL**: arrastrá y soltá el PDF maestro digitalizado.

### Paso 2 — Parámetros de Mapeo

| Parámetro | Descripción |
|---|---|
| Fila inicio de datos | Primera fila del Excel que contiene datos (por encima van títulos/encabezados) |
| Inicia desde fila | Primera fila a procesar |
| Termina en fila | Última fila a procesar (0 = hasta el final) |
| Pág. PDF Inicio | Número de página física del PDF donde comienza el primer folio |

Al modificar los valores hacé clic en **Guardar Cambios**.

### Paso 3 — Previsualización del Inventario

- Se muestra la tabla completa con fila, registro, escribano, protocolo, folios,
  página PDF asignada, fechas, título, interesados y estado.
- Usá la **barra de búsqueda** para filtrar.
- **Clic en una fila** → navega a la página PDF correspondiente en la vista previa.

---

## 2. Analizador de Inventario

### Ejecutar el análisis

Hacé clic en **Ejecutar Análisis**. Se ejecutan los 7 analizadores:

- Folios
- Data Tópica
- Data Crónica
- Cobertura PDF
- Número de Registro
- Escribano
- Protocolo

El **encabezado** muestra el estado general con un indicador de color:

- **Fondo verde**: sin incidencias.
- **Fondo rojo**: hay una o más incidencias (con el detalle de fatales y advertencias).

### Pestañas de resultados

Cada pestaña muestra la lista de registros con las celdas en rojo donde se
detectó un error:

- **Todas las Incidencias**: vista combinada de todos los analizadores.
- **Folios / Data Tópica / Data Crónica / Cobertura PDF / N° Registro /
  Escribano / Protocolo**: detalle por analizador.

- Usá **Solo Líneas con Error** para ocultar los registros sin incidencias.
- **Clic en una fila** → navega a la página PDF del registro.

### Corregir y validar

- **Corregir Seleccionado**: abre el modal de corrección para editar el campo
  del analizador y/o la paginación PDF. Cada pestaña mantiene su propio
  historial de **Deshacer / Rehacer**.
- **Validar como Correcto**: marca la incidencia como validada para que deje de
  mostrarse como error y el registro pase a fragmentarse.

### Estados de los registros

| Estado | Significado |
|---|---|
| *(vacío)* | Sin incidencias |
| REVISAR | Tiene errores fatales o incidencias sin validar |
| VALIDADO | La incidencia fue validada manualmente como correcta |
| FRAGMENTADO | El documento fue generado en la fragmentación |

---

## 3. Editor PDF

Permite ajustar el contenido físico del PDF antes de fragmentar:

- **Excluir**: elimina hojas del proceso (portadas, hojas en blanco, separadores).
- **Mover arriba / abajo**: reordena el orden de las hojas.
- **Deshacer / Rehacer**: revierte cambios del editor.
- Al excluir o reordenar, la columna **Pág. PDF** del inventario se renumerada
  automáticamente (posiciones 1, 2, 3…), manteniendo la coherencia con el editor
  y la vista previa.

---

## 4. Fragmentar PDF

1. Seleccioná el **directorio de salida**.
2. Hacé clic en **FRAGMENTAR PDF**.
3. Al terminar se muestra el **resumen del resultado**: fragmentos creados,
   errores y registros pendientes.

Los documentos se organizan automáticamente en una **jerarquía de 11 niveles**
(ver [Reglas de negocio](reglas-negocio.md)).

### Registros pendientes

Si existen registros en estado REVISAR sin validar, registros sin foliación
(S/F) sin rango manual o folios que no resuelven a páginas, se generan en la
carpeta `logs/pendientes.csv` con el motivo.

---

## 5. Configuraciones y sesiones

- **Guardar** (o `Ctrl+S`): guarda la configuración actual con un nombre.
  Incluye los adjuntos (copias del Excel y del PDF cargados).
- **Cargar** (o `Ctrl+L`): restaura una configuración guardada.
- **Nueva** (o `Ctrl+N`): reinicia el estado para empezar de cero.
- Al cerrar la aplicación, se avisa si quedan cambios sin guardar.

---

## 6. Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl+S` | Guardar configuración |
| `Ctrl+L` | Cargar configuración |
| `Ctrl+N` | Nueva configuración |
| `Ctrl+1` | Espacio de Trabajo |
| `Ctrl+2` | Analizador |
| `Ctrl+3` | Fragmentar |

---

## 7. Temas y vista previa

- El botón del encabezado alterna entre **tema claro y oscuro**.
- El botón de **vista partida** muestra/oculta la vista previa del PDF en el
  lateral derecho.
