import datetime
import logging
import gi  # type: ignore
gi.require_version('Gtk', '4.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
gi.require_version("Adw", "1")
from gi.repository import Gtk  # noqa: E402
from gi.repository import GLib  # noqa: E402
from gi.repository import Adw  # noqa: E402


logger = logging.getLogger(__name__)


def get_current_date():
    return datetime.datetime.now()


class AddWeightDialog(Adw.Dialog):
    def __init__(self, parent, on_save) -> None:
        super().__init__()
        self.set_title("Agregar nuevo peso")
        self.on_save = on_save
        self.selected_date = datetime.date.today()

        vbox = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=15,
            margin_top=15, margin_bottom=15,
            margin_start=15, margin_end=15
        )
        self.set_child(vbox)

        self.date_label = Gtk.Label(xalign=0)
        self.update_date_label()
        vbox.append(self.date_label)

        calendar_button = Gtk.Button(label="Seleccionar fecha")
        calendar_button.add_css_class("suggested-action")
        calendar_button.connect("clicked", self.show_calendar_popup)
        vbox.append(calendar_button)

        weight_box = Gtk.Box(spacing=10)
        weight_label = Gtk.Label(label="Peso:")
        self.weight_entry = Gtk.Entry()
        self.weight_entry.set_placeholder_text("75.3")
        self.weight_entry.set_input_purpose(Gtk.InputPurpose.NUMBER)
        weight_box.append(weight_label)
        weight_box.append(self.weight_entry)
        unit = Gtk.Label(label="kg")
        weight_box.append(unit)
        vbox.append(weight_box)

        action_box = Gtk.Box(spacing=10, halign=Gtk.Align.END)
        cancel_btn = Gtk.Button(label="Cancelar")
        cancel_btn.connect("clicked", lambda b: self.close())

        confirm_btn = Gtk.Button(label="Guardar")
        confirm_btn.add_css_class("suggested-action")
        confirm_btn.connect("clicked", self.on_save_clicked)

        action_box.append(cancel_btn)
        action_box.append(confirm_btn)
        vbox.append(action_box)

    def update_date_label(self):
        formatted = self.selected_date.strftime("%d/%m/%Y")
        self.date_label.set_markup(f"<b>Fecha:</b> {formatted}")

    def show_calendar_popup(self, button, glib=None):
        popover = Gtk.Popover()
        popover.set_parent(button)

        calendar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        popover.set_child(calendar_box)

        calendar = Gtk.Calendar()

        year = self.selected_date.year
        month = self.selected_date.month - 1
        day = self.selected_date.day
        calendar.select_day(GLib.DateTime.new_local(year, month, day, 0, 0, 0))

        calendar_box.append(calendar)

        today_btn = Gtk.Button(label="Hoy", margin_top=5)
        today_btn.connect(
            "clicked",
            lambda b: calendar.select_day(
                GLib.DateTime.new_local(
                    get_current_date().year,
                    get_current_date().month - 1,
                    get_current_date().day,
                    0, 0, 0
                )
            )
        )
        calendar_box.append(today_btn)

        calendar.connect("day-selected", self.on_day_selected, popover)

        popover.popup()

    def on_day_selected(self, calendar: Gtk.Calendar, popover):
        dt = calendar.get_date()
        year = dt.get_year()
        month = dt.get_month() + 1
        day = dt.get_day_of_month() or 1
        try:
            self.selected_date = datetime.date(year, month, day)
            self.update_date_label()
        except ValueError as e:
            logger.exception(f"Error al seleccionar fecha {e}")
        popover.popdown()

    def on_save_clicked(self, button):
        weight_str = self.weight_entry.get_text().strip()
        try:
            weight = float(weight_str)
            if weight <= 0:
                raise ValueError("El peso debe ser positivo.")
            if self.on_save:
                self.on_save(self.selected_date, weight)
            self.close()
        except ValueError as e:
            msg = Adw.MessageDialog(
                transient_for=self,
                heading="Error",
                body=str(e)
            )
            msg.add_response("ok", "OK")
            msg.set_default_response("ok")
            msg.set_close_response("ok")
            msg.present()
