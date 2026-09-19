"""Supplement the unmodified SDK ask/parser with a durable pre-parser journal.

Does not start a run. Use only inside an independently authorised, preregistered
official panel. Keeps prompts and exact returned text, not credential headers.
"""
import contextlib
import hashlib
import json
import os
from pathlib import Path
from unittest.mock import patch


@contextlib.contextmanager
def capture(panel_module, destination):
    path = Path(destination)
    # Never append to or overwrite a prior experiment's journal.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    original = panel_module.chat
    sequence = 0
    def write(row):
        payload = (json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n").encode()
        remaining = memoryview(payload)
        while remaining:
            written = os.write(fd, remaining)
            if written <= 0:
                raise OSError("raw journal write made no progress")
            remaining = remaining[written:]
        os.fsync(fd)

    def captured_chat(endpoint, prompt):
        nonlocal sequence
        sequence += 1
        call = sequence
        write({"kind": "reader-request-before-transport", "call": call,
               "reader": endpoint["name"], "model": endpoint["model"],
               "prompt": prompt, "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest()})
        try:
            returned = original(endpoint, prompt)
        except BaseException as exc:
            write({"kind": "reader-transport-exception", "call": call,
                   "exception_type": type(exc).__name__})
            raise
        raw_text, truncated = returned
        write({"kind": "reader-response-before-parser", "call": call,
               "raw_text": raw_text, "truncated": truncated,
               "raw_text_sha256": hashlib.sha256(raw_text.encode()).hexdigest()})
        return returned  # Same object/bytes; no parsing, retries or answer changes.

    try:
        with patch.object(panel_module, "chat", captured_chat):
            yield
    finally:
        os.close(fd)
