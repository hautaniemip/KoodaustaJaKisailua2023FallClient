from __future__ import annotations

import random
from enum import Enum
from logging import getLogger
from typing import TYPE_CHECKING

from src.helpers import get_coordinate_difference, get_approximate_direction

if TYPE_CHECKING:
    from apiwrapper.websocket_wrapper import ClientContext
from apiwrapper.models import GameState, Command, ActionType, MoveActionData, CellType, CompassDirection, \
    ShootActionData, TurnActionData, Coordinates


class State(Enum):
    Shoot = 0
    Turn = 1
    Move = 2


ai_logger = getLogger("team_ai")
"""You can use this logger to track the behaviour of your bot. 

This is preferred to calling print("msg") as it offers 
better configuration (see README.md in root)

Examples:
    >>> ai_logger.debug("A message that is not important but helps with understanding the code during problem solving.")
    >>> ai_logger.info("A message that you want to see to know the state of the bot during normal operation.")
    >>> ai_logger.warning("A message that demands attention, but is not yet causing problems.")
    >>> ai_logger.error("A message about the bot reaching an erroneous state")
    >>> ai_logger.exception("A message that is same as error, but can be only called in Except blocks. " +
    >>>                     "Includes exception info in the log")
    >>> ai_logger.critical("A message about a critical exception, usually causing a premature shutdown")
"""


def process_tick(context: ClientContext, game_state: GameState) -> Command | None:
    """Main function defining the behaviour of the AI of the team

    Arguments:
        context (ClientContext): persistent context that can store data and state between ticks. Wiped on game creation
        game_state (GameState): the current state of the game

    Returns:
        Command: `apiwrapper.models.Command` instance containing the type and data of the command to be executed on the
        tick. Returning None tells server to move 0 steps forward.

    Note:
        You can get tick time in milliseconds from `context.tick_length_ms` and ship turn rate in 1/8th circles from
        `context.turn_rate`.

        If your function takes longer than the max tick length the function is cancelled and None is returned.
    """
    ai_logger.info("processing tick")
    # please add your code here

    action = random.choice(list(State))

    if action == State.Move:
        return Command(ActionType.Move, MoveActionData(random.randint(1, 3)))

    if action == State.Turn:
        return Command(ActionType.Turn, TurnActionData(random.choice(list(CompassDirection))))

    if action == State.Shoot:
        return Command(ActionType.Shoot, ShootActionData(random.randint(1, 4), random.randint(1, 4)))

    return Command(ActionType.Turn, TurnActionData(CompassDirection.East))
