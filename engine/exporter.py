"""PDF generation engine using ReportLab."""

from __future__ import annotations
import io
from pathlib import Path
from uuid import UUID
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.units import inch

class ReportExporter:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        self.styles.add(ParagraphStyle(
            name='NexusHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor("#A7A5FF"),
            spaceAfter=20,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='NexusCardTitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor("#A7A5FF"),
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        ))
        self.styles.add(ParagraphStyle(
            name='NexusMetaData',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            fontName='Courier'
        ))

        self.styles.add(ParagraphStyle(
            name='NexusLink',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.blue,
            fontName='Helvetica'
        ))
        self.styles.add(ParagraphStyle(
            name='NexusItalic',
            parent=self.styles['Normal'],
            fontSize=9,
            fontName='Helvetica-Oblique',
            textColor=colors.grey
        ))

    def generate_pdf(self, idea_title: str, idea_description: str, report_content: str, cards: list, citations: list) -> bytes:
        """Generate a valid, premium-styled PDF binary stream."""
        buffer = io.BytesIO()
        try:
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
            elements = []

            # Header
            elements.append(Paragraph(f"AIdeator // Intelligence_Report", self.styles['NexusMetaData']))
            elements.append(Paragraph(idea_title.upper() if idea_title else "UNTITLED_CONCEPT", self.styles['NexusHeader']))
            elements.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['NexusMetaData']))
            elements.append(Spacer(1, 0.2 * inch))

            # Description
            elements.append(Paragraph("CONCEPT_SUMMARY", self.styles['NexusCardTitle']))
            elements.append(Paragraph(idea_description or "No description provided.", self.styles['Normal']))
            elements.append(Spacer(1, 0.3 * inch))

            # Main Content (Synthesized intelligence)
            elements.append(Paragraph("SYNTHESIZED_INTELLIGENCE", self.styles['NexusCardTitle']))
            
            # Better text cleaning for ReportLab Paragraph compatibility
            # Paragraph handles <b>, <i>, <br/>, and <u>
            processed_content = report_content.replace("**", "<b>").replace("__", "<i>")
            processed_content = processed_content.replace("\n", "<br/>")
            # Remove any other problematic markdown/html characters that might break the parser
            processed_content = processed_content.replace("#", "").replace("- ", "&bull; ")
            
            elements.append(Paragraph(processed_content, self.styles['Normal']))
            elements.append(Spacer(1, 0.3 * inch))

            # Bento Cards (Dimensions)
            if cards:
                elements.append(Paragraph("DIMENSIONAL_SCORES", self.styles['NexusCardTitle']))
                data = [["Dimension", "Score", "Confidence"]]
                for card in cards:
                    data.append([
                        str(card.get('type', 'Unknown')).capitalize(),
                        str(card.get('score', 'N/A')),
                        f"{card.get('confidence', 0)}%"
                    ])
                
                t = Table(data, colWidths=[2 * inch, 1 * inch, 1.5 * inch])
                t.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#A7A5FF")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                ]))
                elements.append(t)
                elements.append(Spacer(1, 0.3 * inch))

            # Raw Citations
            if citations:
                elements.append(PageBreak())
                elements.append(Paragraph("SOURCE_CITATIONS", self.styles['NexusCardTitle']))
                for i, citation in enumerate(citations, 1):
                    elements.append(Paragraph(f"[{i}] {citation.get('title', 'Unknown Source')}", self.styles['Normal']))
                    elements.append(Paragraph(citation.get('url', ''), self.styles['NexusLink']))
                    elements.append(Paragraph(f"Context: {citation.get('snippet', 'No snippet available.')}", self.styles['NexusItalic']))
                    elements.append(Spacer(1, 0.1 * inch))

            doc.build(elements)
        except Exception as e:
            # Fallback for unexpected rendering errors to at least provide SOMETHING
            buffer.seek(0)
            buffer.truncate(0)
            fallback_doc = SimpleDocTemplate(buffer, pagesize=A4)
            fallback_doc.build([Paragraph(f"Critical Rendering Error: {str(e)}", self.styles['Normal'])])
        
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
