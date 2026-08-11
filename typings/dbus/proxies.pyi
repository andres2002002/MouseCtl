from __future__ import annotations

from typing import Any

class ProxyObject:
    def __getattr__(self, name: str) -> Any: ...
