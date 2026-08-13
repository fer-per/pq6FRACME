"""
Ventana principal de la aplicación.

Compone sidebar, header, área de contenido (QStackedWidget)
y panel lateral de PDF preview como dock widget.
"""
import logging
import os
import re
import shutil

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QSplitter, QDockWidget, QMessageBox,
    QInputDialog, QDialogButtonBox, QComboBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut

from src.presentation.constants import (
    ViewId, SESIONES_DIR, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
)
from src.presentation.theme.colors import get_palette
from src.presentation.theme.stylesheet import generate_stylesheet
from src.presentation.viewmodels.app_state import AppStateVM
from src.presentation.widgets.sidebar import Sidebar
from src.presentation.widgets.header import Header
from src.presentation.widgets.pdf_preview import PDFPreview

from src.application.container import Container

logger = logging.getLogger(__name__)

_NOMBRE_INVALIDO = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _nombre_valido(nombre: str) -> bool:
    """True si el nombre de perfil es válido para un archivo Windows."""
    return bool(nombre.strip()) and not _NOMBRE_INVALIDO.search(nombre)


def _ruta_perfil(nombre: str) -> str:
    """Ruta completa de un perfil de configuración."""
    return os.path.join(SESIONES_DIR, f"{nombre}.json")


def _listar_perfiles() -> list:
    """Nombres de los perfiles de configuración guardados (orden alfabético)."""
    if not os.path.isdir(SESIONES_DIR):
        return []
    return sorted(
        f[:-5] for f in os.listdir(SESIONES_DIR) if f.endswith(".json")
    )


def _archivos_dir(nombre: str) -> str:
    """Directorio donde se guardan copias del Excel/PDF de un perfil."""
    return os.path.join(SESIONES_DIR, f"{nombre}_archivos")


def _empaquetar_adjuntos(nombre: str, estado: dict) -> dict:
    """Copia el Excel y PDF cargados junto al perfil.

    Devuelve un dict con ``excel_adjunto``/``pdf_adjunto`` (rutas relativas
    a ``SESIONES_DIR``) que se guardan en el JSON del perfil.
    """
    adjuntos = {}
    dir_adj = _archivos_dir(nombre)
    os.makedirs(dir_adj, exist_ok=True)
    for key, destino_nombre in (
        ("excel_path", "inventario_cargado.xlsx"),
        ("pdf_path", "pdf_cargado.pdf"),
    ):
        origen = estado.get(key)
        if not origen or not os.path.isfile(origen):
            continue
        destino = os.path.join(dir_adj, destino_nombre)
        try:
            shutil.copy2(origen, destino)
            adjuntos[key.replace("_path", "_adjunto")] = os.path.relpath(
                destino, SESIONES_DIR
            )
        except OSError as e:
            logger.warning("No se pudo copiar %s: %s", origen, e)
    return adjuntos


def _resolver_adjuntos(data: dict):
    """Prioriza los adjuntos guardados del perfil sobre las rutas originales."""
    for key, adj_key in (("excel_path", "excel_adjunto"), ("pdf_path", "pdf_adjunto")):
        adj = data.get(adj_key)
        if not adj:
            continue
        if not os.path.isabs(adj):
            adj = os.path.normpath(os.path.join(SESIONES_DIR, adj))
        if os.path.isfile(adj):
            data[key] = adj


