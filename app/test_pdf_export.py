"""
This script tests the PDF export functionality in isolation.
Run it directly to test if PDF generation works without Flask route issues.
"""

import os
import sys
import json
from datetime import datetime
import traceback

# Add parent directory to path so we can import our modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Create dummy objects for testing
class DummyProject:
    def __init__(self, name, description):
        self.id = 1
        self.name = name
        self.description = description

class DummyFile:
    def __init__(self, filename, file_type, content=None, file_path=None):
        self.id = 1
        self.filename = filename
        self.file_type = file_type
        self.content = content
        self.file_path = file_path
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

def test_latex_export():
    """Test the LaTeX export functionality"""
    try:
        print("Importing LatexExport...")
        from app.latex_export import LatexExport
        
        # Create a test project
        project = DummyProject("Test Project", "This is a test project for PDF export")
        
        # Create some test files
        files = [
            DummyFile("README.md", "text", "# Test Project\n\nThis is a test file."),
            DummyFile("Notes.txt", "text", "These are some test notes.")
        ]
        
        # Test image file if available
        test_image_path = os.path.join(parent_dir, "test_image.jpg")
        if os.path.exists(test_image_path):
            files.append(DummyFile("test_image.jpg", "image", file_path=test_image_path))
        
        print(f"Created test project with {len(files)} files")
        
        # Initialize LaTeX export
        latex_export = LatexExport()
        
        # Generate LaTeX
        print("Generating LaTeX...")
        try:
            latex_content, temp_dir = latex_export.generate_latex(project, files)
            print(f"LaTeX generated: {len(latex_content)} characters")
        except Exception as e:
            print(f"Error generating LaTeX: {str(e)}")
            print(traceback.format_exc())
            return False
        
        # Generate PDF
        print("Generating PDF...")
        try:
            result = latex_export.generate_pdf(latex_content, temp_dir)
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            print(traceback.format_exc())
            return False
        
        # Check result
        print(f"PDF generation result: {result.get('success')}")
        if not result.get('success', False):
            print(f"Error: {result.get('error', 'Unknown error')}")
            return False
        
        # Write PDF to file if successful
        if 'pdf_content' in result:
            output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_output.pdf")
            with open(output_path, 'wb') as f:
                f.write(result['pdf_content'])
            print(f"PDF written to: {output_path}")
        
        # Test JSON serialization
        print("Testing JSON serialization...")
        clean_result = {k: v for k, v in result.items() if k != 'pdf_content'}
        try:
            json_str = json.dumps(clean_result)
            print(f"JSON serialization successful: {len(json_str)} characters")
            print(f"JSON: {json_str}")
        except Exception as e:
            print(f"JSON serialization failed: {str(e)}")
            
            # Identify problematic keys
            problematic_keys = []
            for key, value in clean_result.items():
                try:
                    json.dumps({key: value})
                except Exception:
                    problematic_keys.append(key)
                    print(f"Problematic key: {key}, value type: {type(value)}")
            
            if problematic_keys:
                print(f"Problematic keys for JSON serialization: {problematic_keys}")
            return False
        
        print("Test completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error in test: {str(e)}")
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Check if pdflatex is available
    import subprocess
    try:
        subprocess.run(['pdflatex', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("pdflatex is available in the system")
    except FileNotFoundError:
        print("WARNING: pdflatex is not installed or not in PATH. PDF generation will fail.")
        print("To fix: Install TexLive or MikTeX on your system.")

    # Run the test
    success = test_latex_export()
    print(f"Test {'passed' if success else 'failed'}")
    sys.exit(0 if success else 1)
