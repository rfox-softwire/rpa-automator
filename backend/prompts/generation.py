from typing import List, Dict, Any

def get_generate_prompt(instruction: str) -> str:
    """Generate the prompt for script generation."""
    return (
        "You are a RPA assistant that generates a Python script based on a user's instruction "
        "for interactions with web applications using the Playwright package.\n\n"
        f"The user's instructions are: {instruction}\n"
        "Propose a Python script that will perform the actions described in the user's instructions. Only return the proposed python script and avoid using try/catch blocks"
    )

def get_repair_prompt(instruction: str, error_context: str, original_script: str, page_history: List[Dict[str, Any]] = None) -> str:
    """Generate the prompt for script repair.
    
    Args:
        instruction: The original user instruction
        error_context: Formatted error context including any page history
        original_script: The script that needs to be fixed
        page_history: List of page objects containing page titles, URLs, and HTML content
    """
    prompt_parts = [
        "You are a RPA assistant that generates a Python script based on a user's instruction "
        "for interactions with web applications using the Playwright package.\n\n"
        f"The user is trying to fix an error in their script. Here's the error that occurred:\n{error_context}\n\n"
        f"Here's the original script that had the error:\n```python\n{original_script}\n```\n\n"
        "Only return the proposed python script and avoid using try/catch blocks"
    ]
    
    # Add page history if available
    if page_history:
        prompt_parts.append("=== PAGE HISTORY ===\n")
        MAX_HTML_PREVIEW = 8000
        for i, page in enumerate(page_history, 1):
            page_info = f"--- Page {i}: {page.get('title', 'No title')} ({page.get('url', 'No URL')}) ---\n"
            if 'html' in page:
                html_preview = page['html'][:MAX_HTML_PREVIEW]
                if len(page['html']) > MAX_HTML_PREVIEW:
                    html_preview += "\n... [truncated]"
                page_info += f"HTML Preview (first {len(html_preview)} characters):\n{html_preview}\n"
            prompt_parts.append(page_info)
    
    prompt_parts.extend([
        "\nPlease generate a corrected version of the script that fixes the error while maintaining the original functionality.",
        f"The user's original instruction was: {instruction}"
    ])
    
    return "\n".join(prompt_parts)
