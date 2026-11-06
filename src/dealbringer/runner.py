from datetime import UTC, datetime
from time import monotonic

from dealbringer.models import RunResult
from dealbringer.stores.base import Store, StoreError


def run(store: Store, *, dry_run: bool = False) -> RunResult:
    started = monotonic()
    result = RunResult(store.name, dry_run, datetime.now(UTC).isoformat())
    try:
        offers = store.discover()
    except (StoreError, TimeoutError):
        result.errors.append("Discovery failed or timed out; check adapter availability and retry.")
    else:
        result.found = len(offers)
        for offer in offers:
            if offer.clipped:
                result.previously_clipped += 1
            elif not offer.eligible or dry_run:
                result.skipped += 1
            else:
                try:
                    store.clip(offer.id)
                    if not store.verify(offer.id):
                        raise StoreError("Verification failed")
                except (StoreError, TimeoutError):
                    result.failed += 1
                    result.errors.append(
                        "Clipping failed or could not be verified; rerun to check current status."
                    )
                else:
                    result.newly_clipped += 1
    result.duration_seconds = round(monotonic() - started, 6)
    return result
