import asyncio
import logging


log = logging.getLogger(__name__)

_connection: dict[str, asyncio.Queue] = {}
_finished_results: dict[str, dict] = {}


def register_connection(request_id: str) -> asyncio.Queue:
    """called when front opens SSE."""
    queue: asyncio.Queue = asyncio.Queue()
    _connection[request_id] = queue
    return queue


def unregister_connection(request_id: str):
    """called when front closes SSE."""
    log.info("Deleting connection for: %s", request_id)
    _connection.pop(request_id, None)
    _finished_results.pop(request_id, None)  # можно удалять, чтобы не росло


async def send_to_connection(request_id: str, message: dict) -> bool:
    """called from webhook. puts the message in a cabinet."""
    queue = _connection.get(request_id)
    if queue:
        await queue.put(message)
        return True
    else:  # if front hasnt yet connected, save the result
        _finished_results[request_id] = message
        return False  # front hasnt opened SSE or has already closed it


def get_finished_result(request_id: str):
    """if front was late"""
    return _finished_results.get(request_id)