class MainWindow(QMainWindow):
    """
    Ventana principal del Escritorio Archivista.

    Layout:
    ┌──────────────────────────────────────────────────┐
    │  HEADER                                          │
    ├──────┬───────────────────────┬───────────────────┤
    │      │                       │                   │
    │  S   │    CONTENT            │   PDF PREVIEW     │
    │  I   │    (QStackedWidget)   │   (DockWidget)    │
    │  D   │                       │                   │
    │  E   │                       │                   │
    │  B   │                       │                   │
    │  A   │                       │                   │
    │  R   │                       │                   │
    └──────┴───────────────────────┴───────────────────┘
    """

    def __init__(self, container: Container, state: AppStateVM):
        super().__init__()
        self._container = container
        self._state = state
        self._views = {}

        self.setWindowTitle("Escritorio Archivista — SGFD v2.0")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self.resize(1400, 850)

        self._preview_pdf_path = None

        self._setup_ui()
        self._setup_shortcuts()
        self._connect_signals()

        # Aplicar tema
        self.setStyleSheet(generate_stylesheet(self._state.dark_mode))

        logger.info("MainWindow inicializada.")

    def _setup_ui(self):
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self._header = Header()
        main_layout.addWidget(self._header)

        # Cuerpo: sidebar + contenido
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        body_layout.addWidget(self._sidebar)

        # Contenido principal (QStackedWidget)
        self._stack = QStackedWidget()
        body_layout.addWidget(self._stack, stretch=1)

        main_layout.addWidget(body, stretch=1)

        # PDF Preview como DockWidget
        self._pdf_dock = QDockWidget("Vista Previa PDF", self)
        self._pdf_dock.setAllowedAreas(
            Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea
        )
        self._pdf_preview = PDFPreview()
        self._pdf_preview.set_renderer(self._render_pdf_page)
        self._pdf_dock.setWidget(self._pdf_preview)
        self._pdf_dock.setMinimumWidth(320)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self._pdf_dock)

        # Crear vistas placeholder (se reemplazan al registrar vistas reales)
        self._create_placeholder_views()

    def _create_placeholder_views(self):
        """Crea placeholders para las vistas que aún no están registradas."""
        from PySide6.QtWidgets import QLabel
        from src.presentation.theme.fonts import get_font

        placeholder_names = [
            ("📁 Workspace", ViewId.WORKSPACE),
            ("📊 Analizador", ViewId.ANALYZER),
            ("✂️ Fragmentar", ViewId.PROCESS),
            ("📄 Editor PDF", ViewId.PDF_EDITOR),
            ("📖 Documentación", ViewId.DOCS),
            ("🛟 Soporte", ViewId.SUPPORT),
        ]
        for name, view_id in placeholder_names:
            placeholder = QLabel(f"{name}\n\nVista en construcción...")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setFont(get_font("title_md"))
            idx = self._stack.addWidget(placeholder)
            self._views[view_id] = idx

    def register_view(self, view_id: int, widget: QWidget):
        """Registra una vista real reemplazando el placeholder."""
        if view_id in self._views:
            old_idx = self._views[view_id]
            old_widget = self._stack.widget(old_idx)
            self._stack.removeWidget(old_widget)
            old_widget.deleteLater()

        idx = self._stack.insertWidget(view_id, widget)
        self._views[view_id] = idx

    def navigate_to(self, view_id: int):
        """Navega a una vista por su ID."""
        if view_id in self._views:
            self._stack.setCurrentIndex(self._views[view_id])
            self._sidebar.set_active_view(view_id)
            logger.info("Navegación a vista: %d", view_id)

    def _setup_shortcuts(self):
        """Configura atajos de teclado."""
        QShortcut(QKeySequence("Ctrl+S"), self, self._on_save)
        QShortcut(QKeySequence("Ctrl+L"), self, self._on_load)
        QShortcut(QKeySequence("Ctrl+N"), self, self._on_new)
        QShortcut(QKeySequence("Ctrl+1"), self, lambda: self.navigate_to(ViewId.WORKSPACE))
        QShortcut(QKeySequence("Ctrl+2"), self, lambda: self.navigate_to(ViewId.ANALYZER))
        QShortcut(QKeySequence("Ctrl+3"), self, lambda: self.navigate_to(ViewId.PROCESS))

    def _connect_signals(self):
        """Conecta señales entre componentes."""
        self._sidebar.navigation_requested.connect(self.navigate_to)
        self._header.dual_view_toggled.connect(self._on_dual_view_toggled)
        self._header.theme_toggled.connect(self._on_theme_toggled)
        self._header.save_requested.connect(self._on_save)
        self._header.load_requested.connect(self._on_load)
        self._header.new_requested.connect(self._on_new)

        # PDF preview signals
        self._pdf_preview.page_changed.connect(self._on_page_changed)
        self._pdf_preview.zoom_changed.connect(self._on_zoom_changed)

        # State signals
        self._state.logs_changed.connect(self._on_logs_changed)
        self._state.pdf_changed.connect(self._on_pdf_state_changed)
        self._state.theme_changed.connect(self._on_theme_changed)

    def _on_dual_view_toggled(self, visible: bool):
        """Muestra/oculta la vista previa del PDF."""
        self._pdf_dock.setVisible(visible)
        self._state.dual_view_active = visible

    def _on_theme_toggled(self, dark: bool):
        """Cambia el tema de la aplicación."""
        self._state.dark_mode = dark
        self.setStyleSheet(generate_stylesheet(dark))
        self._state.add_log("INFO", f"Tema cambiado a {'oscuro' if dark else 'claro'}.")

    def _on_theme_changed(self, dark: bool):
        """Propaga el cambio de tema a vistas y widgets con estilos inline."""
        self._apply_theme(self._sidebar, dark)
        self._apply_theme(self._header, dark)
        self._apply_theme(self._pdf_preview, dark)
        for idx in self._views.values():
            self._apply_theme(self._stack.widget(idx), dark)

    @staticmethod
    def _apply_theme(widget: QWidget, dark: bool):
        """Invoca ``apply_theme`` en un widget si lo implementa."""
        apply = getattr(widget, 'apply_theme', None)
        if apply is not None:
            apply(dark)

    def _on_save(self):
        """Guarda la configuración actual con un nombre de perfil."""
        dlg = QInputDialog(self)
        dlg.setWindowTitle("Guardar configuración")
        dlg.setLabelText("Nombre de la configuración:")
        dlg.setTextValue(self._state.profile_name or "")
        dlg.setOkButtonText("Guardar")
        dlg.setCancelButtonText("Cancelar")
        self._style_input_dialog_buttons(dlg)
        ok = dlg.exec()
        nombre = dlg.textValue()
        if not ok:
            return
        nombre = nombre.strip()
        if not _nombre_valido(nombre):
            self._state.add_log(
                "ERR", "Nombre de configuración inválido."
            )
            QMessageBox.warning(
                self, "Nombre inválido",
                "El nombre no puede estar vacío ni contener caracteres "
                "inválidos: \\ / : * ? \" < > |",
            )
            return

        ruta = _ruta_perfil(nombre)
        if os.path.exists(ruta):
            sobrescribir = QMessageBox(self)
            sobrescribir.setWindowTitle("Sobrescribir")
            sobrescribir.setIcon(QMessageBox.Icon.Question)
            sobrescribir.setText(
                f"Ya existe la configuración '{nombre}'. ¿Deseás "
                "sobrescribirla?"
            )
            si_btn = sobrescribir.addButton(
                "Sí", QMessageBox.ButtonRole.YesRole
            )
            no_btn = sobrescribir.addButton(
                "No", QMessageBox.ButtonRole.NoRole
            )
            sobrescribir.setDefaultButton(no_btn)
            self._style_messagebox_buttons(sobrescribir)
            sobrescribir.exec()
            if sobrescribir.clickedButton() is not si_btn:
                return

        try:
            datos = self._state.to_dict()
            # Guardar también el Excel y PDF cargados, con los parámetros
            # de mapeo que ya van en `to_dict`.
            datos.update(_empaquetar_adjuntos(nombre, datos))
            self._container.gestionar_sesion.guardar(ruta, datos)
            self._state.profile_name = nombre
            self._header.set_profile_name(nombre)
            self._state.mark_saved()
            self._state.add_log(
                "SUCCESS", f"Configuración '{nombre}' guardada exitosamente."
            )
            QMessageBox.information(
                self, "Configuración guardada",
                f"La configuración '{nombre}' se guardó exitosamente.",
            )
        except Exception as e:
            self._state.add_log("ERR", f"Error al guardar sesión: {e}")
            QMessageBox.critical(
                self, "Error",
                f"No se pudo guardar la configuración:\n{e}",
            )

    def _on_load(self):
        """Carga una configuración guardada y la aplica al estado."""
        perfiles = _listar_perfiles()
        if not perfiles:
            QMessageBox.warning(
                self, "Sin configuraciones",
                "No hay configuraciones guardadas. Usá Guardar primero.",
            )
            return

        actual = self._state.profile_name or perfiles[0]
        dlg = QInputDialog(self)
        dlg.setWindowTitle("Cargar configuración")
        dlg.setLabelText("Configuración a cargar:")
        dlg.setComboBoxItems(perfiles)
        dlg.setComboBoxEditable(False)
        combo = dlg.findChild(QComboBox)
        if combo is not None:
            combo.setCurrentIndex(
                perfiles.index(actual) if actual in perfiles else 0
            )
        dlg.setOkButtonText("Cargar")
        dlg.setCancelButtonText("Cancelar")
        self._style_input_dialog_buttons(dlg)
        ok = dlg.exec()
        nombre = dlg.textValue()
        if not ok:
            return

        ruta = _ruta_perfil(nombre)
        try:
            data = self._container.gestionar_sesion.cargar(ruta)
            if not data:
                self._state.add_log(
                    "WARN", f"La configuración '{nombre}' está vacía."
                )
                QMessageBox.warning(
                    self, "Sin configuración",
                    f"La configuración '{nombre}' está vacía.",
                )
                return
            # Resolver adjuntos del perfil (copias del Excel/PDF)
            _resolver_adjuntos(data)
            self._state.from_dict(data)
            self._state.profile_name = nombre
            self._header.set_profile_name(nombre)
            self._state.add_log(
                "SUCCESS", f"Configuración '{nombre}' cargada exitosamente."
            )
            # Recargar el Excel y PDF con los parámetros de mapeo guardados
            self._reload_archivos()
            QMessageBox.information(
                self, "Configuración cargada",
                f"La configuración '{nombre}' se cargó correctamente.",
            )
        except Exception as e:
            self._state.add_log("ERR", f"Error al cargar configuración: {e}")
            QMessageBox.critical(
                self, "Error",
                f"No se pudo cargar la configuración:\n{e}",
            )

    def _on_new(self):
        """Reinicia el estado para empezar una configuración nueva."""
        conf = QMessageBox(self)
        conf.setWindowTitle("Nueva configuración")
        conf.setIcon(QMessageBox.Icon.Question)
        conf.setText(
            "¿Empezar una configuración nueva?\n"
            "Se descartará el estado actual. Las configuraciones guardadas "
            "no se borran."
        )
        si_btn = conf.addButton("Sí", QMessageBox.ButtonRole.YesRole)
        no_btn = conf.addButton("No", QMessageBox.ButtonRole.NoRole)
        conf.setDefaultButton(no_btn)
        self._style_messagebox_buttons(conf)
        conf.exec()
        if conf.clickedButton() is not si_btn:
            return
        self._state.reset()
        self._header.set_profile_name("")
        self.navigate_to(ViewId.WORKSPACE)
        self._state.add_log(
            "INFO", "Nueva configuración iniciada."
        )
        QMessageBox.information(
            self, "Nueva configuración",
            "Estado reiniciado. Podés comenzar a cargar un nuevo inventario.\n"
            "Usá Guardar para crear otra configuración.",
        )

    def _style_messagebox_buttons(self, box: QMessageBox):
        """Colorea los botones de un QMessageBox según su funcionalidad.

        - Acción afirmativa/guardar   (Aceptar, Sí, Guardar)   → verde
        - Acción destructiva          (Salir sin guardar, No)  → rojo
        - Resto (Cancelar, Cerrar, etc.)                        → neutro

        Los colores se toman de la paleta del tema activo.
        """
        for btn in box.buttons():
            role = box.buttonRole(btn)
            if role in (
                QMessageBox.ButtonRole.AcceptRole,
                QMessageBox.ButtonRole.YesRole,
                QMessageBox.ButtonRole.ApplyRole,
            ):
                btn.setObjectName("btn_confirmar")
            elif role == QMessageBox.ButtonRole.DestructiveRole:
                btn.setObjectName("btn_destructivo")
            else:
                btn.setObjectName("btn_neutro")

        box.setStyleSheet(self._dialog_button_stylesheet())

    def _style_input_dialog_buttons(self, dialog: QInputDialog):
        """Colorea los botones de un QInputDialog (Guardar/Cargar/Cancelar)."""
        bbox = dialog.findChild(QDialogButtonBox)
        if bbox is None:
            return
        ok_btn = bbox.button(QDialogButtonBox.StandardButton.Ok)
        cancel_btn = bbox.button(QDialogButtonBox.StandardButton.Cancel)
        if ok_btn is not None:
            ok_btn.setObjectName("btn_confirmar")
        if cancel_btn is not None:
            cancel_btn.setObjectName("btn_neutro")
        dialog.setStyleSheet(self._dialog_button_stylesheet())

    def _dialog_button_stylesheet(self) -> str:
        """Hoja de estilo común para botones de diálogos según funcionalidad."""
        pal = get_palette(self._state.dark_mode)
        return f"""
            QPushButton#btn_confirmar {{
                background-color: {pal['validate_bg']};
                color: {pal['validate_fg']};
                border: none; border-radius: 6px;
                padding: 6px 14px; font-weight: 600;
            }}
            QPushButton#btn_confirmar:hover {{
                background-color: {pal['validate_hover']};
            }}
            QPushButton#btn_confirmar:pressed {{
                background-color: {pal['validate_pressed']};
            }}
            QPushButton#btn_destructivo {{
                background-color: {pal['error']};
                color: #ffffff;
                border: none; border-radius: 6px;
                padding: 6px 14px; font-weight: 600;
            }}
            QPushButton#btn_destructivo:hover {{
                background-color: {pal['error']};
            }}
            QPushButton#btn_neutro {{
                background-color: {pal['surface_container']};
                color: {pal['text_primary']};
                border: none; border-radius: 6px;
                padding: 6px 14px;
            }}
            QPushButton#btn_neutro:hover {{
                background-color: {pal['surface_high']};
            }}
        """

    def closeEvent(self, event):
        """Al cerrar, avisa si la última configuración no está guardada."""
        if not self._state.has_unsaved_changes():
            event.accept()
            return

        respuesta = QMessageBox(self)
        respuesta.setWindowTitle("Cambios sin guardar")
        respuesta.setIcon(QMessageBox.Icon.Warning)
        respuesta.setText(
            "No guardaste la última configuración.\n\n"
            "Si cerrás la aplicación se perderá la configuración actual."
        )
        guardar_btn = respuesta.addButton(
            "Guardar y salir", QMessageBox.ButtonRole.AcceptRole
        )
        salir_btn = respuesta.addButton(
            "Salir sin guardar", QMessageBox.ButtonRole.DestructiveRole
        )
        cancelar_btn = respuesta.addButton(
            "Cancelar", QMessageBox.ButtonRole.RejectRole
        )
        respuesta.setDefaultButton(guardar_btn)
        respuesta.setEscapeButton(cancelar_btn)
        self._style_messagebox_buttons(respuesta)
        respuesta.exec()

        clicked = respuesta.clickedButton()
        role = respuesta.buttonRole(clicked)
        if role == QMessageBox.ButtonRole.AcceptRole:
            self._on_save()
            if self._state.has_unsaved_changes():
                event.ignore()
            else:
                event.accept()
        elif role == QMessageBox.ButtonRole.DestructiveRole:
            event.accept()
        else:
            event.ignore()

    def _on_page_changed(self, page: int):
        """Actualiza la página del PDF en el estado (el preview maneja el render)."""
        self._syncing_from_preview = True
        try:
            self._state.pdf_current_page = page
        finally:
            self._syncing_from_preview = False

    def _on_zoom_changed(self, zoom: int):
        """Actualiza el zoom del PDF (el preview maneja el render)."""
        self._state.pdf_zoom = zoom

    def _on_logs_changed(self):
        """Los logs se manejan en Python logging, no en UI."""
        pass

    def _on_pdf_state_changed(self):
        """Actualiza la vista previa cuando cambia el estado del PDF."""
        if self._state.pdf_path != self._preview_pdf_path:
            self._preview_pdf_path = self._state.pdf_path
            self._pdf_preview.reset_document()
        self._pdf_preview.set_total_pages(self._state.pdf_total_pages)
        if not getattr(self, '_syncing_from_preview', False):
            self._pdf_preview.set_current_page(self._state.pdf_current_page)

    def _render_pdf_page(self, page: int, zoom: int):
        """Renderer para el preview continuo: devuelve PNG o None."""
        if not self._state.pdf_path:
            return None
        try:
            return self._container.pdf_service.renderizar_pagina(
                self._state.pdf_path, page, zoom,
            )
        except Exception as e:
            logger.error("Error renderizando PDF: %s", e)
            return None

    def _render_current_page(self):
        """Compat: desplaza la vista previa a la página actual del estado."""
        self._pdf_preview.set_current_page(self._state.pdf_current_page)

    def _reload_archivos(self):
        """Refleja la configuración cargada en el workspace.

        Actualiza los archivos mostrados (Paso 1), los parámetros de mapeo
        (Paso 2) y recarga el Excel/PDF con los valores guardados.
        """
        idx = self._views.get(ViewId.WORKSPACE)
        widget = self._stack.widget(idx) if idx is not None else None
        if widget is None:
            return
        refresh = getattr(widget, "refresh_from_state", None)
        if refresh is None:
            return
        try:
            refresh()
        except Exception as e:
            self._state.add_log("ERR", f"No se pudieron recargar los archivos: {e}")

    @property
    def pdf_preview(self) -> PDFPreview:
        return self._pdf_preview

    @property
    def state(self) -> AppStateVM:
        return self._state

    @property
    def container(self) -> Container:
        return self._container
