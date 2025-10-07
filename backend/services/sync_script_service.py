import os
import subprocess
import sys
import importlib.util
import importlib.metadata
import re
import json
import traceback
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

from models.base import ScriptResult, ScriptError

class SyncScriptService:
    def __init__(self, scripts_dir: str = "data/scripts"):
        """Initialize the SyncScriptService with the directory to store scripts.
        
        Args:
            scripts_dir: Directory where scripts will be stored. Will be created if it doesn't exist.
        """
        self.scripts_dir = Path(scripts_dir)
        try:
            self.scripts_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(
                f"Failed to create scripts directory '{scripts_dir}': {str(e)}\n"
                "Please check if you have the necessary permissions or specify a different directory."
            )

    def _ensure_playwright_browsers(self) -> bool:
        """Ensure Playwright browsers are installed."""
        try:
            # Check if playwright is installed
            try:
                import playwright
            except ImportError:
                return True  # If playwright isn't installed, the package installation will handle it
                
            # Try to import the sync API to check browser installation
            from playwright.sync_api import sync_playwright
            
            try:
                # This will raise an error if browsers aren't installed
                with sync_playwright() as p:
                    p.chromium.launch(headless=True).close()
                return True
            except Exception as e:
                print("Playwright browsers not found, installing...")
                # Install browsers
                import subprocess
                subprocess.check_call([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"])
                return True
                
        except Exception as e:
            print(f"Error ensuring Playwright browsers are installed: {e}")
            return False

    def install_package(self, package_name: str) -> bool:
        """Install a Python package using pip."""
        try:
            print(f"Installing package: {package_name}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            return True
        except subprocess.CalledProcessError as e:
            print(f"Failed to install package {package_name}: {e}")
            return False

    def get_imports_from_script(self, script_path: str) -> List[str]:
        """Extract all imported packages from a Python script."""
        with open(script_path, 'r', encoding='utf-8') as f:
            node = ast.parse(f.read())
        
        imports = set()
        for item in ast.walk(node):
            if isinstance(item, ast.Import):
                for name in item.names:
                    imports.add(name.name.split('.')[0])
            elif isinstance(item, ast.ImportFrom):
                if item.module:
                    imports.add(item.module.split('.')[0])
        
        return list(imports)

    def ensure_packages_installed(self, script_path: str) -> bool:
        """Ensure all required packages are installed."""
        try:
            imports = self.get_imports_from_script(script_path)
            if not imports:
                return True
                
            # Get installed packages
            installed_packages = {pkg.metadata['Name'].lower() for pkg in importlib.metadata.distributions()}
            
            # Check for missing packages
            missing = [pkg for pkg in imports if pkg.lower() not in installed_packages]
            
            if not missing:
                return True
                
            print(f"Installing missing packages: {', '.join(missing)}")
            for pkg in missing:
                if not self.install_package(pkg):
                    print(f"Failed to install package: {pkg}")
                    return False
                    
            return True
            
        except Exception as e:
            print(f"Error ensuring packages are installed: {e}")
            return False

    def run_script(self, script_path: str) -> ScriptResult:
        """
        Execute a Python script synchronously and return the result with detailed error information.
        First ensures all required packages are installed.
        """
        script_content = ""
        
        try:
            # Ensure the script exists
            if not os.path.exists(script_path):
                return ScriptResult(
                    success=False,
                    error_type="FileNotFoundError",
                    error_details={"script_path": script_path, "message": "Script file not found"}
                )
            
            # Read the script content
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Check if this is a Playwright script and ensure browsers are installed
            if 'playwright' in script_content.lower() and not self._ensure_playwright_browsers():
                return ScriptResult(
                    success=False,
                    error_type="BrowserInstallationError",
                    error_details={"message": "Failed to install required Playwright browsers"}
                )
            
            # Ensure required packages are installed
            if not self.ensure_packages_installed(script_path):
                return ScriptResult(
                    success=False,
                    error_type="DependencyError",
                    error_details={"message": "Failed to install required packages"},
                    script_content=script_content
                )
            
            # Execute the script
            print(f"[SyncScriptService] Starting script execution: {script_path}")
            
            # Use subprocess to run the script in a separate process
            process = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            try:
                # Wait for the process to complete with a timeout
                stdout, stderr = process.communicate(timeout=300)  # 5 minutes timeout
                returncode = process.returncode
                
            except subprocess.TimeoutExpired:
                process.kill()
                return ScriptResult(
                    success=False,
                    error_type="TimeoutError",
                    error_details={"message": "Script execution timed out after 300 seconds"},
                    script_content=script_content
                )
            
            # Process the results
            if returncode == 0:
                return ScriptResult(
                    success=True,
                    output=stdout,
                    stderr=stderr,
                    script_content=script_content
                )
            else:
                # Try to extract error information
                error_type = "RuntimeError"
                error_message = stderr.strip() or "Script execution failed"
                
                # Try to extract more specific error information
                if stderr:  # Only try to match if there's stderr output
                    error_match = re.search(r'^(\w+):\s*(.*?)(?:\n|$)', stderr, re.MULTILINE)
                    if error_match:
                        error_type = error_match.group(1)
                        error_message = error_match.group(2).strip()
                
                return ScriptResult(
                    success=False,
                    output=stdout,
                    stderr=stderr,
                    script_content=script_content,
                    error_type=error_type,
                    error_details={"message": error_message}
                )
                
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            error_traceback = traceback.format_exc()
            
            return ScriptResult(
                success=False,
                error_type=error_type,
                error_details={
                    "message": error_message,
                    "traceback": error_traceback
                },
                script_content=script_content,
                stderr=f"{error_type}: {error_message}\n\n{error_traceback}"
            )
    
    def save_script(self, content: str, script_id: str = None) -> tuple[str, str]:
        """Save a script to a file and return its path and ID."""
        if script_id is None:
            import uuid
            script_id = str(uuid.uuid4())
            
        script_filename = f"script_{script_id}.py"
        script_path = self.scripts_dir / script_filename
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return str(script_path), script_id
