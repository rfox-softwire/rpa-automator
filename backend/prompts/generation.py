from typing import List, Dict, Any

def get_generate_prompt(instruction: str) -> str:
    """Generate the prompt for script generation."""
    return (
        "You are a RPA assistant that generates a Python script based on a user's instruction "
        "for interactions with web applications using the Playwright package.\n\n"
        f"The user's instructions are: {instruction}\n\n"
        "IMPORTANT: The script should follow these rules:\n"
        "1. Use `from playwright.sync_api import sync_playwright` (synchronous API)\n"
        "2. Use standard synchronous Python (no async/await)\n"
        "3. Do not use try/catch blocks\n"
        "4. The script should be self-contained with all necessary imports\n"
        "5. The script should be executable directly\n\n"
        "Only return the proposed python script."
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
        f"Here's the original script that had the error (convert it to synchronous code):\n```python\n{original_script}\n```\n\n"
        "IMPORTANT: The script should follow these rules:\n"
        "1. Use `from playwright.sync_api import sync_playwright` (synchronous API)\n"
        "2. Use standard synchronous Python (no async/await)\n"
        "3. Do not use try/catch blocks\n"
        "4. The script should be self-contained with all necessary imports\n"
        "5. The script should be executable directly\n\n"
        "Only return the proposed python script."
    ]
    
    # Add page history if available (only include most recent 2 pages to save tokens)
    if page_history:
        prompt_parts.append("=== PAGE HISTORY (MOST RECENT 2 PAGES) ===\n"
                         "Key page states before the error. Focus on these when debugging.\n")
        
        # Only process the 2 most recent pages
        MAX_PAGES = 2
        MAX_HTML_PREVIEW = 2000
        
        for i, page in enumerate(page_history[-MAX_PAGES:], 1):
            # Extract key metadata
            url = page.get('url', '').split('?')[0]  # Remove query params
            title = (page.get('title', '')[:50] + '...') if len(page.get('title', '')) > 50 else page.get('title', 'No title')
            
            # Format compact page info
            page_info = [f"[Page {len(page_history)-MAX_PAGES + i}] {title}"]
            if url:
                page_info[-1] += f"\n- URL: {url}"
            
            # Add HTML analysis if available
            if 'html' in page and page['html']:
                html_preview = page['html'].strip()[:MAX_HTML_PREVIEW]
                
                # Extract key elements (more targeted approach)
                elements = []
                html_lower = html_preview.lower()
                
                # Check for key elements without loading the entire HTML into memory
                key_elements = [
                    ('form', 'Forms'),
                    ('table', 'Tables'),
                    ('button', 'Buttons'),
                    ('input', 'Inputs'),
                    ('select', 'Dropdowns'),
                    ('iframe', 'Iframes')
                ]
                
                found_elements = []
                for elem, label in key_elements:
                    if f'<{elem}' in html_lower:
                        count = html_lower.count(f'<{elem}')
                        found_elements.append(f"{label}: {count}")
                
                # Add element summary if any were found
                if found_elements:
                    page_info.append("Elements: " + ", ".join(found_elements))
                
                # Add a small sample of the HTML structure
                page_info.append("HTML Sample (first 500 chars):")
                sample = html_preview[:500]
                if len(html_preview) > 500:
                    sample += "..."
                page_info.append(f"```html\n{sample}\n```")
            
            prompt_parts.append("\n".join(page_info) + "\n")
    
    prompt_parts.extend([
        "\nPlease generate a corrected version of the script that fixes the error while maintaining the original functionality.",
        f"The user's original instruction was: {instruction}"
    ])
    
    return "\n".join(prompt_parts)
