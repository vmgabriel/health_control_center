import pathlib
import json

import pytest

from health_control_chackra.domain import configuration_repository as subject


@pytest.fixture
def temp_file(tmp_path):
    return tmp_path / "config.json"


@pytest.fixture
def repository(temp_file):
    return subject.FileJSONConfigurationRepository(file_path=temp_file)


def test_create_default_creates_empty_json(repository, temp_file):
    repository.create_default()
    assert temp_file.exists()
    with open(temp_file, "r") as f:
        data = json.load(f)
    assert data == {}


def test_exists_returns_true_when_file_exists(repository, temp_file):
    temp_file.touch()
    assert repository.exists()


def test_exists_returns_false_when_file_does_not_exist(repository):
    assert not repository.exists()


def test_get_all_returns_content_of_json_file(repository, temp_file):
    initial_data = {"key": "value"}
    with open(temp_file, "w") as f:
        json.dump(initial_data, f)
    result = repository.get_all()
    assert result == initial_data


def test_get_all_raises_error_when_file_does_not_exist(repository):
    with pytest.raises(FileNotFoundError):
        repository.get_all()


def test_save_writes_file_path_to_json(repository, temp_file):
    new_file_path = pathlib.Path("/path/to/file.csv")
    repository.save(file_path=new_file_path)
    with open(temp_file, "r") as f:
        data = json.load(f)
    assert data == {"file_csv": str(new_file_path.absolute())}