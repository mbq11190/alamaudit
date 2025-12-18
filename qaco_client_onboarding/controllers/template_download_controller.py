# -*- coding: utf-8 -*-

import base64
import io
import logging
import os

from odoo import http
from odoo.http import request, content_disposition

_logger = logging.getLogger(__name__)

# Try to import optional PDF generation libraries
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    _logger.info("WeasyPrint not available - PDF generation will use alternative method")

try:
    from docx import Document
    from docx.shared import Inches, Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    _logger.info("python-docx not available - Word generation will use alternative method")


class FitProperTemplateController(http.Controller):
    """Controller for downloading Fit & Proper Assessment templates."""

    def _get_template_path(self):
        """Get the path to the HTML template."""
        module_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(module_path, 'static', 'templates', 'fit_proper_assessment_template.html')

    def _read_html_template(self):
        """Read the HTML template file."""
        template_path = self._get_template_path()
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    @http.route('/onboarding/template/fit_proper/html', type='http', auth='user', methods=['GET'])
    def download_fit_proper_html(self, **kwargs):
        """Download Fit & Proper template as HTML."""
        try:
            html_content = self._read_html_template()
            
            return request.make_response(
                html_content,
                headers=[
                    ('Content-Type', 'text/html; charset=utf-8'),
                    ('Content-Disposition', content_disposition('Fit_Proper_Assessment_Template.html')),
                ]
            )
        except Exception as e:
            _logger.error(f"Error generating HTML template: {e}")
            return request.not_found()

    @http.route('/onboarding/template/fit_proper/pdf', type='http', auth='user', methods=['GET'])
    def download_fit_proper_pdf(self, **kwargs):
        """Download Fit & Proper template as PDF."""
        try:
            html_content = self._read_html_template()
            
            if WEASYPRINT_AVAILABLE:
                # Use WeasyPrint for high-quality PDF
                pdf_buffer = io.BytesIO()
                HTML(string=html_content).write_pdf(pdf_buffer)
                pdf_content = pdf_buffer.getvalue()
            else:
                # Fallback: Use Odoo's built-in wkhtmltopdf if available
                try:
                    from odoo.tools import pdf
                    pdf_content = pdf.html2pdf(html_content)
                except Exception:
                    # Last resort: Return HTML with PDF content type (browser will render)
                    _logger.warning("No PDF generator available, returning HTML for print-to-PDF")
                    return request.make_response(
                        html_content,
                        headers=[
                            ('Content-Type', 'text/html; charset=utf-8'),
                            ('Content-Disposition', content_disposition('Fit_Proper_Assessment_Template_PrintToPDF.html')),
                        ]
                    )
            
            return request.make_response(
                pdf_content,
                headers=[
                    ('Content-Type', 'application/pdf'),
                    ('Content-Disposition', content_disposition('Fit_Proper_Assessment_Template.pdf')),
                ]
            )
        except Exception as e:
            _logger.error(f"Error generating PDF template: {e}")
            return request.not_found()

    @http.route('/onboarding/template/fit_proper/docx', type='http', auth='user', methods=['GET'])
    def download_fit_proper_docx(self, **kwargs):
        """Download Fit & Proper template as Word document."""
        try:
            if DOCX_AVAILABLE:
                doc = self._create_word_document()
                docx_buffer = io.BytesIO()
                doc.save(docx_buffer)
                docx_content = docx_buffer.getvalue()
            else:
                # Fallback: Return HTML with docx-friendly styling
                _logger.warning("python-docx not available, returning HTML for Word import")
                html_content = self._read_html_template()
                return request.make_response(
                    html_content,
                    headers=[
                        ('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                        ('Content-Disposition', content_disposition('Fit_Proper_Assessment_Template.doc')),
                    ]
                )
            
            return request.make_response(
                docx_content,
                headers=[
                    ('Content-Type', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'),
                    ('Content-Disposition', content_disposition('Fit_Proper_Assessment_Template.docx')),
                ]
            )
        except Exception as e:
            _logger.error(f"Error generating Word template: {e}")
            return request.not_found()

    def _create_word_document(self):
        """Create a Word document for the Fit & Proper template."""
        doc = Document()
        
        # Set document margins
        for section in doc.sections:
            section.top_margin = Cm(2)
            section.bottom_margin = Cm(2)
            section.left_margin = Cm(2.5)
            section.right_margin = Cm(2.5)
        
        # Title
        title = doc.add_heading('📌 FIT & PROPER ASSESSMENT TEMPLATE', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Subtitle
        subtitle = doc.add_paragraph('(To be embedded under Fit & Proper Evidence and attached as signed document)')
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle.runs[0].italic = True
        
        # Section A: Identification Details
        doc.add_heading('A. IDENTIFICATION DETAILS', level=1)
        table_a = doc.add_table(rows=7, cols=2)
        table_a.style = 'Table Grid'
        
        id_items = [
            ('Entity Name', ''),
            ('Role Assessed', '☐ Director  ☐ CEO  ☐ CFO  ☐ Key Management  ☐ Trustee'),
            ('Individual Name', ''),
            ('CNIC / Passport No.', ''),
            ('Nationality', ''),
            ('Date of Assessment', ''),
            ('Applicable Regulator', '☐ SECP  ☐ SBP  ☐ NGO  ☐ Other: ___________'),
        ]
        for i, (item, value) in enumerate(id_items):
            table_a.rows[i].cells[0].text = item
            table_a.rows[i].cells[1].text = value
        
        # Section B: Integrity & Reputation
        doc.add_heading('B. INTEGRITY & REPUTATION ASSESSMENT', level=1)
        doc.add_paragraph('(Mandatory – ISQM-1 / SECP / IESBA)').italic = True
        
        table_b = doc.add_table(rows=6, cols=4)
        table_b.style = 'Table Grid'
        table_b.rows[0].cells[0].text = 'Criteria'
        table_b.rows[0].cells[1].text = 'Yes'
        table_b.rows[0].cells[2].text = 'No'
        table_b.rows[0].cells[3].text = 'Remarks'
        
        integrity_items = [
            'No criminal conviction or pending prosecution',
            'No involvement in fraud, misappropriation, or breach of trust',
            'No adverse regulatory or enforcement actions',
            'No disqualification under Companies Act 2017',
            'No history of willful default or financial misconduct',
        ]
        for i, item in enumerate(integrity_items, 1):
            table_b.rows[i].cells[0].text = item
            table_b.rows[i].cells[1].text = '☐'
            table_b.rows[i].cells[2].text = '☐'
        
        # Section C: Competence & Experience
        doc.add_heading('C. COMPETENCE & EXPERIENCE ASSESSMENT', level=1)
        
        table_c = doc.add_table(rows=6, cols=4)
        table_c.style = 'Table Grid'
        table_c.rows[0].cells[0].text = 'Criteria'
        table_c.rows[0].cells[1].text = 'Yes'
        table_c.rows[0].cells[2].text = 'No'
        table_c.rows[0].cells[3].text = 'Remarks'
        
        competence_items = [
            'Relevant academic qualification',
            'Relevant professional experience',
            "Adequate understanding of entity's business",
            'Knowledge of applicable laws & regulations',
            'Financial literacy (for directors / audit committee)',
        ]
        for i, item in enumerate(competence_items, 1):
            table_c.rows[i].cells[0].text = item
            table_c.rows[i].cells[1].text = '☐'
            table_c.rows[i].cells[2].text = '☐'
        
        # Section D: Financial Soundness
        doc.add_heading('D. FINANCIAL SOUNDNESS', level=1)
        
        table_d = doc.add_table(rows=5, cols=4)
        table_d.style = 'Table Grid'
        table_d.rows[0].cells[0].text = 'Criteria'
        table_d.rows[0].cells[1].text = 'Yes'
        table_d.rows[0].cells[2].text = 'No'
        table_d.rows[0].cells[3].text = 'Remarks'
        
        financial_items = [
            'Not declared bankrupt / insolvent',
            'No overdue taxes or statutory defaults',
            'No material unpaid liabilities to lenders',
            'No adverse credit information',
        ]
        for i, item in enumerate(financial_items, 1):
            table_d.rows[i].cells[0].text = item
            table_d.rows[i].cells[1].text = '☐'
            table_d.rows[i].cells[2].text = '☐'
        
        # Section E: Independence & Conflict
        doc.add_heading('E. INDEPENDENCE & CONFLICT OF INTEREST', level=1)
        
        table_e = doc.add_table(rows=5, cols=4)
        table_e.style = 'Table Grid'
        table_e.rows[0].cells[0].text = 'Criteria'
        table_e.rows[0].cells[1].text = 'Yes'
        table_e.rows[0].cells[2].text = 'No'
        table_e.rows[0].cells[3].text = 'Remarks'
        
        independence_items = [
            "No conflict with entity's interest",
            'No prohibited related-party relationships',
            'Disclosed all potential conflicts',
            'Not holding incompatible positions',
        ]
        for i, item in enumerate(independence_items, 1):
            table_e.rows[i].cells[0].text = item
            table_e.rows[i].cells[1].text = '☐'
            table_e.rows[i].cells[2].text = '☐'
        
        # Section F: AML/CFT
        doc.add_heading('F. AML / CFT & SANCTIONS SCREENING', level=1)
        
        table_f = doc.add_table(rows=5, cols=3)
        table_f.style = 'Table Grid'
        table_f.rows[0].cells[0].text = 'Check'
        table_f.rows[0].cells[1].text = 'Status'
        table_f.rows[0].cells[2].text = 'Evidence'
        
        table_f.rows[1].cells[0].text = 'PEP Screening'
        table_f.rows[1].cells[1].text = '☐ Clear  ☐ Flag'
        table_f.rows[1].cells[2].text = 'Screenshot / Report'
        
        table_f.rows[2].cells[0].text = 'Sanctions Screening (UN / OFAC / EU)'
        table_f.rows[2].cells[1].text = '☐ Clear  ☐ Flag'
        table_f.rows[2].cells[2].text = 'Screenshot / Report'
        
        table_f.rows[3].cells[0].text = 'Country Risk'
        table_f.rows[3].cells[1].text = '☐ Low  ☐ Medium  ☐ High'
        table_f.rows[3].cells[2].text = 'Narrative'
        
        table_f.rows[4].cells[0].text = 'Source of Wealth Reasonable'
        table_f.rows[4].cells[1].text = '☐ Yes  ☐ No'
        table_f.rows[4].cells[2].text = 'Explanation'
        
        # Section G: EDD
        doc.add_heading('G. ENHANCED DUE DILIGENCE (EDD)', level=1)
        doc.add_paragraph('(Complete only if Enhanced Due Diligence Required is checked)').italic = True
        
        table_g = doc.add_table(rows=5, cols=3)
        table_g.style = 'Table Grid'
        table_g.rows[0].cells[0].text = 'Trigger'
        table_g.rows[0].cells[1].text = 'Yes'
        table_g.rows[0].cells[2].text = 'No'
        
        edd_items = [
            'Politically Exposed Person (PEP)',
            'Foreign national from high-risk jurisdiction',
            'Complex ownership / nominee structure',
            'Adverse media',
        ]
        for i, item in enumerate(edd_items, 1):
            table_g.rows[i].cells[0].text = item
            table_g.rows[i].cells[1].text = '☐'
            table_g.rows[i].cells[2].text = '☐'
        
        doc.add_paragraph()
        doc.add_paragraph('EDD Procedures Performed:').bold = True
        doc.add_paragraph('_' * 80)
        doc.add_paragraph('_' * 80)
        doc.add_paragraph('_' * 80)
        
        # Section H: Overall Assessment
        doc.add_heading('H. OVERALL ASSESSMENT & CONCLUSION', level=1)
        
        p = doc.add_paragraph()
        p.add_run('Overall Fit & Proper Status:').bold = True
        doc.add_paragraph('☐ Fit & Proper')
        doc.add_paragraph('☐ Fit & Proper with Conditions')
        doc.add_paragraph('☐ Not Fit & Proper')
        doc.add_paragraph()
        doc.add_paragraph('Conditions / Safeguards (if any):').bold = True
        doc.add_paragraph('_' * 80)
        doc.add_paragraph('_' * 80)
        
        # Section I: Declaration
        doc.add_heading('I. DECLARATION BY ASSESSED PERSON', level=1)
        
        doc.add_paragraph('I confirm that the information provided is true and complete. I undertake to inform the entity and auditors of any material change.').italic = True
        doc.add_paragraph()
        doc.add_paragraph('Name: ________________________________')
        doc.add_paragraph('Signature: ________________________________')
        doc.add_paragraph('Date: ________________________________')
        
        # Section J: Auditor Confirmation
        doc.add_heading('J. AUDITOR / FIRM CONFIRMATION', level=1)
        
        doc.add_paragraph('We confirm that Fit & Proper assessment has been conducted in accordance with:').bold = True
        doc.add_paragraph('• Companies Act, 2017')
        doc.add_paragraph('• ISQM-1')
        doc.add_paragraph('• IESBA Code of Ethics')
        doc.add_paragraph('• SECP / SBP / applicable regulations')
        doc.add_paragraph()
        doc.add_paragraph('Engagement Partner: ________________________________')
        doc.add_paragraph('Signature: ________________________________')
        doc.add_paragraph('Date: ________________________________')
        
        return doc
