import unittest
from datetime import date
from unittest.mock import patch, MagicMock
import cairo
import gi  # type: ignore
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango  # noqa: E402
from health_control_chackra.chart import time_series_chart as subject  # noqa: E402


DATE_FORMAT = "%Y-%m-%d"


class TestTimeSeriesEntry(unittest.TestCase):

    def test_time_series_entry_initialization(self):
        entry = subject.TimeSeriesEntry(date=date(2025, 9, 18), value=100.5)
        self.assertEqual(entry.date, date(2025, 9, 18))
        self.assertEqual(entry.value, 100.5)

    def test_time_series_entry_from_str_valid(self):
        entry = subject.TimeSeriesEntry.from_str("2025-09-18", 100.5)
        self.assertIsNotNone(entry)
        self.assertEqual(entry.date, date(2025, 9, 18))
        self.assertEqual(entry.value, 100.5)

    def test_time_series_entry_from_str_invalid_date(self):

        entry = subject.TimeSeriesEntry.from_str("not-a-date", 100.5)
        self.assertIsNone(entry)

    def test_time_series_entry_from_str_invalid_value(self):
        entry = subject.TimeSeriesEntry.from_str("2025-09-18", "invalid-value")
        self.assertIsNone(entry)


class TestChartStyle(unittest.TestCase):
    def test_get_colors_dark_mode(self):
        colors = subject.ChartStyle.get_colors(is_dark=True)
        self.assertIsInstance(colors, subject.ChartColors)
        self.assertEqual(colors.bg, (0.1, 0.1, 0.1))
        self.assertEqual(colors.grid, (0.3, 0.3, 0.3))
        self.assertEqual(colors.axes, (0.7, 0.7, 0.7))
        self.assertEqual(colors.text, (0.9, 0.9, 0.9))
        self.assertEqual(colors.line, (0.3, 0.6, 1.0))
        self.assertEqual(colors.tooltip_bg, (0.2, 0.2, 0.2, 0.95))
        self.assertEqual(colors.tooltip_border, (0.6, 0.6, 0.6, 1.0))
        self.assertEqual(colors.tooltip_text, (1.0, 1.0, 1.0))

    def test_get_colors_light_mode(self):
        colors = subject.ChartStyle.get_colors(is_dark=False)
        self.assertIsInstance(colors, subject.ChartColors)
        self.assertEqual(colors.bg, (1.0, 1.0, 1.0))
        self.assertEqual(colors.grid, (0.9, 0.9, 0.9))
        self.assertEqual(colors.axes, (0.4, 0.4, 0.4))
        self.assertEqual(colors.text, (0.1, 0.1, 0.1))
        self.assertEqual(colors.line, (0.2, 0.5, 0.8))
        self.assertEqual(colors.tooltip_bg, (1.0, 1.0, 1.0, 0.95))
        self.assertEqual(colors.tooltip_border, (0.8, 0.8, 0.8, 1.0))
        self.assertEqual(colors.tooltip_text, (0.1, 0.1, 0.1))


class TestScaleFunction(unittest.TestCase):
    def test_scale_valid_range(self):
        result = subject.scale(50, 0, 100, 0, 10)
        self.assertEqual(result, 5.0)

    def test_scale_min_max_equal(self):
        result = subject.scale(50, 50, 50, 0, 10)
        self.assertEqual(result, 5.0)

    def test_scale_value_below_min(self):
        result = subject.scale(-10, 0, 100, 0, 10)
        self.assertEqual(result, -1.0)

    def test_scale_value_above_max(self):
        result = subject.scale(150, 0, 100, 0, 10)
        self.assertEqual(result, 15.0)

    def test_scale_value_at_min(self):
        result = subject.scale(0, 0, 100, 0, 10)
        self.assertEqual(result, 0.0)

    def test_scale_value_at_max(self):
        result = subject.scale(100, 0, 100, 0, 10)
        self.assertEqual(result, 10.0)

    def test_scale_negative_range(self):
        result = subject.scale(-50, -100, 0, -10, 0)
        self.assertEqual(result, -5.0)

    def test_scale_output_flipped_range(self):
        result = subject.scale(50, 0, 100, 10, 0)
        self.assertEqual(result, 5.0)


