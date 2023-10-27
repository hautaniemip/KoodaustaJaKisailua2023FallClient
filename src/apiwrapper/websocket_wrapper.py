import asyncio
import json
import multiprocessing
from abc import ABC, abstractmethod
from enum import Enum
from multiprocessing.pool import ThreadPool
from typing import Callable, Any

from websockets.sync.client import connect

from apiwrapper.helpers import get_config
from apiwrapper.models import Command, MoveActionData, GameState
from apiwrapper.serialization import deserialize_game_state, serialize_command
from team_ai import process_tick


class ClientState(Enum):
    Unconnected = 0,
    Unauthorized = 1,
    Idle = 2,
    InGame = 3


class ClientContext:
    pass


class Client:
    def __init__(self, state: ClientState = ClientState.Unconnected, context: ClientContext = None):
        self.state: ClientState = state
        self.context: ClientContext = context if context is not None else ClientContext()


def handle_auth_ack(client, *_):
    if client.state == ClientState.Unauthorized:
        client.state = ClientState.Idle
        print("Authorization successful")


def handle_game_start(client, _, websocket):
    assert client.state == ClientState.Idle, (f"Game can only be started in idle state! State right now is: "
                                              f"{client.state}")
    client.context = ClientContext()
    client.state = ClientState.InGame
    websocket.send(json.dumps({"eventType": "startAck", "data": {}}))


def handle_game_tick(client, raw_state, websocket):
    assert client.state == ClientState.InGame, (f"Game ticks can only be handled while in in-game state! State right "
                                                f"now is: {client.state}")
    state = deserialize_game_state(raw_state)
    action = _handle_tick_processing_timeout(client, state)
    if action is None:
        action = Command("move", MoveActionData(0))
    serialized_action = serialize_command(action)
    websocket.send(json.dumps({"eventType": "gameAction", "data": serialized_action}))


def _handle_tick_processing_timeout(client: Client, state: GameState) -> Command | None:
    try:
        with ThreadPool() as pool:
            return pool.apply_async(process_tick, (client.context, state)).get(
                timeout=int(get_config("tick_ms")) / 1000)
    except multiprocessing.TimeoutError:
        return None


def handle_game_end(client, _, websocket):
    assert client.state == ClientState.InGame, (f"Game can only be ended in in game state! State right now is: "
                                                f"{client.state}")
    client.context = ClientContext()
    client.state = ClientState.Idle
    websocket.send(json.dumps({"eventType": "endAck", "data": {}}))


_EVENT_HANDLERS = {
    "authAck": handle_auth_ack,
    "startGame": handle_game_start,
    "gameTick": handle_game_tick,
    "endGame": handle_game_end
}


def connect_websocket(url: str, port: int):
    client = Client()
    with connect(f"ws://{url}:{port}") as websocket:
        client.state = ClientState.Unauthorized
        auth_msg = json.dumps({"eventType": "auth", "data": {"token": "myToken"}})
        websocket.send(auth_msg)
        while True:
            print("Waiting for message...")
            raw_message = websocket.recv()
            message = json.loads(raw_message)
            print(f"Received: {message}")
            handler = _EVENT_HANDLERS.get(message["eventType"], None)
            if handler is not None:
                _EVENT_HANDLERS[message["eventType"]](client, message["data"], websocket)
