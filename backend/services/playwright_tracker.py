"""Enhanced monitoring for Playwright scripts with structured event logging."""
import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
import json

class EventType(str, Enum):
    NAVIGATION = "navigation"
    CLICK = "click"
    INPUT = "input"
    CONSOLE = "console"
    NETWORK = "network"
    ERROR = "error"

@dataclass
class Event:
    """Represents a single monitored event."""
    type: EventType
    timestamp: str
    data: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the event to a dictionary for serialization."""
        return {
            "type": self.type.value,
            "timestamp": self.timestamp,
            "data": self.data
        }

class PlaywrightTracker:
    """Tracks and logs Playwright script execution events."""
    
    def __init__(self):
        self.events: List[Event] = []
        self.metadata: Dict[str, Any] = {
            "start_time": self._get_timestamp(),
            "status": "running"
        }
    
    def log_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Log a new event with the given type and data."""
        event = Event(
            type=event_type,
            timestamp=self._get_timestamp(),
            data=data
        )
        self.events.append(event)
    
    def get_events(self, event_type: Optional[EventType] = None) -> List[Dict[str, Any]]:
        """Get all events, optionally filtered by type."""
        events = self.events
        if event_type:
            events = [e for e in events if e.type == event_type]
        return [e.to_dict() for e in events]
    
    def get_execution_log(self) -> Dict[str, Any]:
        """Get a complete log of the execution."""
        return {
            "metadata": self.metadata,
            "events": [e.to_dict() for e in self.events]
        }
    
    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.datetime.utcnow().isoformat()
    
    def finalize(self, success: bool = True) -> Dict[str, Any]:
        """Finalize the tracking and return the complete log."""
        self.metadata.update({
            "end_time": self._get_timestamp(),
            "status": "completed" if success else "failed"
        })
        return self.get_execution_log()
