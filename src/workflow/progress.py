import threading

_store: dict[str, str] = {}
_lock = threading.Lock()


def set_stage(task_id: str, stage: str) -> None:
    with _lock:
        _store[task_id] = stage


def get_stage(task_id: str) -> str | None:
    with _lock:
        return _store.get(task_id)


def clear_stage(task_id: str) -> None:
    with _lock:
        _store.pop(task_id, None)
