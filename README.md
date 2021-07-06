# Fake Websocket Server

Fake in the sense that it's actually a working server (created using
`websockets` library) but one that that exists briefly to allow
integration testing.


# Installation

pip install fakewsserver
 

# Usage

## One message sent, one received, everything is as expected

```python
from fakewsserver import assert_communication

async with assert_communication(
        port=12345,
        communication=[('hello', 'there')],
        ):
    async with websockets.connect('ws://localhost:12345') as client:
        await client.send('hello')
        response = await client.recv()

assert response == 'there'
```

## Expected communication pattern does not match

```python
communication = [
    ('hello', 'there'),
    ('general', 'Kenobi'),
]

async with assert_communication(
        port=12345,
        communication=communication,
        ):
    async with websockets.connect('ws://localhost:12345') as client:
        await client.send('hello')
        response = await client.recv()
        assert response == 'there'
        await client.send('admiral')
        await client.recv()
```

And there's a feedback what went wrong:
```
    AssertionError: Failed 2nd step:
    Expected: "general"
    Got: "admiral"
```

## Utilities

When working with APIs it might be convenient to capture real messages
to write tests against them. Here's a simple example (using the fake server;
in real life we would connect to a real websocket server).

```python
from fakewsserver import respond_with, write_communication

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
```
