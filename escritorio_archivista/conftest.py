"""
Configuración de pytest — agrega el directorio raíz al sys.path.
"""
import sys
import os

# Agregar el directorio raíz del proyecto al sys.path
sys.path.insert(0, os.path.dirname(__file__))
