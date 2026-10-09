"""Per-storage-path daemon worker pools with backpressure and a watchdog.

External producers use a bounded queue. Recursive shard discovery can add
children without blocking workers on their own queue (which would deadlock).
Callbacks are serialized per pool; work and filesystem calls run concurrently.
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque
from dataclasses import dataclass

WORKERS = max(1, int(os.environ.get("GALAXY_CHECK_WORKERS", "8")))
QUEUE_SIZE = max(1, int(os.environ.get("GALAXY_CHECK_QUEUE", "2000")))


@dataclass
class _Task:
    item: object
    started: float
    abandoned: bool = False


class WorkerPool:
    """Run work(item, publish), then consume(item, result) under a lock.

    consume returns any recursively discovered children. publish(callback)
    commits incremental findings only while a task is still live. A watchdog
    can abandon a blocked task and start a replacement daemon worker.
    """

    def __init__(self, label, work, consume, *, timeout=None, on_timeout=None,
                 heartbeat=30):
        self.label = label
        self.work = work
        self.consume = consume
        self.timeout = timeout
        self.on_timeout = on_timeout
        self.heartbeat = max(0.01, heartbeat)
        self.condition = threading.Condition(threading.RLock())
        self.queue = deque()
        self.active = {}
        self.pending = 0
        self.completed = 0
        self.errors = []
        self.closed = False
        self.stop = threading.Event()
        self.started = time.monotonic()
        for _ in range(WORKERS):
            self._start_worker()
        self.monitor = threading.Thread(target=self._monitor, daemon=True)
        self.monitor.start()

    def _start_worker(self):
        threading.Thread(target=self._worker, daemon=True).start()

    def submit(self, item):
        with self.condition:
            while len(self.queue) >= QUEUE_SIZE and not self.errors:
                self.condition.wait()
            self._raise_error()
            self.queue.append(item)
            self.pending += 1
            self.condition.notify_all()

    def _raise_error(self):
        if self.errors:
            raise self.errors[0]

    def _worker(self):
        while True:
            with self.condition:
                while not self.queue and not self.closed:
                    self.condition.wait()
                if self.closed:
                    return
                task = _Task(self.queue.popleft(), time.monotonic())
                self.active[id(task)] = task
                self.condition.notify_all()

            def publish(callback):
                with self.condition:
                    if not task.abandoned and not self.closed:
                        callback()

            try:
                result = self.work(task.item, publish)
                with self.condition:
                    if not task.abandoned and not self.closed:
                        children = self.consume(task.item, result)
                        if children is not None:
                            for child in children:
                                self.queue.append(child)
                                self.pending += 1
            except Exception as exc:
                with self.condition:
                    if not task.abandoned:
                        self.errors.append(exc)
            finally:
                with self.condition:
                    self.active.pop(id(task), None)
                    if not task.abandoned:
                        self.pending -= 1
                        self.completed += 1
                    self.condition.notify_all()
            if task.abandoned:
                return

    def _monitor(self):
        last_heartbeat = time.monotonic()
        while not self.stop.wait(0.1):
            now = time.monotonic()
            with self.condition:
                if self.timeout is not None:
                    for key, task in list(self.active.items()):
                        limit = self.timeout(task.item) if callable(self.timeout) else self.timeout
                        if limit is None or now - task.started < limit:
                            continue
                        task.abandoned = True
                        self.active.pop(key)
                        self.pending -= 1
                        try:
                            if self.on_timeout:
                                self.on_timeout(task.item)
                        except Exception as exc:
                            self.errors.append(exc)
                        self._start_worker()
                        self.condition.notify_all()
                if now - last_heartbeat >= self.heartbeat:
                    last_heartbeat = now
                    print(
                        f"    [{self.label}] heartbeat: {self.completed} completed, "
                        f"{len(self.queue)} queued, {len(self.active)} active, "
                        f"{now - self.started:.1f}s elapsed", flush=True,
                    )

    def wait(self):
        with self.condition:
            while self.pending and not self.errors:
                self.condition.wait()
            self._raise_error()

    def close(self):
        with self.condition:
            self.closed = True
            self.condition.notify_all()
        self.stop.set()
        self.monitor.join()


class LineWriter:
    """Lazy, incremental output shared safely by multiple storage pools."""

    def __init__(self, path, header=""):
        self.path = path
        self.header = header
        self.lock = threading.Lock()
        self.fh = None

    def write(self, line):
        with self.lock:
            if self.fh is None:
                self.fh = self.path.open("w")
                self.fh.write(self.header)
            self.fh.write(line)
            self.fh.flush()

    def close(self):
        with self.lock:
            if self.fh is not None:
                self.fh.close()
