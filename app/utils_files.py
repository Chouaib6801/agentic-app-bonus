"""
File generation utilities for output files.

Handles creation of:
- PDF reports using ReportLab
"""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import re


def generate_pdf_report(markdown_content: str, output_path: str) -> None:
    """
    Generate a PDF report from markdown content.
    
    Uses ReportLab for PDF generation with simple styling.
    Converts basic markdown formatting to PDF elements.
    
    Args:
        markdown_content: The markdown report content
        output_path: Path where the PDF should be saved
    """
    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Get default styles and create custom ones
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    h1_style = ParagraphStyle(
        'CustomH1',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=16
    )
    
    h2_style = ParagraphStyle(
        'CustomH2',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=10,
        spaceBefore=12
    )
    
    h3_style = ParagraphStyle(
        'CustomH3',
        parent=styles['Heading3'],
        fontSize=12,
        spaceAfter=8,
        spaceBefore=10
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        leading=14
    )
    
    # Process markdown content
    story = []
    lines = markdown_content.split('\n')
    
    current_paragraph = []
    is_first_heading = True
    
    def flush_paragraph():
        """Add accumulated paragraph text to story."""
        if current_paragraph:
            text = ' '.join(current_paragraph)
            text = escape_html(text)
            text = convert_inline_formatting(text)
            if text.strip():
                story.append(Paragraph(text, body_style))
            current_paragraph.clear()
    
    def escape_html(text: str) -> str:
        """Escape HTML special characters."""
        text = text.replace('&', '&amp;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text
    
    def convert_inline_formatting(text: str) -> str:
        """Convert markdown inline formatting to ReportLab XML."""
        # Bold: **text** or __text__
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
        # Italic: *text* or _text_
        text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
        text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
        return text
    
    for line in lines:
        stripped = line.strip()
        
        # Skip empty lines (flush paragraph)
        if not stripped:
            flush_paragraph()
            continue
        
        # Headers
        if stripped.startswith('# '):
            flush_paragraph()
            text = escape_html(stripped[2:])
            if is_first_heading:
                story.append(Paragraph(text, title_style))
                is_first_heading = False
            else:
                story.append(Paragraph(text, h1_style))
        elif stripped.startswith('## '):
            flush_paragraph()
            text = escape_html(stripped[3:])
            story.append(Paragraph(text, h2_style))
        elif stripped.startswith('### '):
            flush_paragraph()
            text = escape_html(stripped[4:])
            story.append(Paragraph(text, h3_style))
        elif stripped.startswith('#### '):
            flush_paragraph()
            text = escape_html(stripped[5:])
            story.append(Paragraph(text, h3_style))
        # List items
        elif stripped.startswith('- ') or stripped.startswith('* '):
            flush_paragraph()
            text = escape_html(stripped[2:])
            text = convert_inline_formatting(text)
            story.append(Paragraph(f"• {text}", body_style))
        elif re.match(r'^\d+\.\s', stripped):
            flush_paragraph()
            text = escape_html(stripped)
            text = convert_inline_formatting(text)
            story.append(Paragraph(text, body_style))
        # Horizontal rule
        elif stripped in ['---', '***', '___']:
            flush_paragraph()
            story.append(Spacer(1, 12))
        # Regular text
        else:
            current_paragraph.append(stripped)
    
    # Flush any remaining paragraph
    flush_paragraph()
    
    # Add some content if empty
    if not story:
        story.append(Paragraph("No content generated.", body_style))
    
    # Build PDF
    doc.build(story)

