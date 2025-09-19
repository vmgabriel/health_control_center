import pathlib
import datetime
import pytest
from health_control_chackra.domain import weight_repository as subject


@pytest.unittests
def test_filecsvweightrepository_exists_with_existing_file(tmp_path):
    file_path = tmp_path / "weights.csv"
    file_path.touch()  # Create the file
    repository = subject.FileCsvWeightRepository(file_path)

    assert repository.exists() is True


@pytest.unittests
def test_filecsvweightrepository_exists_with_nonexistent_file():
    file_path = pathlib.Path("nonexistent.csv")
    repository = subject.FileCsvWeightRepository(file_path)

    assert repository.exists() is False


@pytest.unittests
def test_filecsvweightrepository_get_all_with_data(tmp_path):
    file_path = tmp_path / "weights.csv"
    file_path.write_text("date,weight\n2025-09-01,70\n2025-09-02,72\n")  # Add some test data
    repository = subject.FileCsvWeightRepository(file_path)

    result = repository.get_all()

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == {'date': '2025-09-01', 'weight': '70'}
    assert result[1] == {'date': '2025-09-02', 'weight': '72'}


@pytest.unittests
def test_filecsvweightrepository_get_all_with_empty_file(tmp_path):
    file_path = tmp_path / "weights.csv"
    file_path.write_text("")  # Create an empty file
    repository = subject.FileCsvWeightRepository(file_path)

    result = repository.get_all()

    assert isinstance(result, list)
    assert len(result) == 0


@pytest.unittests
def test_filecsvweightrepository_insert(tmp_path):
    file_path = tmp_path / "weights.csv"
    repository = subject.FileCsvWeightRepository(file_path)

    date = datetime.date(2025, 9, 1)
    weight = 70.0
    repository.insert(weight, date)

    with open(file_path, "r") as f:
        content = f.read()

    assert "date,weight\n2025-09-01,70.0\n" in content


@pytest.unittests
def test_filecsvweightrepository_insert_append_to_existing_file(tmp_path):
    file_path = tmp_path / "weights.csv"
    file_path.write_text("date,weight\n2025-09-01,68.5\n")  # Add initial data
    repository = subject.FileCsvWeightRepository(file_path)

    date = datetime.date(2025, 9, 2)
    weight = 72.0
    repository.insert(weight, date)

    with open(file_path, "r") as f:
        content = f.read()

    assert content == "date,weight\n2025-09-01,68.5\n2025-09-02,72.0\n"