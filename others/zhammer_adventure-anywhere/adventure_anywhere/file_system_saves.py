import io
import os
from pathlib import Path
from typing import Optional

from adventure_anywhere.definitions import SavesGateway


class FileSystemSavesGateway(SavesGateway):
    saves_directory_path: Path

    def __init__(self, saves_directory: Optional[str] = None) -> None:
        self.saves_directory_path = Path(saves_directory or "adventure_anywhere_file_saves")
        if not self.saves_directory_path.exists():
            os.makedirs(self.saves_directory_path)

    def fetch_save(self, player_id: str) -> Optional[io.BytesIO]:
        save_file_path = self.saves_directory_path / player_id
        if not save_file_path.exists():
            return None

        with open(save_file_path, "rb") as save_file:
            return io.BytesIO(save_file.read())

    def update_save(self, player_id: str, save: io.BytesIO) -> None:
        save_file_path = self.saves_directory_path / player_id
        with open(save_file_path, "wb") as save_file:
            save_file.write(save.getvalue())
