"""Helper module for a simple speckle object tree flattening."""

from collections.abc import Iterable
from specklepy.objects import Base


def flatten_base(base: Base, parent_type: str = None) -> Iterable[Base]:
    """Take a base and flatten it to an iterable of bases.

    Args:
        base: The base object to flatten.
        parent_type: The type of the parent object, if any.

    Yields:
        Base: A flattened base object.
    """
    if isinstance(base, Base):
        base["parent_type"] = parent_type

    if hasattr(base, "elements") and base.elements:
        try:
            for element in base.elements:
                # Recursively yield flattened elements of the child
                yield from flatten_base(element, base.speckle_type)
        except KeyError:
            pass
    else:
        yield base
