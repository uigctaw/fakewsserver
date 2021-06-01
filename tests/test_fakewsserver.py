import pytest
import websockets

from fakewsserver import assert_communication


atest = pytest.mark.asyncio


@atest
async def test_connect_do_nothing_and_return():
   
    async with assert_communication(
            port=1234, communication=()) as result:
        pass

    assert result.passed


@atest
async def test_single_response_succeeds():

    communication =  [
        ('hello', 'there'),
    ]

    async with assert_communication(
            port=12345,
            communication=communication,
            ) as result:
        async with websockets.connect('ws://[::1]:12345') as client:
            await client.send('hello')
            response = await client.recv()
         
    assert result.passed
    assert response == 'there'


@atest
async def test_2_out_1_response_succeeds():

    communication =  [
        ('hello', None),
        ('there', 'General Kenobi'),
    ]

    async with assert_communication(
            port=12345,
            communication=communication,
            ) as result:
        async with websockets.connect('ws://[::1]:12345') as client:
            await client.send('hello')
            await client.send('there')
            response = await client.recv()
         
    assert result.passed
    assert response == 'General Kenobi'


@atest
async def test_2_messages_out_1_response_in_succeed():

    communication =  [
        ('hello', None),
        ('there', 'General Kenobi'),
    ]

    async with assert_communication(
            port=12345,
            communication=communication,
            ) as result:
        async with websockets.connect('ws://[::1]:12345') as client:
            await client.send('hello')
            await client.send('there')
            response = await client.recv()
         
    assert response == 'General Kenobi'


@atest
async def test_expected_message_is_incorrect_gives_an_error():

    communication =  [
        ('hello', 'there'),
    ]

    with pytest.raises(AssertionError):
        async with assert_communication(
                port=12345,
                communication=communication,
                ) as result:
            async with websockets.connect('ws://[::1]:12345') as client:
                await client.send('hi')
                response = await client.recv()
