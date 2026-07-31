# Sistema de Gestión y Fragmentación Documental (SGFD)

Aplicación profesional de escritorio para la gestión, análisis, validación y fragmentación de documentos notariales históricos.

## Requisitos

- Python 3.13+
- Dependencias: ver `requirements.txt`

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python main.py
```

## Arquitectura

Clean Architecture + MVVM

```
Presentación (PySide6) → Aplicación (Use Cases) → Dominio (Entidades, Servicios) ← Infraestructura
```

## Testing

```bash
pytest tests/ -v
```
