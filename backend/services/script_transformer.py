"""AST-based transformer for injecting monitoring code into Playwright scripts."""
import ast
import astor
import os
import sys
from typing import Optional, List, Dict, Any, Set, Tuple

class PlaywrightTransformer(ast.NodeTransformer):
    """AST transformer for injecting monitoring code into Playwright scripts."""
    
    def __init__(self):
        self.imports_added = False
        self.tracker_var = "_tracker"
        self.imported_names: Set[str] = set()
        self.context_vars: Set[str] = set()
    
    def visit_Module(self, node: ast.Module) -> ast.Module:
        # First collect all imports and track imported names
        self._collect_imports(node)
        
        # Add our monitoring imports if Playwright is being used
        if not self.imports_added and any(name in self.imported_names 
                                       for name in ['sync_playwright', 'playwright']):
            self._add_monitoring_imports(node)
        
        # Process the rest of the module
        self.generic_visit(node)
        return node
    
    def _collect_imports(self, node: ast.Module) -> None:
        """Collect all imported names from the module."""
        for n in ast.walk(node):
            if isinstance(n, (ast.Import, ast.ImportFrom)):
                for alias in n.names:
                    self.imported_names.add(alias.name.split('.')[0])
    
    def _add_monitoring_imports(self, node: ast.Module) -> None:
        """Add monitoring-related imports to the module."""
        # Add the project root to the Python path
        sys_path_append = ast.Expr(
            value=ast.Call(
                func=ast.Attribute(
                    value=ast.Name(id='sys', ctx=ast.Load()),
                    attr='path',
                    ctx=ast.Load()
                ),
                args=[],
                keywords=[],
                starargs=ast.List(
                    elts=[
                        ast.Constant(value=os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
                    ],
                    ctx=ast.Load()
                ),
                kwargs=[]
            )
        )
        
        # Add the imports
        imports = [
            ast.Import(names=[ast.alias(name='os', asname=None)]),
            ast.Import(names=[ast.alias(name='sys', asname=None)]),
            sys_path_append,
            ast.ImportFrom(module='backend.services.playwright_tracker', 
                          names=[ast.alias(name='PlaywrightTracker', asname='tracker')], 
                          level=0),
            ast.ImportFrom(
                module='playwright.sync_api',
                names=[ast.alias(name='sync_playwright')],
                level=0
            )
        ]
        node.body = imports + node.body
        self.imports_added = True
    
    def visit_With(self, node: ast.With) -> ast.With:
        """Transform Playwright context managers to include monitoring."""
        if not self._is_playwright_context(node):
            return self.generic_visit(node)
        
        # Track the context variable
        context_var = None
        if isinstance(node.items[0].optional_vars, ast.Name):
            context_var = node.items[0].optional_vars.id
            self.context_vars.add(context_var)
        
        # Add tracker initialization before the with block
        tracker_init = ast.Expr(
            value=ast.Call(
                func=ast.Name(id='print', ctx=ast.Load()),
                args=[ast.Constant(value="[Script Monitor] Initializing Playwright monitoring...")],
                keywords=[]
            )
        )
        
        # Process the body of the with block
        self.generic_visit(node)
        
        # Add page wrapping for the context
        if context_var:
            # Add code to wrap the browser context
            wrap_code = ast.parse(f"""
{context_var} = tracker.wrap_browser({context_var})
            """).body
            node.body = wrap_code + node.body
        
        # Add tracker initialization at the beginning
        node.body = [tracker_init] + node.body
        
        return node
    
    def _is_playwright_context(self, node: ast.With) -> bool:
        """Check if this is a Playwright context manager."""
        if not node.items:
            return False
            
        item = node.items[0]
        if not isinstance(item.context_expr, ast.Call):
            return False
            
        # Check for sync_playwright()
        if (isinstance(item.context_expr.func, ast.Name) and 
            item.context_expr.func.id == 'sync_playwright'):
            return True
            
        # Check for page/context methods
        if (isinstance(item.context_expr.func, ast.Attribute) and
            hasattr(item.context_expr.func.value, 'id') and
            item.context_expr.func.value.id in self.context_vars):
            return True
            
        return False

def transform_script(script_content: str) -> str:
    """
    Transform a Playwright script to include monitoring.
    
    Args:
        script_content: The original script content as a string
        
    Returns:
        str: The transformed script with monitoring code injected
    """
    try:
        tree = ast.parse(script_content)
        transformer = PlaywrightTransformer()
        new_tree = transformer.visit(tree)
        ast.fix_missing_locations(new_tree)
        
        # Add a final print statement to show monitoring is active
        final_print = ast.parse('print("[Script Monitor] Script monitoring is active")')
        if isinstance(new_tree, ast.Module):
            new_tree.body.extend(final_print.body)
        
        return astor.to_source(new_tree)
    except Exception as e:
        # If transformation fails, return the original script with a warning
        print(f"[Script Monitor] Warning: Could not inject monitoring: {e}")
        return script_content
