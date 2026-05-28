import abc
import io
from typing import Callable, NamedTuple, NewType, Optional


Notice = NewType("Notice", str)


class SavesGateway(abc.ABC):
    @abc.abstractmethod
    def fetch_save(self, player_id: str) -> Optional[io.BytesIO]:
        ...

    @abc.abstractmethod
    def update_save(self, player_id: str, save: io.BytesIO) -> None:
        ...


class GameEngine(abc.ABC):
    @abc.abstractmethod
    def resume(self, save: io.BytesIO) -> None:
        ...

    @abc.abstractmethod
    def start(self) -> str:
        ...

    @abc.abstractmethod
    def do_command(self, command: str) -> str:
        ...

    @abc.abstractmethod
    def save(self) -> io.BytesIO:
        ...

    @abc.abstractmethod
    def last_output(self) -> str:
        ...


class Config(NamedTuple):
    preprocess_command: Optional[Callable[[str], str]] = None
    after_start_notice: Optional[Notice] = None


class Context(NamedTuple):
    saves: SavesGateway
    config: Config = Config()
