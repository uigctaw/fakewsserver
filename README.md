# Fake Websocket Server

Fake in the sense that it's actually a working server (created using
`websockets` library) but one that that exists briefly to allow
integration testing.


# Installation

pip install fakewsserver
 

# Usage

```python
from fakewsserver import assert_communication
async with assert_communication(
        port=12345,
        communication=communication,
        ):
```
