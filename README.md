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
