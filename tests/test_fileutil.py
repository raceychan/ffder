import pathlib

import pytest

from ffder.main import FileLoader, FileUtil, UnsupportedFileFormatError


@pytest.fixture(scope="session")
def fileloader():
    return FileLoader.from_chain()


@pytest.fixture(scope="session")
def fileutil(fileloader: FileLoader):
    from pathlib import Path

    return FileUtil(work_dir=Path.cwd(), file_loader=fileloader)


def test_load_env(fileutil: FileUtil, tmp_path: pathlib.Path):
    env_file = tmp_path / ".env"
    env_file.write_text("TEST=true")
    values = fileutil.read_file(env_file)
    assert values["TEST"] == "true"
    assert isinstance(values, dict)


def test_not_file_not_found_err(fileloader: FileLoader):
    error_file = pathlib.Path("none_exists.err")
    with pytest.raises(FileNotFoundError):
        _ = fileloader.handle(error_file)


def test_load_toml(fileloader: FileLoader, tmp_path: pathlib.Path):
    toml = tmp_path / "settings.toml"
    toml.write_text("TEST=true")
    file = pathlib.Path(toml)
    values = fileloader.handle(file)
    assert values["TEST"] is True


def test_unsupported_file_format(fileutil: FileUtil, tmp_path: pathlib.Path):
    unsupported_file = tmp_path / "settings.ini"
    unsupported_file.write_text("TEST=true")
    file = pathlib.Path(unsupported_file)
    with pytest.raises(UnsupportedFileFormatError):
        _ = fileutil.read_file(file)
