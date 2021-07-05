import pytest
import websockets

from fakewsserver import assert_communication

atest = pytest.mark.asyncio


@atest
async def test_connect_do_nothing_and_return():

    async with assert_communication(port=1234, communication=()):
        pass


@atest
async def test_single_response_succeeds():
    async with assert_communication(
            port=12345,
            communication=[('hello', 'there')],
            ):
        async with websockets.connect('ws://localhost:12345') as client:
            await client.send('hello')
            response = await client.recv()

    assert response == 'there'


@atest
async def test_2_out_1_response_succeeds():
    # Also bytes are fine

    communication = [
        ('hello', None),
        (b'there', b'General Kenobi'),
    ]

    async with assert_communication(
            port=12345,
            communication=communication,
            ):
        async with websockets.connect('ws://localhost:12345') as client:
            await client.send('hello')
            await client.send(b'there')
            response = await client.recv()

    assert response == b'General Kenobi'


@atest
async def test_2_messages_out_1_response_in_succeed():

    communication = [
        ('hello', None),
        ('there', 'General Kenobi'),
    ]

    async with assert_communication(
            port=12345,
            communication=communication,
            ):
        async with websockets.connect('ws://localhost:12345') as client:
            await client.send('hello')
            await client.send('there')
            response = await client.recv()

    assert response == 'General Kenobi'


@atest
async def test_expected_message_is_incorrect_and_results_in_an_error():

    communication = [
        ('hello', 'there'),
    ]

    with pytest.raises(AssertionError):
        async with assert_communication(
                port=12345,
                communication=communication,
                ):
            async with websockets.connect('ws://localhost:12345') as client:
                await client.send('hi')
                await client.recv()


@atest
async def test_more_messages_expected_than_sent_causes_error():

    communication = [
        ('hello', 'there'),
        ('General', 'Kenobi'),
    ]

    with pytest.raises(AssertionError):
        async with assert_communication(
                port=12345,
                communication=communication,
                ):
            async with websockets.connect('ws://localhost:12345') as client:
                await client.send('hello')
                await client.recv()


@atest
async def test_multiple_responses_for_a_single_message():

    communication = [
        ('hello', None),
        ('there', ['General', b'Kenobi']),
    ]

    async with assert_communication(
            port=12345,
            communication=communication,
            ):
        async with websockets.connect('ws://localhost:12345') as client:
            await client.send('hello')
            await client.send('there')
            assert await client.recv() == 'General'
            assert await client.recv() == b'Kenobi'
