import pathlib
from typing import Callable
import os
import logging
import gi  # type: ignore
gi.require_version('Gtk', '4.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
gi.require_version("Adw", "1")
from gi.repository import Gtk  # noqa: E402
from gi.repository import Gio  # noqa: E402
from gi.repository import GObject  # noqa: E402
from gi.repository import Adw  # noqa: E402


logger = logging.getLogger(__name__)


class SelectFileFormAttribute(Gtk.Box):
    def __init__(
            self,
            title: str,
            default_path: str = "",
            file_filter: Gtk.FileFilter = None,
            dialog_title: str = "Seleccionar archivo"
    ):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        self.dialog_title = dialog_title
        self.current_path = default_path

        label = Gtk.Label(label=title)
        label.set_halign(Gtk.Align.START)
        label.set_hexpand(False)
        self.append(label)

        self.path_entry = Gtk.Entry()
        self.path_entry.set_editable(False)
        self.path_entry.set_hexpand(True)
        self.path_entry.set_sensitive(False)
        if default_path and os.path.exists(default_path):
            self.path_entry.set_text(default_path)
        else:
            self.path_entry.set_placeholder_text("Ningún archivo seleccionado")
        self.append(self.path_entry)

        button = Gtk.Button()
        icon = Gtk.Image.new_from_icon_name("document-open-symbolic")
        button.set_child(icon)
        button.add_css_class("circular")
        button.set_tooltip_text("Seleccionar archivo")
        button.set_size_request(40, -1)
        button.connect("clicked", self.on_button_clicked)
        self.append(button)

        self.file_filter = file_filter or self.create_any_filter()

    def create_any_filter(self) -> Gtk.FileFilter:
        f = Gtk.FileFilter()
        f.set_name("Todos los archivos")
        f.add_pattern("*")
        return f

    def on_button_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            title=self.dialog_title,
            action=Gtk.FileChooserAction.OPEN
        )

        win = self.get_root()
        if isinstance(win, Gtk.Window):
            dialog.set_transient_for(win)

        dialog.add_button("_Cancelar", Gtk.ResponseType.CANCEL)
        dialog.add_button("_Abrir", Gtk.ResponseType.ACCEPT)

        dialog.set_filter(self.file_filter)

        if self.current_path and os.path.exists(self.current_path):
            try:
                gfile = Gio.File.new_for_path(os.path.dirname(self.current_path))
                dialog.set_file(gfile)
            except Exception:
                pass

        dialog.connect("response", self.on_dialog_response)
        dialog.present()

    def on_dialog_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.ACCEPT:
            selected_file = dialog.get_file()
            path = selected_file.get_path()
            if path:
                self.current_path = path
                self.path_entry.set_text(path)
                self.emit("file-changed", path)
        dialog.destroy()

    def get_file_path(self) -> str:
        return self.current_path

    def set_file_path(self, path: str):
        if os.path.exists(path) or path == "":
            self.current_path = path
            if path:
                self.path_entry.set_text(path)
            else:
                self.path_entry.set_text("")
        else:
            logger.error("Ruta no valida: %s", path)

    def clear(self):
        self.current_path = ""
        self.path_entry.set_text("")


GObject.signal_new(
    "file-changed",
    SelectFileFormAttribute,
    GObject.SignalFlags.RUN_FIRST,
    None,
    [str]
)



class ConfigurationDialog(Adw.Dialog):
    current_file: str | None = None

    def __init__(self, parent, on_save: Callable, file_path: pathlib.Path | None = None) -> None:
        super().__init__()
        self.on_save = on_save
        logger.info("file_path %s", file_path)
        if file_path:
            self.current_file = file_path.absolute().as_posix()

        self.set_title("Configuración")

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15, margin_top=15, margin_bottom=15, margin_start=15, margin_end=15)
        self.set_child(vbox)

        csv_filter = Gtk.FileFilter()
        csv_filter.set_name("Archivos CSV")
        csv_filter.add_mime_type("text/csv")
        csv_filter.add_pattern("*.csv")

        file_widget = SelectFileFormAttribute(
            title="Datos de peso:",
            default_path=file_path.as_posix() if file_path else "~",
            file_filter=csv_filter,
            dialog_title="Elegir archivo CSV"
        )
        file_widget.connect("file-changed", self.on_file_changed)
        vbox.append(file_widget)

        action_area = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        action_area.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", self.on_cancel_clicked)
        action_area.append(cancel_btn)

        confirm_btn = Gtk.Button(label="Guardar")
        confirm_btn.add_css_class("suggested-action")
        confirm_btn.connect("clicked", self.on_save_clicked)
        action_area.append(confirm_btn)

        vbox.append(action_area)

    def on_save_clicked(self, button):
        logger.info("File selected: %s", self.current_file)
        if self.on_save:
            self.on_save(file_path=self.current_file)
        self.close()

    def on_cancel_clicked(self, button):
        self.close()

    def on_file_changed(self, widget, path):
        self.current_file = str(path)
