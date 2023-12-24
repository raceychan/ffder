import abc
import functools
import pathlib
import typing as ty
from collections.abc import MutableMapping


def flatten(d: MutableMapping, parent_key: str = "", separator: str = "__"):
    items = []
    for key, value in d.items():
        new_key = parent_key.upper() + separator + key if parent_key else key
        if isinstance(value, MutableMapping):
            if not value:
                items.append((new_key, {}))
            else:
                items.extend(flatten(value, new_key, separator=separator).items())
        else:
            items.append((new_key, value))
    return dict(items)


def unflatten(flat_dict: MutableMapping, separator: str = "__"):
    unflattened_dict = {}
    for compound_key, value in flat_dict.items():
        keys = compound_key.split(separator)
        d = unflattened_dict
        for key in keys[:-1]:
            d = d.setdefault(key.lower() if key.isupper() else key, {})
        d[keys[-1]] = value
    return unflattened_dict


class EndOfChainError(Exception):
    ...


class NotDutyError(Exception):
    ...


class UnsupportedFileFormatError(Exception):
    def __init__(self, file: pathlib.Path):
        super().__init__(
            f"File of format {file.suffix} is not supported, as dependency is not installed"
        )


class LoaderNode(ty.Protocol):
    next: ty.Optional["LoaderNode"]
    supported_formats: ty.ClassVar[set[str] | str]

    @abc.abstractmethod
    def _validate(self, file: pathlib.Path) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def loads(self, file: pathlib.Path) -> dict[str, ty.Any]:
        raise NotImplementedError

    @abc.abstractmethod
    def handle(self, file: pathlib.Path) -> dict[str, ty.Any]:
        raise NotImplementedError


class FileLoader(LoaderNode):
    _handle_chain: ty.ClassVar[list[type["LoaderNode"]]] = list()
    supported_formats: ty.ClassVar[set[str] | str]

    def __init__(self) -> None:
        self._next: ty.Optional["FileLoader"] = None

    def __init_subclass__(cls: type["FileLoader"]) -> None:
        cls._handle_chain.append(cls)

    def __str__(self):
        return f"{self.__class__.__name__}({self.supported_formats})"

    def __repr__(self):
        return self.__str__()

    @property
    def next(self) -> ty.Optional["FileLoader"]:
        return self._next

    @next.setter
    def next(self, handler: ty.Optional["FileLoader"]) -> None:
        self._next = handler

    def chain(self, handler: "FileLoader") -> "FileLoader":
        self.next = handler
        return self.next

    def validate(self, file: pathlib.Path) -> bool:
        if not file.is_file() or not file.exists():
            raise FileNotFoundError(f"File {file} not found")
        return self._validate(file)

    def _validate(self, file: pathlib.Path) -> bool:
        supported = self.supported_formats
        if isinstance(supported, str):
            supported = {supported}
        return file.suffix in supported or file.name in supported

    def handle(self, file: pathlib.Path) -> dict[str, ty.Any]:
        if self.validate(file):
            return self.loads(file)

        if self._next is None:
            raise EndOfChainError

        return self._next.handle(file)

    def reverse(self) -> None:
        """
        Reverse the whole chain so that the last node becomes the first node
        Do this when you want your newly added subclass take over the chain
        """
        prev = None
        node = self

        while node.next:
            next = node.next
            node.next = prev
            prev = node
            node = next

        node.next = prev

    @classmethod
    def register(cls, loader: type["LoaderNode"]) -> type["LoaderNode"]:
        """
        Use this to register a new loader to the chain
        """
        cls._handle_chain.append(loader)
        return loader

    @classmethod
    def from_chain(cls, reverse: bool = True) -> "LoaderNode":
        loaders = [loader_cls() for loader_cls in cls._handle_chain]

        if reverse:
            loaders = list(reversed(loaders))

        head = node = loaders[0]

        for loader in loaders[1:]:
            node.next = loader
            node = loader
        return head


class ENVFileLoader(FileLoader):
    supported_formats = ".env"

    def loads(self, file: pathlib.Path) -> dict[str, ty.Any]:
        try:
            import dotenv
        except ImportError as ie:
            raise UnsupportedFileFormatError(file) from ie

        return dotenv.dotenv_values(file)


class TOMLFileLoader(FileLoader):
    supported_formats = ".toml"

    def loads(self, file: pathlib.Path) -> dict[str, ty.Any]:
        try:
            import tomllib
        except ModuleNotFoundError:
            import tomli as tomllib
        except ImportError as ie:
            raise UnsupportedFileFormatError(file) from ie

        config = tomllib.loads(file.read_text())
        return config


class YAMLFileLoader(FileLoader):
    supported_formats = {".yml", ".yaml"}

    def loads(self, file: pathlib.Path) -> dict[str, ty.Any]:
        try:
            import yaml
        except ImportError as ie:
            raise UnsupportedFileFormatError(file) from ie

        config: dict[str, ty.Any] = yaml.safe_load(file.read_bytes())
        return config


class JsonFileLoader(FileLoader):
    supported_formats = ".json"

    def loads(self, file: pathlib.Path) -> dict[str, ty.Any]:
        try:
            import json
        except ImportError as ie:
            raise UnsupportedFileFormatError(file) from ie

        config: dict[str, ty.Any] = json.loads(file.read_bytes())
        return config


class FileUtil:
    def __init__(
        self,
        work_dir: pathlib.Path = pathlib.Path.cwd(),
        file_loader: LoaderNode = FileLoader.from_chain(),
    ):
        self.work_dir = work_dir
        self.file_loader = file_loader

    def find(self, filename: str, dir: str | None = None) -> pathlib.Path:
        work_dir = pathlib.Path(dir) if dir is not None else self.work_dir

        rg = work_dir.rglob(filename)
        try:
            file = next(rg)
        except StopIteration as se:
            raise FileNotFoundError(
                f"File '{filename}' not found in current directory {work_dir}"
            ) from se
        return file

    def loads(self, file: str | pathlib.Path) -> dict[str, ty.Any]:
        """
        Example:
        ---

        >>> config = FileUtil().read_file(".env")
        >>> assert isinstance(config, dict)
        True
        """
        if isinstance(file, str):
            file = self.find(file)
        try:
            data = self.file_loader.handle(file)
        except EndOfChainError as ee:
            raise UnsupportedFileFormatError(file) from ee
        return data

    @classmethod
    @functools.lru_cache(maxsize=1)
    def from_cwd(cls) -> "FileUtil":
        return cls(work_dir=pathlib.Path.cwd(), file_loader=FileLoader.from_chain())


def loads(file: str | pathlib.Path) -> dict[str, ty.Any]:
    return FileUtil.from_cwd().loads(file)


def find(filename: str, dir: str | None = None) -> pathlib.Path:
    return FileUtil.from_cwd().find(filename, dir)
