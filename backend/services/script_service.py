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

class ScriptService:
    def __init__(self, scripts_dir: str = "data/scripts"):
        self.scripts_dir = Path(scripts_dir)
        self.scripts_dir.mkdir(exist_ok=True)
    
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
        Inject monitoring code into the script if it uses Playwright.
        This wraps the script in a monitoring context to track page interactions.
        """
        if 'playwright' not in script_content.lower():
            return script_content
            
        # Add monitoring imports and context manager
        monitoring_imports = (
            "from playwright.sync_api import sync_playwright\n"
            "from playwright_monitor import monitor_playwright\n"
            "import sys\n"
            "import os\n"
            "# Add the backend directory to the path to allow imports\n"
            "sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))\n\n"
        )
        
        # Find the main script content
        lines = script_content.splitlines()
        import_lines = []
        other_lines = []
        
        # Separate import lines from other lines
        for line in lines:
            if line.strip().startswith(('import ', 'from ')):
                import_lines.append(line)
            else:
                other_lines.append(line)
        
        # Reconstruct the script with monitoring
        monitored_script = []
        monitored_script.extend(import_lines)
        monitored_script.append("")
        monitored_script.append("# --- Monitoring Code (Injected) ---")
        monitored_script.append(monitoring_imports)
        
        # Add the monitoring context manager
        monitored_script.append("# Wrap the script in a monitoring context")
        monitored_script.append("if __name__ == '__main__':")
        monitored_script.append("    with monitor_playwright() as context:")
        
        # Add the original code, properly indented
        for line in other_lines:
            if line.strip():
                monitored_script.append(f"        {line}")
            else:
                monitored_script.append("")
        
        return "\n".join(monitored_script)
    
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
            
            # Execute the script with a timeout using subprocess.run in a thread
            try:
                def run_script():
                    return subprocess.run(
                        [sys.executable, str(temp_script)],
                        capture_output=True,
                        text=True,
                        timeout=300,  # 5 minutes timeout
                        encoding='utf-8',
                        errors='replace'
                    )
                
                # Run the blocking subprocess in a separate thread
                process = await asyncio.to_thread(run_script)
                stdout = process.stdout
                stderr = process.stderr
                returncode = process.returncode
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
                # Clean up the temp file before re-raising
                if temp_script.exists():
                    temp_script.unlink()
                return ScriptResult(
                    success=False,
                    error_type="RuntimeError",
                    error_details={"message": f"Script execution failed: {str(e)}"},
                    script_content=script_content
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
