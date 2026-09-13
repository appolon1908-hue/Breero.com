from collections.abc import Mapping, Set
from dataclasses import dataclass
from typing import Generic, TypeVar

StateT = TypeVar("StateT")


class InvalidStateTransition(ValueError):
    def __init__(self, current: object, target: object) -> None:
        self.current = current
        self.target = target
        super().__init__(f"invalid state transition: {current!s} -> {target!s}")


@dataclass(frozen=True, slots=True)
class StateMachine(Generic[StateT]):
    transitions: Mapping[StateT, Set[StateT]]

    def can_transition(self, current: StateT, target: StateT) -> bool:
        return target in self.transitions.get(current, frozenset())

    def require_transition(self, current: StateT, target: StateT) -> None:
        if not self.can_transition(current, target):
            raise InvalidStateTransition(current, target)
