"""
RTF Handler - Utility functions for working with RTF content
"""
import re

def is_rtf_content(content):
    """
    Determine if content is in RTF format
    
    Args:
        content: The text content to check
        
    Returns:
        Boolean indicating if the content is RTF
    """
    if not content:
        return False
    
    # Check if the content starts with the RTF header
    return content.strip().startswith(r'{\rtf')

def extract_text_from_rtf(rtf_content):
    """
    Extract plain text from RTF content using regex patterns
    
    Args:
        rtf_content: The RTF content to convert
        
    Returns:
        Plain text extracted from RTF
    """
    if not rtf_content:
        return ""
    
    try:
        # Remove RTF control sequences
        text = re.sub(r'\\[a-z0-9]+', ' ', rtf_content)  # Remove control words
        text = re.sub(r'\{|\}', '', text)  # Remove braces
        text = re.sub(r'\\\'[0-9a-f]{2}', '', text)  # Remove hex escapes
        text = re.sub(r'\\par', '\n', text)  # Replace paragraph marks with newlines
        text = re.sub(r'\\\*.*?;', '', text)  # Remove other control sequences
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from RTF: {str(e)}")
        return "Error processing RTF content"

def process_rtf_file(file_path):
    """
    Read an RTF file and extract plain text
    
    Args:
        file_path: Path to RTF file
        
    Returns:
        Tuple of (rtf_content, plain_text)
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            rtf_content = f.read()
        
        if is_rtf_content(rtf_content):
            plain_text = extract_text_from_rtf(rtf_content)
            return rtf_content, plain_text
        else:
            # Not actually RTF content despite the file path
            return None, rtf_content
    except Exception as e:
        print(f"Error processing RTF file: {str(e)}")
        return None, None

def handle_content_update(new_content, old_rtf_content=None):
    """
    Handle updating content, checking if it's RTF and extracting plain text if needed
    
    Args:
        new_content: The updated content
        old_rtf_content: Previous RTF content, if any
        
    Returns:
        Tuple of (plain_text, rtf_content)
    """
    # If content is RTF, extract plain text
    if is_rtf_content(new_content):
        return extract_text_from_rtf(new_content), new_content
    
    # If content was previously RTF but now isn't, keep the new content as is
    # and clear RTF content
    return new_content, None

def get_display_content(plain_text, rtf_content):
    """
    Get the appropriate content for display
    
    Args:
        plain_text: Plain text content
        rtf_content: RTF content (if any)
        
    Returns:
        Content to display to the user
    """
    # If we have RTF content, use the plain text for display
    if rtf_content:
        return plain_text
    
    # Otherwise, just use plain text
    return plain_text
