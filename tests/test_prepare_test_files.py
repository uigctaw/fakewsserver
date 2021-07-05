from io import StringIO
from unittest import mock
import json
import pytest
import websockets

from fakewsserver import (
        respond_with,
        write_communication,
        AsyncClientProto,
        InvalidArguments,
        WriteProto,
        )

atest = pytest.mark.asyncio


@atest
async def test_documentation_test_case():

    send = 'Hello there'
    receive = ['General', 'Kenobi']

    file = StringIO()
    async with respond_with(port=12345, responses=receive):
        async with websockets.connect('ws://localhost:12345') as client:
            await write_communication(
                to_send=send,
                client=client,
                file=file,
                timeout=None,
                num_responses=len(receive),
            )

    file.seek(0)
    data_raw = file.read()
    data = json.loads(data_raw)

    assert data == [
        dict(
            type='send',
            data='Hello there',
        ),
        dict(
            type='receive',
            data='General',
        ),
        dict(
            type='receive',
            data='Kenobi',
        ),
    ]


@atest
async def test_persisting_single_msg_out_and_few_msgs_in():

    send = 'Hello there'
    receive = ['General', 'Kenobi']

    for timeout, num_responses in [
        (0.001, None),
        (None, 2),
        (5, 2),
    ]:
        file = StringIO()
        async with respond_with(port=12345, responses=receive):
            async with websockets.connect('ws://localhost:12345') as client:
                await write_communication(
                    to_send=send,
                    client=client,
                    file=file,
                    timeout=timeout,
                    num_responses=num_responses,
                )
        file.seek(0)
        data_raw = file.read()
        data = json.loads(data_raw)
        assert data == [
            dict(
                type='send',
                data='Hello there',
            ),
            dict(
                type='receive',
                data='General',
            ),
            dict(
                type='receive',
                data='Kenobi',
            ),
        ]


@atest
async def test_either_num_respones_or_timeout_is_required():

    with pytest.raises(InvalidArguments):
        await write_communication(
            to_send='does not matter',
            client=mock.Mock(spec=AsyncClientProto),
            file=mock.Mock(spec=WriteProto),
            timeout=None,
            num_responses=None,
        )
