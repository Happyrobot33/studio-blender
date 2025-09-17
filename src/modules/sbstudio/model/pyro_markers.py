from dataclasses import asdict, dataclass, field
from json import dumps, loads

import logging
from typing import Any, TypeVar

import bpy

__all__ = ("PyroMarkers", "PyroPayload")

C = TypeVar("C", bound="PyroMarkers")


@dataclass
class PyroPayload:
    """Properties of a pyro payload that we store and use."""

    name: str
    """Name of the pyro effect to trigger."""

    duration: float = 30
    """The overall duration of the pyro effect, in seconds."""

    prefire_time: float = 0
    """Time needed for the pyro payload to show up after ignition, in seconds."""

    def as_api_dict(self) -> dict[str, Any]:
        """Returns the pyro payload as a dictionary compatible with the Skybrush API."""
        return {
            "name": self.name,
            "duration": self.duration,
            "prefireTime": self.prefire_time
        }


@dataclass
class PyroMarker:
    """Descriptor of a single pyro trigger event
    on a specific drone's specific pyro channel.

    So far we assume that one channel can be used only once for pyro triggering."""

    channel: int
    """The frame number of the trigger event."""
    #frame: int

    pitch: int
    yaw: int
    roll: int

    payload: PyroPayload
    """Properties of the pyro payload attached."""

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        payload = data.get("payload")
        if payload is None:
            raise ValueError("payload field is missing")
        channel = data.get("channel")
        if channel is None:
            raise ValueError("channel field is missing")
        
        pitch = data.get("pitch", 0)
        yaw = data.get("yaw", 0)
        roll = data.get("roll", 0)

        return cls(payload=PyroPayload(**payload), channel=int(channel), pitch=int(pitch), yaw=int(yaw), roll=int(roll))

    def is_active_at_frame(self, frame: int, fps: float) -> bool:
        return False
        """Returns whether the pyro is active at the given frame"""
        if self.frame <= frame <= self.frame + self.payload.duration * fps:
            return True

        return False


@dataclass
class PyroMarkers:
    """Pyro marker list for a single drone.

    We assume that each pyro channel contains only a single pyro event."""

    markers: dict[int, PyroMarker] = field(default_factory=dict)
    """The list of pyro trigger markers, indexed by the pyro channel."""

    @classmethod
    def from_dict(cls, data: dict[int, PyroMarker]):
        """Creates a pyro markers object from its dictionary representation."""
        return cls(markers=data)

    @classmethod
    def from_str(cls, data: str):
        """Creates a pyro markers object from its string representation."""
        return cls(
            markers={
                int(channel): PyroMarker.from_dict(marker)
                for channel, marker in loads(data).items()
            }
            if data
            else {}
        )

    def as_dict(self) -> dict[int, Any]:
        """Returns the pyro trigger event markers stored for a single drone
        as a dictionary."""
        return {
            int(channel): asdict(marker)
            for channel, marker in sorted(self.markers.items())
        }

    def as_api_dict(self, fps: int, ndigits: int = 3) -> dict[str, Any]:
        """Returns the pyro trigger event markers stored for a single drone
        as a dictionary compatible with the Skybrush API."""
        items = sorted(self.markers.items())
        keys = sorted(self.markers.keys())

        #check if we dont have any markers
        if len(items) == 0:
            return {"version": 1, "events": [], "payloads": {}}

        #we are gonna do something EXTREMELY stupid here
        #essentially, we are going to act like we only have one entire pyro event
        #BUT in the payload key name, we will store a entire json string

        actual_events = [
            [round(frame / fps, ndigits=ndigits), self.markers[frame].channel]
            for frame in keys
        ]

        keys = keys[:1]
        events = [
            #frame is stored in the key
            [0, 1, str(1)]
        ]
        payloads = {
            str(1): {
                "name": str(actual_events),
                "prefireTime": 0.0,
                "duration": 30.0
            }
        }
        final = {"version": 1, "events": events, "payloads": payloads}
        print(final)

        return final

    def as_str(self) -> str:
        """Returns the JSON string representation of pyro trigger event markers
        stored for a single drone."""
        return dumps(self.as_dict())

    def shift_time_in_place(self: C, frame_delta: int) -> C:
        """Shifts all timestamps of the pyro markers in-place.

        Parameters:
            frame_delta: the frame delta to add to the frame of each event
        """
        return self
        for marker in self.markers.values():
            marker.frame += frame_delta
        return self
