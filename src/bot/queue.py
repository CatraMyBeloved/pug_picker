from dataclasses import dataclass


@dataclass
class Queue:
    is_active: str = 'inactive'
    tank: set[str] = None
    dps: set[str] = None
    support: set[str] = None

    def __post_init__(self):
        self.tank = set() if self.tank is None else self.tank
        self.dps = set() if self.dps is None else self.dps
        self.support = set() if self.support is None else self.support
        return
