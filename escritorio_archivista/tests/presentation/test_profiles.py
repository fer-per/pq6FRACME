"""Tests de utilidades para los perfiles de configuración."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.presentation import main_window
from src.presentation.constants import SESIONES_DIR


class TestRutaPerfil:
    def test_construye_ruta_en_sesiones(self):
        assert main_window._ruta_perfil("mi config") == os.path.join(
            SESIONES_DIR, "mi config.json"
        )


class TestNombreValido:
    def test_nombres_correctos(self):
        assert main_window._nombre_valido("proto16")
        assert main_window._nombre_valido("config con espacios")
        assert main_window._nombre_valido("acervo-7-1891")

    def test_nombres_invalidos(self):
        assert not main_window._nombre_valido("")
        assert not main_window._nombre_valido("   ")
        assert not main_window._nombre_valido("a/b")
        assert not main_window._nombre_valido("a\\b")
        assert not main_window._nombre_valido("a:b")
        assert not main_window._nombre_valido('a"b')
        assert not main_window._nombre_valido("a*b")
        assert not main_window._nombre_valido("a<b")


class TestListarPerfiles:
    def test_sin_carpeta_devuelve_vacio(self, tmp_path, monkeypatch):
        ruta = os.path.join(tmp_path, "no_existe")
        monkeypatch.setattr(main_window, "SESIONES_DIR", ruta)
        assert main_window._listar_perfiles() == []

    def test_lista_solo_jsons_ordenados(self, tmp_path, monkeypatch):
        monkeypatch.setattr(main_window, "SESIONES_DIR", str(tmp_path))
        (tmp_path / "b.json").write_text("{}", encoding="utf-8")
        (tmp_path / "a.json").write_text("{}", encoding="utf-8")
        (tmp_path / "nota.txt").write_text("hola", encoding="utf-8")

        assert main_window._listar_perfiles() == ["a", "b"]
