"""Tests para utilidades del ViewModel de Procesamiento."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.presentation.viewmodels.process_vm import (
    resolver_directorio_salida,
    resolver_directorio_corrida,
)
from src.presentation.constants import DEFAULT_OUTPUT_DIR


class TestResolverDirectorioSalida:
    def test_retorna_base_si_no_existe(self, tmp_path):
        base = os.path.join(tmp_path, "output")
        assert resolver_directorio_salida(base) == base

    def test_numera_corridas_sucesivas(self, tmp_path):
        base = os.path.join(tmp_path, "output")
        os.makedirs(base)

        assert resolver_directorio_salida(base) == f"{base} (1)"
        os.makedirs(f"{base} (1)")

        assert resolver_directorio_salida(base) == f"{base} (2)"
        os.makedirs(f"{base} (2)")

        assert resolver_directorio_salida(base) == f"{base} (3)"

    def test_salta_numeros_ya_ocupados(self, tmp_path):
        base = os.path.join(tmp_path, "output")
        os.makedirs(base)
        os.makedirs(f"{base} (1)")
        os.makedirs(f"{base} (3)")

        assert resolver_directorio_salida(base) == f"{base} (2)"

    def test_ruta_relativa_tambien_funciona(self, tmp_path):
        base = os.path.join(tmp_path, "salida")
        assert resolver_directorio_salida(base) == base
        os.makedirs(base)
        assert resolver_directorio_salida(base) == f"{base} (1)"


class TestResolverDirectorioCorrida:
    def test_carpeta_usuario_no_se_numera(self, tmp_path):
        base = os.path.join(tmp_path, "elegida")
        os.makedirs(base)
        assert resolver_directorio_corrida(base) == base

    def test_carpeta_usuario_no_se_numera_si_ya_existe(self, tmp_path):
        base = os.path.join(tmp_path, "elegida")
        os.makedirs(base)
        os.makedirs(f"{base} (1)")
        assert resolver_directorio_corrida(base) == base

    def test_default_sin_existir_no_se_numera(self, tmp_path):
        base = os.path.join(tmp_path, "output")
        assert resolver_directorio_corrida(base, default_dir=base) == base

    def test_default_se_numera_si_ya_existe(self, tmp_path):
        base = os.path.join(tmp_path, "output")
        os.makedirs(base)
        os.makedirs(f"{base} (1)")
        assert resolver_directorio_corrida(base, default_dir=base) == f"{base} (2)"

    def test_default_numeracion_escala_con_corridas(self, tmp_path):
        base = os.path.join(tmp_path, "output")
        assert resolver_directorio_corrida(base, default_dir=base) == base
        os.makedirs(base)
        assert resolver_directorio_corrida(base, default_dir=base) == f"{base} (1)"
        os.makedirs(f"{base} (1)")
        assert resolver_directorio_corrida(base, default_dir=base) == f"{base} (2)"
