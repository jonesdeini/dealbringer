import json
from pathlib import Path

from dealbringer.models import Offer

OFFERS = (
    Offer("apples", "Save on apples"),
    Offer("bread", "Save on bread", clipped=True),
    Offer("milk", "Save on milk"),
    Offer("expired", "Expired fixture", eligible=False),
)


class FakeStore:
    name = "fake"

    def __init__(self, data_dir: Path):
        self.path = data_dir / "fake-state.json"
        self.clipped = {offer.id for offer in OFFERS if offer.clipped}
        if self.path.exists():
            self.clipped.update(json.loads(self.path.read_text()))

    def discover(self) -> list[Offer]:
        return [Offer(o.id, o.title, o.id in self.clipped, o.eligible) for o in OFFERS]

    def clip(self, offer_id: str) -> None:
        self.clipped.add(offer_id)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(sorted(self.clipped)))
        temporary.chmod(0o600)
        temporary.replace(self.path)

    def verify(self, offer_id: str) -> bool:
        return offer_id in self.clipped
