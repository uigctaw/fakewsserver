from typing import Iterable, Optional, Protocol, Union
import asyncio
import collections
import contextlib
import json

import websockets


LOCALHOST = 'localhost'


class InvalidArguments(Exception):
    pass


class Result:

    def __init__(self, messages_expected: bool):
        self.exception: Optional[Exception]
        if messages_expected:
            self.passed = False
            self.exception = AssertionError('Did not receive any messages.')
        else:
            self.passed = True
            self.exception = None


def _get_asserting_ws_connection_handler(communication, result):

    communication = list(reversed(communication))

    async def fn(ws_proto, path):
        i = 0  # apparently `enumerate` does not work with `async for`
        async for message in ws_proto:
            i += 1
            expected_input, answer = communication.pop()
            if expected_input == message:
                if isinstance(answer, (str, bytes)):
                    await ws_proto.send(answer)
                elif isinstance(answer, collections.abc.Iterable):
                    for piece_of_answer in answer:
                        await ws_proto.send(piece_of_answer)
            else:
                ith = {
                    1: '1st',
                    2: '2nd',
                    3: '3rd',
                }.get(i, f'{i}th')
                result.exception = AssertionError(
                    f'Failed {ith} step:\n'
                    f'Expected: "{expected_input}"\n'
                    + f'Got: "{message}"'
                )
                result.passed = False
                return
        if communication:
            result.passed = False
            result.exception = AssertionError(
                f'No more input messages. Expecting more: {communication}.'
            )
        else:
            result.passed = True

    return fn


Message = Union[str, bytes]
MessagePair = tuple[
        Optional[Message],
        Optional[Union[Iterable[Message], Message]],
        ]


@contextlib.asynccontextmanager
async def assert_communication(
        port: int,
        communication: Iterable[MessagePair],
        ):
    result = Result(messages_expected=bool(list(communication)))
    handler = _get_asserting_ws_connection_handler(communication, result)
    async with websockets.serve(  # type: ignore[attr-defined]
            handler, LOCALHOST, port):
        try:
            yield

        # If found mismatch between what was expected and received
        # the server will close connection before the client expects it.
        except (
                websockets
                .exceptions  # type: ignore[attr-defined]
                .ConnectionClosedOK
        ):
            pass
    if not result.passed:
        raise result.exception  # type: ignore[misc]


@contextlib.asynccontextmanager
async def respond_with(
        port: int,
        responses: Iterable[Message],
        ):
    handler = _get_dumb_responding_handler(responses)
    async with websockets.serve(  # type: ignore[attr-defined]
            handler, LOCALHOST, port):
        yield


def _get_dumb_responding_handler(responses):

    async def fn(ws_proto, path):
        async for message in ws_proto:
            for response in responses:
                await ws_proto.send(response)
    return fn


class AsyncClientProto(Protocol):

    async def send(self, str) -> None:
        pass

    async def recv(self) -> str:
        pass


class WriteProto(Protocol):

    def write(self, str) -> None:
        pass


async def write_communication(
        *,
        to_send: str,
        client: AsyncClientProto,
        file: WriteProto,
        timeout: Optional[float],
        num_responses: Optional[int],
        ):
    """Write communication as seen by the client.

    Parameters
    ----------
    to_send:
        A SINGLE message to send using the passed client.
    client:
        A thing with `send` and `recv` methods.
    file:
        A thing with 'write' method.
    timeout:
        How long to wait after each call to `recv` before giving up.
        Pass `None` to wait indefinitely.
    num_responses:
        How many messages to consume before terminating. Pass `None` to
        skip this limit.
    """

    if timeout is None and num_responses is None:
        raise InvalidArguments(
            f'Both cannot be `None`: {timeout = } and {num_responses = }'
        )

    comms = []
    comms.append(dict(type='send', data=to_send))
    await client.send(to_send)
    num_responses_received = 0
    while num_responses is None or num_responses_received < num_responses:
        try:
            received = await asyncio.wait_for(client.recv(), timeout=timeout)
        except asyncio.exceptions.TimeoutError:
            break
        comms.append(dict(type='receive', data=received))
        num_responses_received += 1
    serialized = json.dumps(comms)
    file.write(serialized)
