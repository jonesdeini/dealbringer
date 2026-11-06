from typing import Protocol

from dealbringer.models import Offer


class StoreError(Exception):
    """An expected adapter failure; messages must contain no private data."""


class Store(Protocol):
    name: str

    def discover(self) -> list[Offer]: ...

    def clip(self, offer_id: str) -> None: ...

    def verify(self, offer_id: str) -> bool: ...
