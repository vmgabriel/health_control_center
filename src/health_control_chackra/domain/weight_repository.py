import abc
import datetime
import pathlib
import csv


class WeightRepository(abc.ABC):
    @abc.abstractmethod
    def exists(self) -> bool:
        raise NotImplementedError()

    @abc.abstractmethod
    def get_all(self) -> list[dict]:
        raise NotImplementedError()

    @abc.abstractmethod
    def insert(self, weight: float, date: datetime.date) -> None:
        raise NotImplementedError()


class FileCsvWeightRepository(WeightRepository):
    def __init__(self, file_path: pathlib.Path):
        self.file_path = file_path

    def exists(self) -> bool:
        return self.file_path.exists()

    def get_all(self) -> list[dict]:
        with open(self.file_path, 'r') as f:
            reader = csv.DictReader(f)
            return list(reader)

    def insert(self, weight: float, date: datetime.date) -> None:
        if not self.exists():
            self.file_path.touch()
            self.file_path.write_text('date,weight\n')

        with open(self.file_path, 'a') as f:
            writer = csv.DictWriter(f, fieldnames=['date', 'weight'])
            writer.writerow({'date': date.strftime('%Y-%m-%d'), 'weight': weight})
