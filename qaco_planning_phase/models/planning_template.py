# -*- coding: utf-8 -*-
"""
Session 7B: Planning Templates - Industry-specific pre-configured planning data
Accelerates audit setup with pre-populated risks and analytical procedures.
"""

import json
import logging
from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PlanningTemplate(models.Model):
    """Industry-specific planning templates with pre-populated data."""
    _name = 'qaco.planning.template'
    _description = 'Planning Template - Industry Presets'
    _order = 'industry_type, name'

    name = fields.Char(
        string='Template Name',
        required=True,
        help='Descriptive name for this planning template'
    )
    industry_type = fields.Selection([
        ('manufacturing', 'Manufacturing'),
        ('financial_services', 'Financial Services'),
        ('services', 'Services Sector'),
        ('npo', 'Not-for-Profit'),
        ('retail', 'Retail & Distribution'),
        ('construction', 'Construction & Real Estate'),
        ('other', 'Other Industries'),
    ], string='Industry Type', required=True, help='Primary industry classification')
    
    description = fields.Text(string='Description', help='Template usage guidance and applicability')
    template_data = fields.Text(
        string='Template Data (JSON)',
        help='JSON structure containing P-2 business risks and P-4 analytical procedures'
    )
    active = fields.Boolean(string='Active', default=True)
    
    def action_apply_to_planning(self, planning_main_id):
        """
        Apply this template to a planning phase record.
        Populates P-2 business risks and P-4 analytical procedures.
        """
        self.ensure_one()
        planning = self.env['qaco.planning.main'].browse(planning_main_id)
        
        if not planning:
            raise UserError('Planning phase record not found.')
        
        if not self.template_data:
            raise UserError('This template has no data configured.')
        
        try:
            data = json.loads(self.template_data)
        except json.JSONDecodeError:
            raise UserError('Template data is not valid JSON.')
        
        # Apply P-2 Business Risks
        if 'p2_business_risks' in data and planning.p2_entity_id:
            self._apply_p2_risks(planning.p2_entity_id, data['p2_business_risks'])
        
        # Apply P-4 Analytical Procedures
        if 'p4_analytical_procedures' in data and planning.p4_analytical_id:
            self._apply_p4_procedures(planning.p4_analytical_id, data['p4_analytical_procedures'])
        
        planning.message_post(
            body=f'Planning template applied: <b>{self.name}</b><br/>'
                 f'Pre-populated {len(data.get("p2_business_risks", []))} business risks and '
                 f'{len(data.get("p4_analytical_procedures", []))} analytical procedures.',
            subject='Planning Template Applied'
        )
        
        return True
    
    def _apply_p2_risks(self, p2_entity, risks_data):
        """Create P-2 business risk records from template."""
        BusinessRisk = self.env['qaco.planning.p2.business.risk']
        
        for risk in risks_data:
            BusinessRisk.create({
                'p2_entity_id': p2_entity.id,
                'audit_id': p2_entity.audit_id.id,
                'risk_description': risk.get('risk_description', ''),
                'impact': risk.get('impact', 'medium'),
                'likelihood': risk.get('likelihood', 'medium'),
                'risk_category': risk.get('risk_category', 'operational'),
                'mitigation_strategy': risk.get('mitigation_strategy', ''),
            })
        
        _logger.info(f"Applied {len(risks_data)} P-2 business risks from template to {p2_entity.audit_id.name}")
    
    def _apply_p4_procedures(self, p4_analytical, procedures_data):
        """Create P-4 analytical procedure records from template."""
        # Note: This assumes a P-4 line model exists. Adjust based on actual structure.
        # If P-4 uses embedded fields rather than One2many, store in JSON or Text field instead.
        
        p4_analytical.write({
            'template_procedures': json.dumps(procedures_data),
            'template_applied': True,
        })
        
        _logger.info(f"Applied {len(procedures_data)} P-4 analytical procedures from template to {p4_analytical.audit_id.name}")


class PlanningTemplateWizard(models.TransientModel):
    """Wizard to select and apply planning template to a planning phase."""
    _name = 'qaco.planning.template.wizard'
    _description = 'Apply Planning Template Wizard'

    planning_main_id = fields.Many2one(
        'qaco.planning.main',
        string='Planning Phase',
        required=True,
        default=lambda self: self._get_active_planning_id()
    )
    template_id = fields.Many2one(
        'qaco.planning.template',
        string='Select Template',
        required=True,
        domain="[('active', '=', True)]",
        help='Choose an industry-specific template to pre-populate planning data'
    )
    industry_type = fields.Selection(
        related='template_id.industry_type',
        string='Industry',
        readonly=True
    )
    description = fields.Text(
        related='template_id.description',
        string='Template Description',
        readonly=True
    )
    
    def action_apply_template(self):
        """Apply selected template and close wizard."""
        self.ensure_one()
        
        if self.planning_main_id.is_planning_locked:
            raise UserError('Cannot apply template to a locked planning phase.')
        
        # Check if P-2 or P-4 already have data (warn user)
        if self.planning_main_id.p2_entity_id:
            existing_risks = self.env['qaco.planning.p2.business.risk'].search_count([
                ('p2_entity_id', '=', self.planning_main_id.p2_entity_id.id)
            ])
            if existing_risks > 0:
                raise UserError(
                    f'P-2 Entity Understanding already has {existing_risks} business risk(s). '
                    f'Applying a template will add more risks. Consider clearing existing data first.'
                )
        
        self.template_id.action_apply_to_planning(self.planning_main_id.id)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Template Applied Successfully',
                'message': f'{self.template_id.name} has been applied to planning phase.',
                'type': 'success',
                'sticky': False,
            }
        }
