import logging
import pathlib
import datetime
import gi  # type: ignore
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk  # noqa: E402
from gi.repository import Adw  # noqa: E402
from health_control_chackra.domain import configuration_repository, weight_repository  # noqa: E402
from health_control_chackra.chart import time_series_chart  # noqa: E402
from health_control_chackra.dialog import configuration_dialog, add_weight_dialog  # noqa: E402


_JSON_CONFIGURATION = pathlib.Path(__file__).parent / "configuration.json"
logger = logging.getLogger(__name__)


class MainWindow(Adw.ApplicationWindow):
    banner: Adw.Banner | None = None

    def __init__(self, app, configuration: dict[str, str] | None = None):
        super().__init__(application=app)
        self.configuration = configuration or {}
        self.current_file_path: pathlib.Path | None = None

        self.set_title("📉 Seguimiento de Peso")
        self.set_default_size(1000, 700)

        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        data = self._load_initial_data()

        if not data:
            self._add_missing_file_banner(toolbar_view)

        header_bar = self._create_headerbar()
        toolbar_view.add_top_bar(header_bar)

        self.chart = self._create_chart(data)
        toolbar_view.set_content(self.chart)

    def _add_missing_file_banner(self, toolbar_view: Adw.ToolbarView) -> None:
        self.banner = Adw.Banner.new("⚠️ No se ha configurado el archivo de datos.")
        self.banner.set_revealed(True)
        self.banner.set_button_label("Configurar")
        self.banner.connect("button-clicked", lambda b: self.on_configure_clicked())
        toolbar_view.add_top_bar(self.banner)

    def _create_headerbar(self) -> Adw.HeaderBar:
        header_bar = Adw.HeaderBar()

        add_button = Gtk.Button(
            child=Gtk.Image.new_from_icon_name("list-add-symbolic"),
            tooltip_text="Agregar nuevo peso",
            css_classes=["circular"]
        )
        add_button.connect("clicked", self.on_add_weight_clicked)
        header_bar.pack_start(add_button)

        config_button = Gtk.Button(
            child=Gtk.Image.new_from_icon_name("emblem-system-symbolic"),
            tooltip_text="Configuración",
            css_classes=["circular"]
        )
        config_button.connect("clicked", lambda b: self.on_configure_clicked())
        header_bar.pack_end(config_button)

        return header_bar

    def _create_chart(self, data) -> time_series_chart.TimeSeriesChartWidget:
        config = time_series_chart.ChartConfig(
            title="Seguimiento de Peso",
            y_label="Peso (kg)",
            y_format="{:.1f}",
            line_color=(0.2, 0.5, 0.8),
        )
        return time_series_chart.TimeSeriesChartWidget(data=data, config=config)

    def _load_initial_data(self) -> list[tuple[str, float]]:
        file_path_str = self.configuration.get("file_csv", "").strip()
        if not file_path_str:
            return []

        path = pathlib.Path(file_path_str)
        if not path.exists():
            logger.warning(f"Archivo CSV no encontrado: {path}")
            return []

        try:
            repo = weight_repository.FileCsvWeightRepository(path)
            data = [(entry["date"], float(entry["weight"])) for entry in repo.get_all()]
            logger.info("Loading data... %d register from %s", len(data), path)
            self.current_file_path = path
            return data
        except Exception as e:
            logger.error(f"Error al cargar datos: {e}")
            return []

    def load_data_from_path(self, path: pathlib.Path) -> None:
        try:
            repo = weight_repository.FileCsvWeightRepository(path)
            entries = [
                time_series_chart.TimeSeriesEntry.from_str(entry["date"], float(entry["weight"]))
                for entry in repo.get_all()
            ]
            current_entries: list[time_series_chart.TimeSeriesEntry] = [e for e in entries if e]
            self.chart.entries = sorted(current_entries, key=lambda x: x.date)
            self.chart.queue_draw()
            self.current_file_path = path
            logger.info(f"✅ Datos recargados desde {path}")

            if self.banner is not None:
                self.banner.set_revealed(False)
                self.banner = None

        except Exception as e:
            logger.error(f"Error al cargar datos: {e}")


    def on_add_weight_clicked(self, button: Gtk.Button) -> None:
        def on_save(date: str, weight: float) -> None:
            entry = time_series_chart.TimeSeriesEntry.from_str(date, weight)
            if not entry:
                return
            self.chart.entries.append(entry)
            self.chart.entries.sort(key=lambda x: x.date)

            if self.current_file_path:
                weight_repository.FileCsvWeightRepository(self.current_file_path).insert(
                    weight=weight,
                    date=datetime.datetime.strptime(date, "%Y-%m-%d").date()
                )
                logger.info(f"➕ Peso guardado: {date} - {weight} kg")

        dialog = add_weight_dialog.AddWeightDialog(parent=self, on_save=on_save)
        dialog.present()

    def on_configure_clicked(self) -> None:
        def on_save(file_path: str) -> None:
            path = pathlib.Path(file_path)
            repo = configuration_repository.FileJSONConfigurationRepository(_JSON_CONFIGURATION)
            repo.save(path)
            self.load_data_from_path(path)

        dialog = configuration_dialog.ConfigurationDialog(
            parent=self,
            on_save=on_save,
            file_path=self.current_file_path
        )
        dialog.present()