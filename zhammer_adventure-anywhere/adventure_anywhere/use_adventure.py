from adventure_anywhere import policies, special_sms_functionality
from adventure_anywhere.definitions import Context
from adventure_anywhere.exceptions import CommandPolicyViolationError
from adventure_anywhere.game import GameEngine


def do_command(context: Context, command_text: str, player_id: str) -> str:
    """
    If a game hasn't been started, starts a game and returns the start output.
    Otherwise, resumes the game where it last left off and does the provided command.
    """
    game_engine = GameEngine()
    command_text = special_sms_functionality.preprocess_command(
        command_text, context.config
    )

    command_invalid_reason = policies.command.invalid_reason(command_text)
    if command_invalid_reason:
        raise CommandPolicyViolationError(command_invalid_reason)

    last_save = context.saves.fetch_save(player_id)

    if special_sms_functionality.is_restart_command(command_text) or not last_save:
        start_text = game_engine.start()
        response_text = special_sms_functionality.add_after_start_notices(
            start_text, context.config
        )

    else:
        game_engine.resume(last_save)
        response_text = game_engine.do_command(command_text)

    new_save = game_engine.save()
    context.saves.update_save(player_id, new_save)

    return response_text


def last_output(context: Context, player_id: str) -> str:
    """
    If a game hasn't been started, starts a game and returns the start output.
    Otherwise, returns the last output from the game.
    """
    game_engine = GameEngine()

    last_save = context.saves.fetch_save(player_id)
    if not last_save:
        start_text = game_engine.start()
        response_text = special_sms_functionality.add_after_start_notices(
            start_text, context.config
        )
    else:
        game_engine.resume(last_save)
        response_text = game_engine.last_output()

    return response_text