class TestDetectDarkMode(unittest.TestCase):
    @patch("health_control_chackra.chart.time_series_chart.Gtk")
    def test_detect_dark_mode_prefer_dark_true(self, mock_gtk):
        mock_settings = MagicMock()
        mock_gtk.Settings.get_default.return_value = mock_settings
        mock_settings.get_property.side_effect = lambda prop: {
            "gtk-application-prefer-dark-theme": True,
            "gtk-theme-name": "Adwaita-dark",
        }.get(prop, None)

        result = subject.detect_dark_mode()
        self.assertTrue(result)

    @patch("health_control_chackra.chart.time_series_chart.Gtk")
    def test_detect_dark_mode_prefer_dark_false_theme_name_contains_dark(self, mock_gtk):
        mock_settings = MagicMock()
        mock_gtk.Settings.get_default.return_value = mock_settings
        mock_settings.get_property.side_effect = lambda prop: {
            "gtk-application-prefer-dark-theme": False,
            "gtk-theme-name": "Adwaita-dark",
        }.get(prop, None)

        result = subject.detect_dark_mode()
        self.assertTrue(result)

    @patch("health_control_chackra.chart.time_series_chart.Gtk")
    def test_detect_dark_mode_prefer_dark_false_theme_name_does_not_contain_dark(self, mock_gtk):
        mock_settings = MagicMock()
        mock_gtk.Settings.get_default.return_value = mock_settings
        mock_settings.get_property.side_effect = lambda prop: {
            "gtk-application-prefer-dark-theme": False,
            "gtk-theme-name": "Adwaita-light",
        }.get(prop, None)

        result = subject.detect_dark_mode()
        self.assertFalse(result)

    @patch("health_control_chackra.chart.time_series_chart.Gtk")
    def test_detect_dark_mode_no_settings(self, mock_gtk):
        mock_gtk.Settings.get_default.return_value = None

        result = subject.detect_dark_mode()
        self.assertFalse(result)


class TestMapDateToXCoordinate(unittest.TestCase):
    def test_map_date_to_x_coordinate_within_range(self):
        result = subject.map_date_to_x_coordinate(
            date=date(2025, 9, 18),
            margin_left=10,
            plot_width=100,
            date_min=date(2025, 9, 1),
            date_max=date(2025, 9, 30),
        )
        self.assertEqual(result, 68.62068965517241)

    def test_map_date_to_x_coordinate_start_of_range(self):
        result = subject.map_date_to_x_coordinate(
            date=date(2025, 9, 1),
            margin_left=20,
            plot_width=200,
            date_min=date(2025, 9, 1),
            date_max=date(2025, 9, 30),
        )
        self.assertEqual(result, 20.0)

    def test_map_date_to_x_coordinate_end_of_range(self):
        result = subject.map_date_to_x_coordinate(
            date=date(2025, 9, 30),
            margin_left=15,
            plot_width=300,
            date_min=date(2025, 9, 1),
            date_max=date(2025, 9, 30),
        )
        self.assertEqual(result, 315.0)

    def test_map_date_to_x_coordinate_single_day_range(self):
        result = subject.map_date_to_x_coordinate(
            date=date(2025, 9, 18),
            margin_left=10,
            plot_width=50,
            date_min=date(2025, 9, 18),
            date_max=date(2025, 9, 18),
        )
        self.assertEqual(result, 10.0)

    def test_map_date_to_x_coordinate_outside_range(self):
        result = subject.map_date_to_x_coordinate(
            date=date(2025, 8, 31),
            margin_left=10,
            plot_width=100,
            date_min=date(2025, 9, 1),
            date_max=date(2025, 9, 30),
        )
        self.assertEqual(result, 6.551724137931035)


