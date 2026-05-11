# Shared mutable state — single asyncio process, no threading concerns.
_fault_active: bool = False


def is_fault_active() -> bool:
    return _fault_active


def set_fault(active: bool) -> None:
    global _fault_active
    _fault_active = active
