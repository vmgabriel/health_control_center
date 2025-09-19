import abc
import json
import pathlib

class ConfigurationRepository(abc.ABC):
    @abc.abstractmethod
    def exists(self) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def create_default(self) -> None:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all(self) -> dict[str, str]:
        raise NotImplementedError()

    @abc.abstractmethod
    def save(self, file_path: pathlib.Path) -> None:
        raise NotImplementedError()


class FileJSONConfigurationRepository(ConfigurationRepository):
    def __init__(self, file_path: pathlib.Path):
        self.file_path = file_path

    def create_default(self) -> None:
        with open(self.file_path, 'w') as f:
            json.dump({}, f, indent=4)

    def exists(self) -> bool:
        return self.file_path.exists()

    def get_all(self) -> dict[str, str]:
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def save(self, file_path: pathlib.Path) -> None:
        with open(self.file_path, 'w') as f:
            json.dump({"file_csv": str(file_path.absolute())}, f, indent=4)