class TestCreateLayout(unittest.TestCase):
    def setUp(self):
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 100, 100)
        self.cr = cairo.Context(self.surface)

    def test_create_layout_standard_font(self):
        text = "Testing"
        size = 12

        layout = subject.create_layout(cr=self.cr, text=text, size=size)

        self.assertIsInstance(layout, Pango.Layout)
        self.assertEqual(layout.get_text(), text)

    def test_create_layout_bold_font(self):
        text = "Bold Testing"
        size = 14
        bold = True

        layout = subject.create_layout(cr=self.cr, text=text, size=size, bold=bold)
        font_desc = layout.get_font_description()

        self.assertIsInstance(layout, Pango.Layout)
        self.assertEqual(layout.get_text(), text)
        self.assertTrue(font_desc.get_weight() == Pango.Weight.BOLD)

    def test_create_layout_non_bold_font(self):
        text = "Regular Testing"
        size = 10
        bold = False

        layout = subject.create_layout(cr=self.cr, text=text, size=size, bold=bold)
        font_desc = layout.get_font_description()

        self.assertIsInstance(layout, Pango.Layout)
        self.assertEqual(layout.get_text(), text)
        self.assertTrue(font_desc.get_weight() != Pango.Weight.BOLD)


class TestChartConfig(unittest.TestCase):
    def test_chart_config_default_values(self):
        config = subject.ChartConfig()
        self.assertEqual(config.title, "Graph")
        self.assertEqual(config.x_label, "Date")
        self.assertEqual(config.y_label, "Value")
        self.assertEqual(config.y_format, "{:.1f}")
        self.assertEqual(config.line_color, (0.2, 0.5, 0.8))
        self.assertIsNotNone(config.tooltip_formatter)

    def test_chart_config_custom_values(self):
        custom_formatter = MagicMock()
        config = subject.ChartConfig(
            title="Custom Chart",
            x_label="Custom Date",
            y_label="Custom Value",
            y_format="{:.2f}",
            line_color=(1.0, 0.0, 0.0),
            tooltip_formatter=custom_formatter
        )
        self.assertEqual(config.title, "Custom Chart")
        self.assertEqual(config.x_label, "Custom Date")
        self.assertEqual(config.y_label, "Custom Value")
        self.assertEqual(config.y_format, "{:.2f}")
        self.assertEqual(config.line_color, (1.0, 0.0, 0.0))
        self.assertIs(config.tooltip_formatter, custom_formatter)

    def test_chart_config_post_init_default_formatter(self):
        config = subject.ChartConfig(tooltip_formatter=None)
        formatted_tooltip = config.tooltip_formatter(date(2025, 9, 18), 100.5)
        self.assertIn("2025-09-18", formatted_tooltip)
        self.assertIn("Value: 100.5", formatted_tooltip)


class TestValueToY(unittest.TestCase):
    def test_value_to_y_with_normal_values(self):
        result = subject.value_to_y(value=50, margin_top=10, plot_height=200, min_val=0, max_val=100)
        expected = 110  # Calculated manually or with known expected behavior
        self.assertAlmostEqual(result, expected)

    def test_value_to_y_with_minimum_value(self):
        result = subject.value_to_y(value=0, margin_top=10, plot_height=200, min_val=0, max_val=100)
        expected = 208.0392156862745   # For minimum value expected position
        self.assertAlmostEqual(result, expected)

    def test_value_to_y_with_maximum_value(self):
        result = subject.value_to_y(value=100, margin_top=10, plot_height=200, min_val=0, max_val=100)
        expected = 11.960784313725469  # For maximum value expected position
        self.assertAlmostEqual(result, expected)

    def test_value_to_y_with_negative_values(self):
        result = subject.value_to_y(value=-50, margin_top=10, plot_height=200, min_val=-100, max_val=0)
        expected = 110  # For a negative value expected position within range
        self.assertAlmostEqual(result, expected)

    def test_value_to_y_with_large_plot_height(self):
        result = subject.value_to_y(value=50, margin_top=20, plot_height=1000, min_val=0, max_val=100)
        expected = 520  # Testing with a larger plot height
        self.assertAlmostEqual(result, expected)
