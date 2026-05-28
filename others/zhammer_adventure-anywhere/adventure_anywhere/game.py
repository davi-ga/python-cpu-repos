import io
import re
from typing import Optional

import adventure
from adventure.game import Game

from adventure_anywhere.definitions import GameEngine as GameEngineABC


class GameEngine(GameEngineABC):
    game: Optional[Game]

    def __init__(self) -> None:
        self.game = None

    def start(self) -> str:
        if self.game:
            raise GameAlreadyStartedError

        self.game = Game()
        adventure.load_advent_dat(self.game)
        self.game.start()
        return self.game.output

    def resume(self, save: io.BytesIO) -> None:
        if self.game:
            raise GameAlreadyStartedError

        self.game = Game.resume(save)

    def do_command(self, command: str) -> str:
        if not self.game:
            raise GameNotStartedError

        words = re.findall(r"\w+", command)
        return self.game.do_command(words)

    def save(self) -> io.BytesIO:
        if not self.game:
            raise GameNotStartedError

        save_data_stream = io.BytesIO()
        self.game.t_suspend(verb=None, obj=save_data_stream)
        return save_data_stream

    def last_output(self) -> str:
        if not self.game:
            raise GameNotStartedError

        return self.game.output

    @staticmethod
    def help_prompt() -> str:
        game = Game()
        adventure.load_advent_dat(game)
        return str(game.messages[51])


class GameNotStartedError(Exception):
    message = "Game has not been started"


class GameAlreadyStartedError(Exception):
    message = "Game already started"
