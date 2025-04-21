import os
import re
import tempfile
import shutil
import subprocess
import io
from datetime import datetime
import sys

class LatexExport:
    def __init__(self):
        """Initialize LaTeX export functionality"""
        print("Initializing LatexExport")
        # Base template with placeholders
        self.template = r"""\documentclass[12pt]{article}
\usepackage[a4paper, margin=1in]{geometry}
\usepackage{graphicx}
\usepackage{float}
\usepackage{pdfpages}
\usepackage{datetime}
\usepackage{fancyhdr}
\usepackage{titlesec}

% Setup page headers
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{Electronic Laboratory Notebook}
\fancyhead[R]{${title}$}
\fancyfoot[C]{\thepage}

\title{${title}$}
\author{Electronic Laboratory Notebook}
\date{\today}

\begin{document}

\maketitle
\tableofcontents
\newpage

${abstract}$

% Text Files
${sections}$

% Images
${images}$

% PDF Imports
${imported_pdfs}$

\end{document}"""
    
    @staticmethod
    def tex_escape(text):
        """Escape special LaTeX characters"""
        if text is None:
            return ""
        
        conv = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\^{}',
            '\\': r'\textbackslash{}',
            '<': r'\textless{}',
            '>': r'\textgreater{}',
        }
        regex = re.compile('|'.join(re.escape(key) for key in sorted(conv.keys(), key=lambda item: -len(item))))
        return regex.sub(lambda match: conv[match.group()], text)
    
    def generate_latex(self, project, files):
        """Generate LaTeX code for a project - Without using Jinja2"""
        print("Generating LaTeX content")
        
        # Create temporary directory for files
        temp_dir = tempfile.mkdtemp()
        image_dir = os.path.join(temp_dir, 'images')
        pdf_dir = os.path.join(temp_dir, 'pdfs')
        os.makedirs(image_dir, exist_ok=True)
        os.makedirs(pdf_dir, exist_ok=True)
        
        # Sort files by date (newest first)
        try:
            sorted_files = sorted(files, key=lambda f: f.updated_at if hasattr(f, 'updated_at') else datetime.now(), reverse=True)
            print(f"Sorted {len(sorted_files)} files by date")
        except Exception as e:
            print(f"Error sorting files: {e}")
            sorted_files = files
        
        # Prepare sections for text files
        sections_text = ""
        for file in sorted_files:
            if file.file_type == 'text':
                print(f"Adding text file: {file.filename}")
                section_title = self.tex_escape(file.filename)
                section_content = self.tex_escape(file.content or "No content available.")
                updated_date = ""
                if hasattr(file, 'updated_at'):
                    try:
                        updated_date = f"Last Updated: {file.updated_at.strftime('%Y-%m-%d %H:%M:%S')}"
                    except:
                        updated_date = "Date unknown"
                
                sections_text += f"""\\section{{{section_title}}}
\\textit{{{updated_date}}}

{section_content}

\\newpage
"""
        
        # Prepare images
        images_text = ""
        if any(file.file_type == 'image' for file in sorted_files):
            images_text = "\\section{Figures}\n"
            
            for file in sorted_files:
                if file.file_type == 'image':
                    print(f"Processing image file: {file.filename}")
                    safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
                    temp_image_path = os.path.join(image_dir, safe_name)
                    
                    try:
                        shutil.copy2(file.file_path, temp_image_path)
                        image_path = f"images/{safe_name}"
                        caption = self.tex_escape(file.filename)
                        
                        images_text += f"""
\\begin{{figure}}[H]
    \\centering
    \\includegraphics[width=0.8\\textwidth]{{{image_path}}}
    \\caption{{{caption}}}
\\end{{figure}}
\\newpage
"""
                    except Exception as e:
                        print(f"Error copying image {file.file_path}: {str(e)}")
        
        # Handle PDF files
        imported_pdfs_text = ""
        pdf_files = [f for f in sorted_files if f.file_type == 'binary' and f.filename.lower().endswith('.pdf')]
        
        if pdf_files:
            imported_pdfs_text = "\\section{Imported PDF Documents}\n"
            
            for i, file in enumerate(pdf_files):
                print(f"Processing PDF file: {file.filename}")
                safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
                temp_pdf_path = os.path.join(pdf_dir, safe_name)
                
                try:
                    shutil.copy2(file.file_path, temp_pdf_path)
                    pdf_path = f"pdfs/{safe_name}"
                    title = self.tex_escape(file.filename)
                    
                    imported_pdfs_text += f"""
\\subsection{{{title}}}
\\includepdf[pages=-, addtotoc={{1, section, 1, {title}, pdf:{i}}}, pagecommand={{}}]{{{pdf_path}}}
\\newpage
"""
                except Exception as e:
                    print(f"Error copying PDF {file.file_path}: {str(e)}")
        
        # Abstract section
        abstract_text = f"""\\section{{Project Description}}
{self.tex_escape(project.description or "No description provided.")}
\\newpage
"""
        
        # Replace placeholders with content
        latex_content = self.template
        latex_content = latex_content.replace("${title}$", self.tex_escape(project.name))
        latex_content = latex_content.replace("${abstract}$", abstract_text)
        latex_content = latex_content.replace("${sections}$", sections_text)
        latex_content = latex_content.replace("${images}$", images_text)
        latex_content = latex_content.replace("${imported_pdfs}$", imported_pdfs_text)
        
        print(f"LaTeX content generated, {len(latex_content)} characters")
        return latex_content, temp_dir
    
    def generate_pdf(self, latex_content, temp_dir):
        """Generate a PDF from LaTeX content"""
        try:
            # Write the LaTeX content to a file
            tex_file = os.path.join(temp_dir, 'output.tex')
            print(f"Writing LaTeX to {tex_file}")
            with open(tex_file, 'w', encoding='utf-8') as f:
                f.write(latex_content)
            
            # Compile LaTeX to PDF
            for i in range(2):
                print(f"Running pdflatex, attempt {i+1}")
                try:
                    process = subprocess.run(
                        ['pdflatex', '-interaction=nonstopmode', tex_file],
                        cwd=temp_dir,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=60  # Increased timeout for handling large PDFs
                    )
                    print(f"Return code: {process.returncode}")
                    
                    if process.returncode != 0:
                        output = process.stdout.decode('utf-8', errors='replace')
                        error = process.stderr.decode('utf-8', errors='replace')
                        print(f"pdflatex output: {output[:200]}...")
                        print(f"pdflatex error: {error[:200]}...")
                except subprocess.TimeoutExpired:
                    print("pdflatex process timed out")
                    return {'success': False, 'error': 'PDF generation timed out'}
            
            if process.returncode != 0:
                print("PDF generation failed")
                return {'success': False, 'error': 'PDF generation failed'}
            
            # Check if PDF was created
            pdf_file = os.path.join(temp_dir, 'output.pdf')
            print(f"Looking for PDF at: {pdf_file}")
            
            if not os.path.exists(pdf_file):
                print(f"PDF file not found, directory contents: {os.listdir(temp_dir)}")
                return {'success': False, 'error': 'PDF file was not created'}
            
            # Read the PDF content
            print("Reading PDF content")
            with open(pdf_file, 'rb') as f:
                pdf_content = f.read()
            
            print(f"PDF content read, {len(pdf_content)} bytes")
            return {'success': True, 'pdf_content': pdf_content}
            
        except Exception as e:
            import traceback
            print(f"Error generating PDF: {str(e)}")
            print(traceback.format_exc())
            return {'success': False, 'error': str(e)}
    
    def export_project_to_pdf(self, project, files, output_path=None):
        """Export a project to PDF"""
        print(f"Exporting project '{project.name}' to PDF")
        temp_dir = None
        try:
            # Generate LaTeX content
            latex_content, temp_dir = self.generate_latex(project, files)
            
            # Generate PDF
            result = self.generate_pdf(latex_content, temp_dir)
            
            # Handle output path if specified
            if output_path and result.get('success', False) and 'pdf_content' in result:
                print(f"Writing PDF to {output_path}")
                with open(output_path, 'wb') as f:
                    f.write(result['pdf_content'])
                result['pdf_path'] = output_path
            
            return result
            
        except Exception as e:
            import traceback
            print(f"Error in export_project_to_pdf: {str(e)}")
            print(traceback.format_exc())
            return {'success': False, 'error': str(e)}
            
        finally:
            # Always clean up the temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    print(f"Cleaning up temp directory: {temp_dir}")
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    print(f"Error cleaning up temp directory: {str(e)}")
