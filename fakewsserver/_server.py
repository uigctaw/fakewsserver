from collections.abc import Sequence
from typing import AsyncGenerator, Optional, Union
import collections
import contextlib

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
        Optional[Union[Sequence[Message], Message]],
        ]


@contextlib.asynccontextmanager
async def assert_communication(
        port: int,
        communication: Sequence[MessagePair],
        ) -> AsyncGenerator:
    """

    Parameters
    ----------
    port:
        localhost` port to which the server connects.
    communication:
        Sequence of 2-tuples of messages that are expected
        to occur.

        The 1st tuple element is a message that is expected
        to be delivered when the server reads the connection.
        If it's `None`, nothing is expected.

        The 2nd tuple element contains a single or sequence
        of messages that the server will respond with (or
        unilaterally send if no incoming message is expected).

    Raises
    ------
    AssertionError:
        When expected exchange of messages between the server
        and clients is not as expected.
    """
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
