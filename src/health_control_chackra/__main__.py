import pathlib

from gi.repository import Adw    # type: ignore

from health_control_chackra.ui import main_window
from health_control_chackra.domain import configuration_repository


_JSON_CONFIGURATION = __file__.replace("__main__.py", "configuration.json")


class Application(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.chackra.health_control")
        self.config_repo = configuration_repository.FileJSONConfigurationRepository(
            pathlib.Path(_JSON_CONFIGURATION)
        )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            if not self.config_repo.exists():
                self.config_repo.create_default()
            config = self.config_repo.get_all()
            win = main_window.MainWindow(app=self, configuration=config)
        win.present()


def main():
    Adw.init()
    app = Application()
    app.run(None)


if __name__ == "__main__":
    main()