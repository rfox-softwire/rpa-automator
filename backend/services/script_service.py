import os
import subprocess
import sys
import importlib.util
import importlib.metadata
import asyncio
import re
import aiohttp
import ast
import json
import requests
import traceback
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from urllib.parse import urlparse

from models.base import ScriptResult, ScriptError

import warnings

class ScriptService:
    """Deprecated: Use SyncScriptService instead.
    
    This class is kept for backward compatibility but will be removed in a future version.
    Please update your code to use SyncScriptService from sync_script_service.py
    """
    
    def __init__(self, scripts_dir: str = "data/scripts"):
        """Initialize the ScriptService with the directory to store scripts.
        
        .. deprecated:: 1.0.0
           Use :class:`SyncScriptService` instead.
        
        Args:
            scripts_dir: Directory where scripts will be stored. Will be created if it doesn't exist.
        """
        warnings.warn(
            'ScriptService is deprecated and will be removed in a future version. '
            'Use SyncScriptService instead.',
            DeprecationWarning,
            stacklevel=2
        )
        self.scripts_dir = Path(scripts_dir)
        try:
            self.scripts_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(
                f"Failed to create scripts directory '{scripts_dir}': {str(e)}\n"
                "Please check if you have the necessary permissions or specify a different directory."
            )
    
    async def validate_urls(self, script_content: str) -> Dict[str, Any]:
        """Validate all URLs in a script to ensure they are accessible."""
        try:
            # Extract URLs from script content using regex
            url_pattern = r'https?://(?:[\w-]+\.)+[a-z]{2,}(?::\d+)?(?:/[^\s\"\'<>\[\]{}()]*)?'
            urls = re.findall(url_pattern, script_content, re.IGNORECASE)
            
            # Remove duplicates while preserving order
            unique_urls = []
            seen = set()
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            
            if not unique_urls:
                return {
                    "accessible": True,
                    "inaccessible_urls": [],
                    "all_urls": []
                }
            
            # Check accessibility of each URL
            inaccessible_urls = []
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async def check_url(url):
                try:
                    # First try with a simple GET request with a short timeout
                    try:
                        connector = aiohttp.TCPConnector(ssl=False)  # Disable SSL verification
                        timeout = aiohttp.ClientTimeout(total=10)  # 10 seconds timeout
                        
                        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                            try:
                                # Try with a simple HEAD request first
                                async with session.head(url, headers=headers, allow_redirects=True, ssl=False) as response:
                                    if response.status < 400:
                                        return None
                                    # If HEAD fails with 403/405, try with GET
                                    if response.status in (403, 405):
                                        raise Exception(f'HEAD not allowed (status {response.status}), trying GET')
                                    return f"{url} (HTTP {response.status})"
                                    
                            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                                # If HEAD fails, try with GET
                                if isinstance(e, (aiohttp.ClientConnectorError, aiohttp.ServerTimeoutError)):
                                    # For connection errors, try with GET directly
                                    async with session.get(url, headers=headers, allow_redirects=True, ssl=False) as response:
                                        if response.status >= 400:
                                            return f"{url} (HTTP {response.status})"
                                        return None
                                raise
                                
                    except Exception as e:
                        # If we get here, both HEAD and GET failed
                        error_msg = str(e).split('\n')[0]  # Just get the first line of the error
                        return f"{url} (Error: {error_msg})"
                        
                except Exception as e:
                    # Catch any other unexpected errors
                    return f"{url} (Unexpected error: {str(e)})"
            
            # Check all URLs with a semaphore to limit concurrency
            sem = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
            
            async def check_url_with_semaphore(url):
                async with sem:
                    return await check_url(url)
            
            # Process URLs in batches to avoid overwhelming the system
            batch_size = 10
            all_results = []
            
            for i in range(0, len(unique_urls), batch_size):
                batch = unique_urls[i:i + batch_size]
                batch_results = await asyncio.gather(
                    *(check_url_with_semaphore(url) for url in batch),
                    return_exceptions=True
                )
                all_results.extend(batch_results)
            
            # Process results
            inaccessible_urls = [url for url in all_results if url is not None]
            
            result = {
                "accessible": len(inaccessible_urls) == 0,
                "inaccessible_urls": inaccessible_urls,
                "all_urls": unique_urls
            }
            
            print(f"URL validation results: {json.dumps(result, indent=2)}")
            return result
            
        except Exception as e:
            import traceback
            print(f"Error in validate_urls: {str(e)}\n{traceback.format_exc()}")
            raise
    
    def install_package(self, package_name: str) -> bool:
        """Install a Python package using pip."""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            return True
        except subprocess.CalledProcessError:
            return False
    
    def get_imports_from_script(self, script_path: str) -> List[str]:
        """Extract all imported packages from a Python script."""
        # List of built-in modules that should not be installed
        builtin_modules = set([
            # Standard library modules
            'os', 're', 'sys', 'json', 'time', 'datetime', 'random', 'math',
            'subprocess', 'shutil', 'pathlib', 'typing', 'collections', 'itertools',
            'functools', 'argparse', 'logging', 'urllib', 'http', 'ssl', 'socket',
            'hashlib', 'base64', 'csv', 'io', 'tempfile', 'threading', 'multiprocessing',
            'asyncio', 'contextlib', 'enum', 'abc', 'copy', 'pprint', 'pickle', 'sqlite3',
            'zipfile', 'tarfile', 'gzip', 'bz2', 'lzma', 'zlib', 'statistics', 'decimal',
            'fractions', 'random', 'secrets', 're', 'string', 'unicodedata', 'textwrap',
            'struct', 'codecs', 'datetime', 'calendar', 'collections', 'heapq', 'bisect',
            'array', 'weakref', 'types', 'copy', 'pprint', 'reprlib', 'enum', 'graphlib',
            # Add any other built-in modules that might be imported
        ])
        
        imports = set()
        with open(script_path, 'r', encoding='utf-8') as f:
            try:
                tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            module_name = name.name.split('.')[0]
                            if module_name not in builtin_modules:
                                imports.add(module_name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            module_name = node.module.split('.')[0]
                            if module_name not in builtin_modules:
                                imports.add(module_name)
            except Exception as e:
                print(f"Error parsing script for imports: {e}")
                return []
        
        # Additional filtering for any remaining standard library modules
        stdlib = set(sys.builtin_module_names)
        return [pkg for pkg in imports if pkg not in stdlib and not pkg.startswith('_')]
    
    async def ensure_packages_installed(self, script_path: str) -> bool:
        """Ensure all required packages are installed."""
        try:
            imports = self.get_imports_from_script(script_path)
            if not imports:
                return True
                
            # Get installed packages using importlib.metadata
            installed_packages: Set[str] = set()
            for dist in importlib.metadata.distributions():
                if dist.name:
                    installed_packages.add(dist.name.lower())
            
            # Check which packages are missing
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
    
    def _inject_playwright_monitoring(self, script_content: str) -> str:
        """
        Transform the script to include monitoring using AST.
        This injects monitoring code to track Playwright script execution.
        
        Args:
            script_content: The original script content to transform
            
        Returns:
            str: The transformed script with monitoring code injected
        """
        if 'playwright' not in script_content.lower():
            return script_content
            
        try:
            from .script_transformer import transform_script
            
            # Add a startup message at the beginning of the script
            startup_message = """
# --- Script Execution Started ---
import sys
print("\n[Script Monitor] Playwright script execution started")
print(f"[Script Monitor] Python version: {sys.version}")
print("[Script Monitor] Monitoring browser interactions...\n")
# --- End of Startup Message ---\n
"""
            
            # Transform the script with monitoring
            transformed_script = transform_script(script_content)
            return startup_message + transformed_script
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[Script Monitor] Error injecting monitoring: {error_details}")
            
            # Still add the startup message even if monitoring injection fails
            startup_message = f"""
# --- Script Execution Started ---
import sys
print("\n[Script Monitor] Script execution started (monitoring initialization failed)")
print(f"[Script Monitor] Python version: {{sys.version}}")
print(f"[Script Monitor] Error: {{str(e)}}\n")
# --- End of Startup Message ---\n
"""
            return startup_message + script_content
    
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
                import sys
                import subprocess
                subprocess.check_call([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"])
                return True
                
        except Exception as e:
            print(f"Error ensuring Playwright browsers are installed: {e}")
            return False
    
    async def run_script(self, script_path: str) -> ScriptResult:
        """
        Execute a Python script and return the result with detailed error information.
        First ensures all required packages are installed.
        """
        temp_script = None
        script_content = ""
        
        try:
            # Ensure the script exists
            if not os.path.exists(script_path):
                return ScriptResult(
                    success=False,
                    error_type="FileNotFoundError",
                    error_details={"script_path": script_path, "message": "Script file not found"}
                )
            
            # Read the script content first
            with open(script_path, 'r', encoding='utf-8') as f:
                script_content = f.read()
            
            # Check if this is a Playwright script and ensure browsers are installed
            if 'playwright' in script_content.lower() and not await self._ensure_playwright_browsers():
                return ScriptResult(
                    success=False,
                    error_type="BrowserInstallationError",
                    error_details={"message": "Failed to install required Playwright browsers"}
                )
            
            # Ensure required packages are installed
            if not await self.ensure_packages_installed(script_path):
                return ScriptResult(
                    success=False,
                    error_type="DependencyError",
                    error_details={"message": "Failed to install required packages"},
                    script_content=script_content
                )
            
            # Inject monitoring if using Playwright
            monitored_script = self._inject_playwright_monitoring(script_content)
            
            # Create a temporary file for the monitored script
            temp_script = self.scripts_dir / f"temp_{os.urandom(4).hex()}.py"
            with open(temp_script, 'w', encoding='utf-8') as f:
                f.write(monitored_script)
            
            # Log the script content for debugging
            print(f"[ScriptService] Starting script execution: {script_path}")
            print(f"[ScriptService] Temporary script path: {temp_script}")
            print(f"[ScriptService] Script content (first 20 lines):")
            with open(temp_script, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i < 20:  # Only show first 20 lines to avoid cluttering logs
                        print(f"  {i+1}: {line.rstrip()}")
                    else:
                        print(f"  ... and {sum(1 for _ in f) + 1} more lines")
                        break
            
            # Create a queue to collect output lines
            output_queue = asyncio.Queue()
            
            async def read_stream(stream, is_stderr=False):
                while True:
                    try:
                        line = await stream.readline()
                        if not line:
                            break
                        line = line.decode('utf-8', errors='replace').rstrip()
                        # Print to console for immediate feedback
                        prefix = '[STDERR]' if is_stderr else '[STDOUT]'
                        print(f"{prefix} {line}")
                        await output_queue.put({
                            'type': 'stderr' if is_stderr else 'stdout',
                            'content': line
                        })
                    except Exception as e:
                        error_msg = f"Error reading {'stderr' if is_stderr else 'stdout'}: {str(e)}"
                        print(f"[ScriptService] {error_msg}")
                        await output_queue.put({
                            'type': 'error',
                            'content': error_msg
                        })
                        break
            
            try:
                # Create the subprocess with PIPE for streaming
                process = await asyncio.create_subprocess_exec(
                    sys.executable, str(temp_script),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Start reading from stdout and stderr
                stdout_task = asyncio.create_task(read_stream(process.stdout))
                stderr_task = asyncio.create_task(read_stream(process.stderr, is_stderr=True))
                
                # Wait for the process to complete or timeout
                try:
                    await asyncio.wait_for(process.wait(), timeout=300)  # 5 minutes timeout
                except asyncio.TimeoutError:
                    process.terminate()
                    await output_queue.put({
                        'type': 'error',
                        'content': 'Script execution timed out after 300 seconds'
                    })
                    return ScriptResult(
                        success=False,
                        error_type="TimeoutError",
                        error_details={"message": "Script execution timed out after 300 seconds"},
                        script_content=script_content
                    )
                
                # Wait for all output to be read
                await asyncio.gather(stdout_task, stderr_task)
                
                # Get the final return code
                returncode = process.returncode
                
                # Collect all output
                stdout_lines = []
                stderr_lines = []
                
                while not output_queue.empty():
                    item = await output_queue.get()
                    if item['type'] == 'stdout':
                        stdout_lines.append(item['content'])
                    else:
                        stderr_lines.append(item['content'])
                
                stdout = '\n'.join(stdout_lines)
                stderr = '\n'.join(stderr_lines)
                
                # If script failed with non-zero exit code but no stderr, provide more context
                if returncode != 0 and not stderr:
                    stderr = f"Script exited with non-zero status code: {returncode}\n"
                    stderr += "No error output was captured. This could be due to:\n"
                    stderr += "1. The script called sys.exit() with a non-zero code\n"
                    stderr += "2. The script was terminated by a signal\n"
                    stderr += "3. The error output was not properly captured"
                
                # Try to extract page history from the output if available
                page_history = []
                try:
                    # Look for the execution log in the output
                    for line in stdout.split('\n') + stderr.split('\n'):
                        if line.strip().startswith('PLAYWRIGHT_EXECUTION_LOG:'):
                            log_data = json.loads(line.split('PLAYWRIGHT_EXECUTION_LOG:')[1].strip())
                            if 'page_history' in log_data:
                                page_history = log_data['page_history']
                                break
                except Exception as e:
                    print(f"[ScriptService] Error extracting page history: {e}")
                
                print(f"[ScriptService] Script execution completed with return code: {returncode}")
                print(f"[ScriptService] Script stdout (length: {len(stdout)}): {stdout[:500]}{'...' if len(stdout) > 500 else ''}")
                print(f"[ScriptService] Script stderr (length: {len(stderr)}): {stderr[:500]}{'...' if len(stderr) > 500 else ''}")
                
                # Log the first few lines of the script for debugging
                print("[ScriptService] First 10 lines of script:")
                for i, line in enumerate(script_content.split('\n')[:10]):
                    print(f"  {i+1}: {line}")
                if len(script_content.split('\n')) > 10:
                    print(f"  ... and {len(script_content.split('\n')) - 10} more lines")
            except subprocess.TimeoutExpired:
                # If timeout occurs, the subprocess.run will raise this exception
                if temp_script.exists():
                    temp_script.unlink()
                return ScriptResult(
                    success=False,
                    error_type="TimeoutError",
                    error_details={"message": "Script execution timed out after 300 seconds"},
                    script_content=script_content
                )
            except Exception as e:
                # Get the full traceback
                import traceback
                tb = traceback.format_exc()
                
                # Default error details
                error_type = type(e).__name__
                error_message = str(e)
                suggestions = []
                line_number = None
                
                # Extract line number from traceback if available
                tb_lines = traceback.extract_tb(e.__traceback__)
                if tb_lines:
                    # Get the last frame where the error occurred
                    frame = tb_lines[-1]
                    line_number = frame.lineno
                    
                    # Try to get the problematic line from the script
                    problematic_line = ""
                    try:
                        with open(script_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            if 0 < line_number <= len(lines):
                                problematic_line = lines[line_number - 1].strip()
                    except Exception:
                        pass
                    
                    # Add context to error message
                    error_message = f"{error_type} at line {line_number}: {error_message}"
                    if problematic_line:
                        error_message += f"\nProblematic line: {problematic_line}"
                
                # Common error patterns and suggestions
                if "ModuleNotFoundError" in error_type:
                    module_name = error_message.split("'")[1] if "'" in error_message else ""
                    suggestions = [
                        f"The script is trying to use the '{module_name}' module which is not installed",
                        f"Try installing it with: pip install {module_name}",
                        "If using a virtual environment, make sure it's activated"
                    ]
                elif "ImportError" in error_type:
                    suggestions = [
                        "There was an error importing a module or package",
                        "Check if all required dependencies are installed",
                        "Verify that the module names are spelled correctly"
                    ]
                elif "NameError" in error_type:
                    suggestions = [
                        "The script is trying to use a variable or function that hasn't been defined",
                        "Check for typos in variable and function names",
                        "Make sure all variables are defined before they are used"
                    ]
                elif "SyntaxError" in error_type:
                    suggestions = [
                        "There's a syntax error in the script",
                        f"Check line {line_number} and the lines around it for typos",
                        "Common issues include missing colons, unmatched brackets, or incorrect indentation"
                    ]
                elif "TimeoutError" in error_type:
                    suggestions = [
                        "The script took too long to execute (timeout after 300 seconds)",
                        "Check for infinite loops or long-running operations",
                        "If the script needs more time, consider optimizing it or increasing the timeout"
                    ]
                else:
                    suggestions = [
                        "An unexpected error occurred during script execution",
                        "Check the error message and traceback for more details",
                        "Review the script for any logical errors or edge cases"
                    ]
                
                # Clean up the temp file
                if temp_script and temp_script.exists():
                    temp_script.unlink()
                
                # Create error details with page history if available
                error_details = {
                    "message": error_message,
                    "traceback": tb,
                    "line_number": line_number,
                    "suggestions": suggestions
                }
                
                # Add page history to error details if available
                if 'page_history' in locals() and page_history:
                    error_details["page_history"] = page_history
                
                return ScriptResult(
                    success=False,
                    error_type=error_type,
                    error_details=error_details,
                    script_content=script_content,
                    stdout=stdout if 'stdout' in locals() else "",
                    stderr=tb  # Include full traceback in stderr
                )
            finally:
                # Clean up the temporary file
                if temp_script.exists():
                    temp_script.unlink()
            if returncode == 0:
                return ScriptResult(
                    success=True,
                    stdout=stdout,
                    stderr=stderr,
                    returncode=returncode,
                    script_content=script_content
                )
            else:
                # Try to extract error information
                error_type = "RuntimeError"
                error_message = stderr or "Script execution failed"
                
                # Try to extract more specific error information
                if stderr:  # Only try to match if there's stderr output
                    error_match = re.search(r'^(\w+):\s*(.*?)(?:\n|$)', stderr, re.MULTILINE)
                    if error_match:
                        error_type = error_match.group(1)
                        error_message = error_match.group(2).strip()
                
                return ScriptResult(
                    success=False,
                    stdout=stdout,
                    stderr=stderr,
                    returncode=returncode,
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
                    "type": error_type,
                    "traceback": error_traceback
                },
                script_content=script_content,
                stderr=f"{error_type}: {error_message}\n\n{error_traceback}"
            )
            
        finally:
            # Clean up the temporary file if it was created
            if temp_script and temp_script.exists():
                try:
                    temp_script.unlink()
                except Exception as e:
                    print(f"Warning: Failed to delete temporary file {temp_script}: {e}")
    
    async def save_script(self, content: str, script_id: str = None) -> str:
        """Save a script to a file and return its path."""
        if script_id is None:
            import uuid
            script_id = str(uuid.uuid4())
            
        script_filename = f"script_{script_id}.py"
        script_path = self.scripts_dir / script_filename
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
            
        return str(script_path), script_id
