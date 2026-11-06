from dealbringer.stores.base import StoreError


def unavailable() -> None:
    raise StoreError(
        "Wegmans is unavailable: permitted integration and authorization "
        "must be established in Milestone 2. Use the offline fake store."
    )
