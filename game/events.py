"""The model/view seam.

Game logic (the *model*) mutates state and returns a list of `Event`s — plain
data describing what happened. A renderer (the *view*: the CLI today, a tap UI
later) turns events into words or widgets. No model code calls `print`.

An event is a `kind` plus a bag of fields. Keep kinds coarse and stable; the
renderer owns the prose so wording never leaks into the rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Event:
    kind: str
    data: dict = field(default_factory=dict)

    def __getattr__(self, name: str):
        # Convenience: event.cost instead of event.data["cost"].
        try:
            return self.data[name]
        except KeyError as e:
            raise AttributeError(name) from e


def ev(kind: str, **data) -> Event:
    return Event(kind, data)
