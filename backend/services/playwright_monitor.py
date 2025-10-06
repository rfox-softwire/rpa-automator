from typing import Dict, List, Optional, Any
from playwright.sync_api import sync_playwright, Page, BrowserContext
import json
import os

class PlaywrightMonitor:
    def __init__(self):
        self.page_history: List[Dict[str, str]] = []
        self.current_page: Optional[Page] = None
        self.context: Optional[BrowserContext] = None
        self.playwright = None
        self.browser = None
        
    def start(self):
        """Initialize Playwright and return a new context with monitoring"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.context = self.browser.new_context()
        
        # Track page navigation
        self.context.on("page", self._on_page)
        return self.context
        
    def _on_page(self, page: Page):
        """Handle new page events"""
        self.current_page = page
        
        # Log page access
        def log_navigation(request):
            if request.is_navigation_request():
                self._log_page_access(page)
        
        # Track page navigation and content
        page.on("requestfinished", log_navigation)
        
    def _log_page_access(self, page: Page):
        """Log page access and capture HTML"""
        try:
            url = page.url
            title = page.title()
            html = page.content()
            
            self.page_history.append({
                "url": url,
                "title": title,
                "timestamp": str(datetime.datetime.utcnow()),
                "html": html if len(html) < 10000 else html[:10000] + "... [truncated]"
            })
            
        except Exception as e:
            print(f"Error capturing page content: {str(e)}")
    
    def get_page_history(self) -> List[Dict[str, str]]:
        """Get the history of page accesses"""
        return self.page_history
        
    def get_current_page_html(self) -> Optional[str]:
        """Get HTML of the current page"""
        if not self.current_page:
            return None
        try:
            return self.current_page.content()
        except:
            return None
    
    def stop(self):
        """Clean up resources"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

# Global monitor instance
monitor = PlaywrightMonitor()

def get_playwright_context():
    """Get a monitored Playwright context"""
    return monitor.start()

def get_page_history() -> List[Dict[str, str]]:
    """Get the history of page accesses"""
    return monitor.get_page_history()

def get_current_page_html() -> Optional[str]:
    """Get HTML of the current page"""
    return monitor.get_current_page_html()

def stop_monitor():
    """Stop the monitor and clean up"""
    monitor.stop()

def monitor_playwright():
    """
    Context manager to monitor Playwright scripts.
    
    Example usage:
        with monitor_playwright():
            # Your Playwright code here
            pass
    """
    context = get_playwright_context()
    try:
        yield context
    finally:
        if context:
            context.close()
        stop_monitor()
