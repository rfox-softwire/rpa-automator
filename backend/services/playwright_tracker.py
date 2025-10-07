"""Enhanced monitoring for Playwright scripts with structured event logging."""
import datetime
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Union
import json
from functools import wraps

class EventType(str, Enum):
    NAVIGATION = "navigation"
    CLICK = "click"
    INPUT = "input"
    CONSOLE = "console"
    NETWORK = "network"
    ERROR = "error"
    PAGE_LOAD = "page_load"
    DIALOG = "dialog"
    DOWNLOAD = "download"
    CONSOLE_MESSAGE = "console_message"
    REQUEST = "request"
    RESPONSE = "response"
    REQUEST_FAILED = "request_failed"
    REQUEST_FINISHED = "request_finished"

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
        self.page_history: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {
            "start_time": self._get_timestamp(),
            "status": "running"
        }
    
    def _log_event(self, event_type: EventType, data: Dict[str, Any]) -> None:
        """Internal method to log events."""
        event = Event(
            type=event_type,
            timestamp=self._get_timestamp(),
            data=data
        )
        self.events.append(event)
        print(f"[Script Monitor] {event_type.upper()}: {json.dumps(data, default=str)}")
    
    def wrap_browser(self, browser):
        """Wrap a Playwright browser object to monitor its actions."""
        if not hasattr(browser, '_is_wrapped'):
            browser._is_wrapped = True
            
            # Store original methods
            original_new_context = browser.new_context
            
            # Wrap new_context to monitor page creation
            async def wrapped_new_context(**kwargs):
                context = await original_new_context(**kwargs)
                return self.wrap_context(context)
                
            browser.new_context = wrapped_new_context
            
        return browser
    
    def wrap_context(self, context):
        """Wrap a Playwright context to monitor its pages."""
        if not hasattr(context, '_is_wrapped'):
            context._is_wrapped = True
            
            # Store original methods
            original_new_page = context.new_page
            
            # Wrap new_page to monitor page interactions
            async def wrapped_new_page():
                page = await original_new_page()
                return self.wrap_page(page)
                
            context.new_page = wrapped_new_page
            
        return context
    
    def wrap_page(self, page):
        """Wrap a Playwright page to monitor its actions."""
        if not hasattr(page, '_is_wrapped'):
            page._is_wrapped = True
            
            # Store original methods
            original_click = page.click
            original_fill = page.fill
            original_goto = page.goto
            
            # Add page to history when created
            async def log_page_info():
                try:
                    url = page.url
                    title = await page.title()
                    self.page_history.append({
                        'url': url,
                        'title': title,
                        'timestamp': self._get_timestamp(),
                        'html': await page.content()
                    })
                except Exception as e:
                    print(f"[Script Monitor] Error capturing page info: {e}")
            
            # Run the page info capture in the background
            import asyncio
            asyncio.create_task(log_page_info())
            
            # Wrap methods
            async def wrapped_click(selector, **kwargs):
                self._log_event(EventType.CLICK, {
                    "selector": selector,
                    "kwargs": kwargs
                })
                return await original_click(selector, **kwargs)
                
            async def wrapped_fill(selector, value, **kwargs):
                self._log_event(EventType.INPUT, {
                    "selector": selector,
                    "value": value,
                    "kwargs": kwargs
                })
                return await original_fill(selector, value, **kwargs)
                
            async def wrapped_goto(url, **kwargs):
                self._log_event(EventType.NAVIGATION, {
                    "url": url,
                    "kwargs": kwargs
                })
                return await original_goto(url, **kwargs)
            
            # Replace methods
            page.click = wrapped_click
            page.fill = wrapped_fill
            page.goto = wrapped_goto
            
        return page
    
    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.datetime.utcnow().isoformat()
    
    def finalize(self, success: bool = True) -> Dict[str, Any]:
        """Finalize the tracking and return the complete log."""
        self.metadata.update({
            "end_time": self._get_timestamp(),
            "status": "completed" if success else "failed",
            "duration_seconds": (
                datetime.datetime.utcnow() - 
                datetime.datetime.fromisoformat(self.metadata["start_time"])
            ).total_seconds()
        })
        return self.get_execution_log()
    
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
            "events": [e.to_dict() for e in self.events],
            "page_history": self.page_history
        }
