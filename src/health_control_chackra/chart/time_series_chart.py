from typing import List, Callable, Tuple, Any, Optional
import datetime
import dataclasses
import logging
import gi  # type: ignore
gi.require_version('Gtk', '4.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk  # noqa: E402
from gi.repository import GObject  # noqa: E402
from gi.repository import Pango  # noqa: E402
from gi.repository import PangoCairo  # noqa: E402


COLOR_TYPE_RGB = Tuple[float, float, float]
COLOR_TYPE_ARGB = Tuple[float, float, float, float]
DATE_FORMAT = "%Y-%m-%d"

logger = logging.getLogger(__name__)


def scale(
        value: float,
        value_min: float,
        value_max: float,
        out_min: float,
        out_max: float
) -> float:
    if value_max == value_min:
        return (out_min + out_max) / 2
    return out_min + (value - value_min) / (value_max - value_min) * (out_max - out_min)


def detect_dark_mode() -> bool:
    settings = Gtk.Settings.get_default()
    if not settings:
        return False
    prefer_dark = settings.get_property("gtk-application-prefer-dark-theme")
    theme_name = settings.get_property("gtk-theme-name").lower()
    return prefer_dark or "dark" in theme_name


def map_date_to_x_coordinate(
        date: datetime.date,
        margin_left: int,
        plot_width: int,
        date_min: datetime.date,
        date_max: datetime.date
) -> float:
    days_total = (date_max - date_min).days or 1
    days_elapsed = (date - date_min).days
    return margin_left + (days_elapsed / days_total) * plot_width


def create_layout(cr: Any, text: str, size: int, bold=False) -> Pango.Layout:
    layout = PangoCairo.create_layout(cr)
    font_desc = Pango.FontDescription()
    font_desc.set_family("Sans")
    font_desc.set_size(size * Pango.SCALE)
    if bold:
        font_desc.set_weight(Pango.Weight.BOLD)
    layout.set_font_description(font_desc)
    layout.set_text(text, -1)
    return layout


def value_to_y(value: float, margin_top: float, plot_height: float, min_val: float, max_val: float) -> float:
    return margin_top + plot_height - ((value - (min_val - 1)) / ((max_val + 1) - (min_val - 1))) * plot_height


@dataclasses.dataclass
class TimeSeriesEntry:
    date: datetime.date
    value: float

    @classmethod
    def from_str(cls, date_str: str | datetime.date, value: float) -> Optional["TimeSeriesEntry"]:
        try:
            if isinstance(date_str, datetime.date):
                return cls(date=date_str, value=float(value))
            date = datetime.datetime.strptime(date_str, DATE_FORMAT).date()
            return cls(date=date, value=float(value))
        except Exception as e:
            logger.exception(f"Error parsing date {date_str}: {e}")
            return None


@dataclasses.dataclass
class ChartColors:
    bg: COLOR_TYPE_RGB
    grid: COLOR_TYPE_RGB
    axes: COLOR_TYPE_RGB
    text: COLOR_TYPE_RGB
    line: COLOR_TYPE_RGB
    tooltip_bg: COLOR_TYPE_ARGB
    tooltip_border: COLOR_TYPE_ARGB
    tooltip_text: COLOR_TYPE_RGB


class ChartStyle:
    @staticmethod
    def get_colors(is_dark: bool) -> ChartColors:
        if is_dark:
            return ChartColors(
                bg=(0.1, 0.1, 0.1),
                grid=(0.3, 0.3, 0.3),
                axes=(0.7, 0.7, 0.7),
                text=(0.9, 0.9, 0.9),
                line=(0.3, 0.6, 1.0),
                tooltip_bg=(0.2, 0.2, 0.2, 0.95),
                tooltip_border=(0.6, 0.6, 0.6, 1.0),
                tooltip_text=(1.0, 1.0, 1.0),
            )
        else:
            return ChartColors(
                bg=(1.0, 1.0, 1.0),
                grid=(0.9, 0.9, 0.9),
                axes=(0.4, 0.4, 0.4),
                text=(0.1, 0.1, 0.1),
                line=(0.2, 0.5, 0.8),
                tooltip_bg=(1.0, 1.0, 1.0, 0.95),
                tooltip_border=(0.8, 0.8, 0.8, 1.0),
                tooltip_text=(0.1, 0.1, 0.1),
            )


@dataclasses.dataclass
class ChartConfig:
    title: str = "Graph"
    x_label: str = "Date"
    y_label: str = "Value"
    y_format: str = "{:.1f}"
    line_color: Tuple[float, float, float] = (0.2, 0.5, 0.8)
    tooltip_formatter: Callable[[datetime.date, float], str] | None = None

    def __post_init__(self) -> None:
        if self.tooltip_formatter is None:
            self.tooltip_formatter = lambda d, v: f"{d.strftime(DATE_FORMAT)}\n{self.y_label}: {self.y_format.format(v)}"


class TimeSeriesChartWidget(Gtk.DrawingArea):
    entries: List[TimeSeriesEntry] = []
    hovered_point: int | None = None
    __gsignals__ = {
        "hover-changed": (GObject.SignalFlags.RUN_FIRST, None, (int,))
    }

    def __init__(
        self,
        data: List[Tuple[str, float]],
        config: ChartConfig
    ) -> None:
        super().__init__()
        self._set_chart_size()

        self._load_entries_from_data(data)

        self.config = config

        self._initialize_motion_controller()

        self.is_dark = detect_dark_mode()
        self._connect_with_system_theme()


    def _set_chart_size(self) -> None:
        self.set_size_request(800, 500)
        self.set_content_width(800)
        self.set_content_height(500)
        self.set_draw_func(self.on_draw)

    def _load_entries_from_data(self, data: List[Tuple[str, float]]) -> None:
        self.entries: List[TimeSeriesEntry] = []
        for date_str, value in data:
            entry = TimeSeriesEntry.from_str(date_str, value)
            if entry:
                self.entries.append(entry)
        self.entries.sort(key=lambda x: x.date)

    def _initialize_motion_controller(self) -> None:
        self.set_focusable(True)
        self.motion_controller = Gtk.EventControllerMotion()
        self.motion_controller.connect("motion", self.on_motion)
        self.motion_controller.connect("leave", self.on_leave)
        self.add_controller(self.motion_controller)

    def _connect_with_system_theme(self) -> None:
        settings = Gtk.Settings.get_default()
        if settings:
            settings.connect("notify::gtk-theme-name", self.on_theme_changed)
            settings.connect("notify::gtk-application-prefer-dark-theme", self.on_theme_changed)

    def on_theme_changed(self, _settings: Any, _pspec: Any) -> None:
        was_dark = self.is_dark
        self.is_dark = detect_dark_mode()
        if was_dark != self.is_dark:
            self.queue_draw()

    def on_motion(self, _controller: Any, x: float, y: float) -> None:
        width = self.get_width()
        height = self.get_height()
        if width <= 0 or height <= 0 or not self.entries:
            return

        margin_left, margin_top, margin_right, margin_bottom = 100, 80, 60, 80
        plot_width = width - margin_left - margin_right
        plot_height = height - margin_top - margin_bottom

        min_val = min(e.value for e in self.entries)
        max_val = max(e.value for e in self.entries)
        date_min = self.entries[0].date
        date_max = self.entries[-1].date

        threshold_sq = 15 ** 2
        hovered = None

        for i, entry in enumerate(self.entries):
            px = map_date_to_x_coordinate(entry.date, margin_left, plot_width, date_min, date_max)
            py = value_to_y(entry.value, margin_top, plot_height, min_val, max_val)
            dist_sq = (px - x)**2 + (py - y)**2
            if dist_sq < threshold_sq:
                hovered = i
                break

        if hovered != self.hovered_point:
            self.hovered_point = hovered
            self.queue_draw()
            self.emit("hover-changed", hovered if hovered is not None else -1)

    def on_leave(self, _controller: Any) -> None:
        if self.hovered_point is not None:
            self.hovered_point = None
            self.queue_draw()
            self.emit("hover-changed", -1)

    def on_draw(self, _area: Any, cr: Any, width: int, height: int) -> None:
        colors = ChartStyle.get_colors(self.is_dark)

        # Fondo
        cr.set_source_rgb(*colors.bg)
        cr.paint()

        if not self.entries:
            layout = create_layout(cr, "No hay datos disponibles", 16)
            tw, th = layout.get_pixel_size()
            cr.move_to(width / 2 - tw / 2, height / 2)
            cr.set_source_rgb(*colors.text)
            PangoCairo.show_layout(cr, layout)
            return

        margin_left, margin_top, margin_right, margin_bottom = 100, 80, 60, 80
        plot_width = width - margin_left - margin_right
        plot_height = height - margin_top - margin_bottom

        min_val = min(e.value for e in self.entries)
        max_val = max(e.value for e in self.entries)
        date_min = self.entries[0].date
        date_max = self.entries[-1].date

        # Cuadrícula Y
        for i in range(6):
            frac = i / 5
            y = margin_top + plot_height - frac * plot_height
            cr.set_source_rgb(*colors.grid)
            cr.move_to(margin_left, y)
            cr.line_to(margin_left + plot_width, y)
            cr.stroke()

            value = min_val + frac * (max_val - min_val)
            label = self.config.y_format.format(value)
            layout = create_layout(cr, label, 10)
            tw, th = layout.get_pixel_size()
            cr.set_source_rgb(*colors.text)
            cr.move_to(margin_left - tw - 10, y - th / 2)
            PangoCairo.show_layout(cr, layout)

        # Cuadrícula X
        for i in range(6):
            frac = i / 5
            x = margin_left + frac * plot_width
            cr.set_source_rgb(*colors.grid)
            cr.move_to(x, margin_top)
            cr.line_to(x, margin_top + plot_height)
            cr.stroke()

            days_total = (date_max - date_min).days or 1
            date_val = date_min + datetime.timedelta(days=int(frac * days_total))
            layout = create_layout(cr, date_val.strftime("%d/%m"), 10)
            tw, th = layout.get_pixel_size()
            cr.set_source_rgb(*colors.text)
            cr.move_to(x - tw / 2, margin_top + plot_height + 10)
            PangoCairo.show_layout(cr, layout)

        # Ejes
        cr.set_source_rgb(*colors.axes)
        cr.set_line_width(2)
        cr.move_to(margin_left, margin_top)
        cr.line_to(margin_left, margin_top + plot_height)
        cr.line_to(margin_left + plot_width, margin_top + plot_height)
        cr.stroke()

        # Línea
        line_color = self.config.line_color
        cr.set_source_rgb(*line_color)
        cr.set_line_width(3)
        first = True
        for entry in self.entries:
            x = map_date_to_x_coordinate(entry.date, margin_left, plot_width, date_min, date_max)
            y = value_to_y(entry.value, margin_top, plot_height, min_val, max_val)
            if first:
                cr.move_to(x, y)
                first = False
            else:
                cr.line_to(x, y)
        cr.stroke()

        # Marcadores
        for entry in self.entries:
            x = map_date_to_x_coordinate(entry.date, margin_left, plot_width, date_min, date_max)
            y = value_to_y(entry.value, margin_top, plot_height, min_val, max_val)
            cr.arc(x, y, 4, 0, 2 * 3.14159)
            cr.fill()

        # Resaltar punto
        if self.hovered_point is not None and 0 <= self.hovered_point < len(self.entries):
            entry = self.entries[self.hovered_point]
            x = map_date_to_x_coordinate(entry.date, margin_left, plot_width, date_min, date_max)
            y = value_to_y(entry.value, margin_top, plot_height, min_val, max_val)

            cr.set_source_rgb(*colors.bg)
            cr.arc(x, y, 8, 0, 2 * 3.14159)
            cr.stroke()

            cr.set_source_rgb(*line_color)
            cr.arc(x, y, 7, 0, 2 * 3.14159)
            cr.fill()

            # Tooltip
            text = self.config.tooltip_formatter(entry.date, entry.value)
            layout = create_layout(cr, text, 12)
            lw, lh = layout.get_pixel_size()
            tx, ty = x - lw / 2, y - lh - 15
            tx = max(10, min(tx, width - lw - 20))
            ty = max(10, min(ty, height - lh - 20))

            cr.set_source_rgba(*colors.tooltip_bg)
            cr.rectangle(tx - 8, ty - 8, lw + 16, lh + 12)
            cr.fill()

            cr.set_source_rgba(*colors.tooltip_border)
            cr.rectangle(tx - 8, ty - 8, lw + 16, lh + 12)
            cr.stroke()

            cr.move_to(tx, ty + 2)
            cr.set_source_rgb(*colors.tooltip_text)
            PangoCairo.show_layout(cr, layout)

        # Título y etiquetas
        title = create_layout(cr, self.config.title, 16, bold=True)
        tw, th = title.get_pixel_size()
        cr.move_to(width / 2 - tw / 2, margin_top - th - 20)
        cr.set_source_rgb(*colors.text)
        PangoCairo.show_layout(cr, title)

        xlabel = create_layout(cr, self.config.x_label, 12, bold=True)
        tw, th = xlabel.get_pixel_size()
        cr.move_to(margin_left + plot_width / 2 - tw / 2, margin_top + plot_height + 40)
        PangoCairo.show_layout(cr, xlabel)

        ylabel = create_layout(cr, self.config.y_label, 12, bold=True)
        tw, th = ylabel.get_pixel_size()
        cr.move_to(margin_left, margin_top - th - 10)
        PangoCairo.show_layout(cr, ylabel)