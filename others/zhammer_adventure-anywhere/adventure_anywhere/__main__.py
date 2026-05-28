import sys

from adventure_anywhere.file_system_saves import FileSystemSavesGateway
from adventure_anywhere.definitions import Context
from adventure_anywhere.use_adventure import do_command
from adventure_anywhere.exceptions import CommandPolicyViolationError

file_system_saves = FileSystemSavesGateway()
context = Context(saves=file_system_saves)

player_id = sys.argv[1]
command = sys.argv[2]

try:
    output = do_command(context, command, player_id)
except CommandPolicyViolationError as e:
    print(f"*COMMAND POLICY VIOLATION ERROR: {str(e)}*")
else:
    print(output)
