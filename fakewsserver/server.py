from typing import Optional
import collections
import contextlib

import websockets


class Result:

    def __init__(self, communication: list):
        self.communication = communication
        if communication:
            self.passed = False
            self.exception = AssertionError('Did not receive any messages.')
        else:
            self.passed = True
            self.exception = None


def get_ws_connection_handler(communication, result):

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


@contextlib.asynccontextmanager
async def assert_communication(port, communication):
    result = Result(list(communication))
    handler = get_ws_connection_handler(communication, result)
    async with websockets.serve(handler, '::1', port):
        try:
            yield
        except websockets.exceptions.ConnectionClosedOK:
            pass
    if not result.passed:
        raise result.exception
