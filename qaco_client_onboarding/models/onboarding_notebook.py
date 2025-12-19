# -*- coding: utf-8 -*-
"""
Onboarding Notebook & Notes with Save & Next Functionality
===========================================================
Provides persistent notebook/note-taking with:
- Save & Next navigation
- Auto-save drafts (30 seconds)
- Session persistence
- Draft recovery
- Sequential note management
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class OnboardingNotebook(models.Model):
    """Parent notebook container for organizing notes."""
    _name = 'qaco.onboarding.notebook'
    _description = 'Onboarding Notebook'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    name = fields.Char(
        string='Notebook Title',
        required=True,
        tracking=True,
    )
    description = fields.Text(
        string='Description',
        help='Purpose and scope of this notebook.',
    )
    onboarding_id = fields.Many2one(
        'qaco.client.onboarding',
        string='Client Onboarding',
        ondelete='cascade',
        tracking=True,
        index=True,
    )
    audit_id = fields.Many2one(
        'qaco.audit',
        string='Audit',
        related='onboarding_id.audit_id',
        store=True,
        readonly=True,
        index=True,
    )
    note_ids = fields.One2many(
        'qaco.onboarding.note',
        'notebook_id',
        string='Notes',
    )
    note_count = fields.Integer(
        string='Note Count',
        compute='_compute_note_count',
        store=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    color = fields.Integer(
        string='Color Index',
        default=0,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True)

    # Progress tracking
    progress_percentage = fields.Float(
        string='Progress %',
        compute='_compute_progress',
        store=True,
    )
    last_activity_date = fields.Datetime(
        string='Last Activity',
        compute='_compute_last_activity',
        store=True,
    )

    @api.depends('note_ids')
    def _compute_note_count(self):
        for record in self:
            record.note_count = len(record.note_ids)

    @api.depends('note_ids.is_completed')
    def _compute_progress(self):
        for record in self:
            total = len(record.note_ids)
            if total:
                completed = len(record.note_ids.filtered('is_completed'))
                record.progress_percentage = (completed / total) * 100
            else:
                record.progress_percentage = 0.0

    @api.depends('note_ids.write_date')
    def _compute_last_activity(self):
        for record in self:
            if record.note_ids:
                record.last_activity_date = max(record.note_ids.mapped('write_date'))
            else:
                record.last_activity_date = record.write_date

    def action_create_note(self):
        """Create a new note in this notebook."""
        self.ensure_one()
        # Get next sequence number
        max_seq = max(self.note_ids.mapped('sequence') or [0])
        note = self.env['qaco.onboarding.note'].create({
            'name': _('New Note %s') % (len(self.note_ids) + 1),
            'notebook_id': self.id,
            'sequence': max_seq + 10,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qaco.onboarding.note',
            'res_id': note.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_view_notes(self):
        """Open notes in this notebook."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Notes - %s') % self.name,
            'res_model': 'qaco.onboarding.note',
            'view_mode': 'tree,form',
            'domain': [('notebook_id', '=', self.id)],
            'context': {
                'default_notebook_id': self.id,
                'default_onboarding_id': self.onboarding_id.id,
            },
        }


class OnboardingNote(models.Model):
    """Individual note with Save & Next and auto-save functionality."""
    _name = 'qaco.onboarding.note'
    _description = 'Onboarding Note'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'notebook_id, sequence, id'

    # ═══════════════════════════════════════════════════════════════════════════
    # CORE FIELDS
    # ═══════════════════════════════════════════════════════════════════════════
    name = fields.Char(
        string='Note Title',
        required=True,
        tracking=True,
    )
    notebook_id = fields.Many2one(
        'qaco.onboarding.notebook',
        string='Notebook',
        required=True,
        ondelete='cascade',
    )
    onboarding_id = fields.Many2one(
        'qaco.client.onboarding',
        string='Client Onboarding',
        related='notebook_id.onboarding_id',
        store=True,
        readonly=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Determines the order of notes for Save & Next navigation.',
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # CONTENT FIELDS
    # ═══════════════════════════════════════════════════════════════════════════
    content = fields.Html(
        string='Note Content',
        sanitize=True,
        tracking=True,
        help='Main content of the note. Supports rich text formatting.',
    )
    plain_content = fields.Text(
        string='Plain Text Content',
        compute='_compute_plain_content',
        store=True,
        help='Plain text version for search and preview.',
    )
    summary = fields.Text(
        string='Summary',
        help='Brief summary of the note content.',
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # AUTO-SAVE & DRAFT FIELDS
    # ═══════════════════════════════════════════════════════════════════════════
    draft_content = fields.Html(
        string='Draft Content',
        help='Auto-saved draft content. Restored on session recovery.',
    )
    is_draft = fields.Boolean(
        string='Is Draft',
        default=True,
        tracking=True,
        help='True if note has unsaved changes.',
    )
    last_save_date = fields.Datetime(
        string='Last Saved',
        readonly=True,
        tracking=True,
    )
    last_auto_save_date = fields.Datetime(
        string='Last Auto-Save',
        readonly=True,
    )
    save_count = fields.Integer(
        string='Save Count',
        default=0,
        readonly=True,
        help='Number of times this note has been saved.',
    )
    has_draft_recovery = fields.Boolean(
        string='Has Draft to Recover',
        compute='_compute_has_draft_recovery',
        store=True,
        help='Indicates if there is a draft newer than the saved content.',
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # STATUS & COMPLETION
    # ═══════════════════════════════════════════════════════════════════════════
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('completed', 'Completed'),
    ], string='Status', default='draft', tracking=True)
    is_completed = fields.Boolean(
        string='Completed',
        compute='_compute_is_completed',
        store=True,
    )
    completed_date = fields.Datetime(
        string='Completed Date',
        readonly=True,
    )
    completed_by = fields.Many2one(
        'res.users',
        string='Completed By',
        readonly=True,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # NAVIGATION HELPERS
    # ═══════════════════════════════════════════════════════════════════════════
    next_note_id = fields.Many2one(
        'qaco.onboarding.note',
        string='Next Note',
        compute='_compute_navigation',
    )
    prev_note_id = fields.Many2one(
        'qaco.onboarding.note',
        string='Previous Note',
        compute='_compute_navigation',
    )
    note_position = fields.Char(
        string='Position',
        compute='_compute_note_position',
        help='Position in notebook (e.g., "3 of 10")',
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # METADATA
    # ═══════════════════════════════════════════════════════════════════════════
    tag_ids = fields.Many2many(
        'qaco.note.tag',
        'qaco_note_tag_rel',
        'note_id',
        'tag_id',
        string='Tags',
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'Medium'),
        ('3', 'High'),
    ], string='Priority', default='0')
    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # COMPUTED METHODS
    # ═══════════════════════════════════════════════════════════════════════════

    @api.depends('content')
    def _compute_plain_content(self):
        """Extract plain text from HTML content for search."""
        import re
        for record in self:
            if record.content:
                # Remove HTML tags
                plain = re.sub(r'<[^>]+>', '', record.content)
                # Normalize whitespace
                plain = ' '.join(plain.split())
                record.plain_content = plain[:500] if len(plain) > 500 else plain
            else:
                record.plain_content = ''

    @api.depends('draft_content', 'content', 'last_auto_save_date', 'last_save_date')
    def _compute_has_draft_recovery(self):
        """Check if there's a draft newer than the saved content."""
        for record in self:
            if not record.draft_content:
                record.has_draft_recovery = False
            elif not record.last_auto_save_date or not record.last_save_date:
                record.has_draft_recovery = bool(record.draft_content)
            else:
                record.has_draft_recovery = record.last_auto_save_date > record.last_save_date

    @api.depends('state')
    def _compute_is_completed(self):
        for record in self:
            record.is_completed = record.state == 'completed'

    def _compute_navigation(self):
        """Compute next and previous notes for navigation."""
        for record in self:
            siblings = self.search([
                ('notebook_id', '=', record.notebook_id.id),
            ], order='sequence, id')
            
            ids = siblings.ids
            current_idx = ids.index(record.id) if record.id in ids else -1
            
            if current_idx >= 0:
                record.prev_note_id = siblings[current_idx - 1] if current_idx > 0 else False
                record.next_note_id = siblings[current_idx + 1] if current_idx < len(ids) - 1 else False
            else:
                record.prev_note_id = False
                record.next_note_id = False

    def _compute_note_position(self):
        """Compute position string (e.g., '3 of 10')."""
        for record in self:
            siblings = self.search([
                ('notebook_id', '=', record.notebook_id.id),
            ], order='sequence, id')
            
            if record.id in siblings.ids:
                position = siblings.ids.index(record.id) + 1
                total = len(siblings)
                record.note_position = _('%d of %d') % (position, total)
            else:
                record.note_position = _('New')

    # ═══════════════════════════════════════════════════════════════════════════
    # SAVE & NEXT ACTIONS
    # ═══════════════════════════════════════════════════════════════════════════

    def action_save(self):
        """Save the current note."""
        self.ensure_one()
        self.write({
            'is_draft': False,
            'last_save_date': fields.Datetime.now(),
            'save_count': self.save_count + 1,
            'draft_content': False,  # Clear draft after save
        })
        if self.state == 'draft':
            self.state = 'in_progress'
        return True

    def action_save_and_next(self):
        """Save current note and navigate to next note."""
        self.ensure_one()
        
        # Save current note
        self.action_save()
        
        # Log the action
        self.message_post(
            body=_('Note saved. Navigating to next note.'),
            message_type='notification',
        )
        
        # Navigate to next note or create new one
        if self.next_note_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'qaco.onboarding.note',
                'res_id': self.next_note_id.id,
                'view_mode': 'form',
                'target': 'current',
                'context': {'form_view_initial_mode': 'edit'},
            }
        else:
            # Create new note at end of notebook
            return self.notebook_id.action_create_note()

    def action_save_and_previous(self):
        """Save current note and navigate to previous note."""
        self.ensure_one()
        
        # Save current note
        self.action_save()
        
        if self.prev_note_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'qaco.onboarding.note',
                'res_id': self.prev_note_id.id,
                'view_mode': 'form',
                'target': 'current',
                'context': {'form_view_initial_mode': 'edit'},
            }
        return {'type': 'ir.actions.act_window_close'}

    def action_save_draft(self):
        """Save as draft without marking complete."""
        self.ensure_one()
        self.write({
            'draft_content': self.content,
            'last_auto_save_date': fields.Datetime.now(),
            'is_draft': True,
        })
        return True

    def action_restore_draft(self):
        """Restore content from auto-saved draft."""
        self.ensure_one()
        if self.draft_content:
            self.write({
                'content': self.draft_content,
                'is_draft': True,
            })
            self.message_post(
                body=_('Draft content restored from %s') % self.last_auto_save_date,
                message_type='notification',
            )
        return True

    def action_mark_complete(self):
        """Mark note as completed."""
        self.ensure_one()
        self.action_save()
        self.write({
            'state': 'completed',
            'completed_date': fields.Datetime.now(),
            'completed_by': self.env.user.id,
        })
        return True

    def action_reopen(self):
        """Reopen a completed note."""
        self.ensure_one()
        self.write({
            'state': 'in_progress',
            'completed_date': False,
            'completed_by': False,
        })
        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # API METHODS FOR JAVASCRIPT
    # ═══════════════════════════════════════════════════════════════════════════

    @api.model
    def action_auto_save(self, note_id, content):
        """API method for JavaScript auto-save (called every 30 seconds)."""
        note = self.browse(note_id)
        if note.exists():
            note.write({
                'draft_content': content,
                'last_auto_save_date': fields.Datetime.now(),
                'is_draft': True,
            })
            return {
                'success': True,
                'timestamp': fields.Datetime.now().isoformat(),
                'note_id': note_id,
            }
        return {'success': False, 'error': 'Note not found'}

    @api.model
    def get_note_for_navigation(self, note_id, direction='next'):
        """Get next/previous note for navigation."""
        note = self.browse(note_id)
        if not note.exists():
            return {'error': 'Note not found'}
        
        if direction == 'next':
            target = note.next_note_id
        else:
            target = note.prev_note_id
        
        if target:
            return {
                'id': target.id,
                'name': target.name,
                'position': target.note_position,
                'has_draft': target.has_draft_recovery,
            }
        return {'id': False}

    @api.model
    def get_draft_recovery_info(self, note_id):
        """Get draft recovery information for a note."""
        note = self.browse(note_id)
        if note.exists() and note.has_draft_recovery:
            return {
                'has_draft': True,
                'draft_content': note.draft_content,
                'auto_save_date': note.last_auto_save_date.isoformat() if note.last_auto_save_date else None,
                'last_save_date': note.last_save_date.isoformat() if note.last_save_date else None,
            }
        return {'has_draft': False}

    # ═══════════════════════════════════════════════════════════════════════════
    # CRUD OVERRIDES
    # ═══════════════════════════════════════════════════════════════════════════

    @api.model_create_multi
    def create(self, vals_list):
        """Set sequence and initial state on create."""
        for vals in vals_list:
            if 'sequence' not in vals and vals.get('notebook_id'):
                notebook = self.env['qaco.onboarding.notebook'].browse(vals['notebook_id'])
                max_seq = max(notebook.note_ids.mapped('sequence') or [0])
                vals['sequence'] = max_seq + 10
        return super().create(vals_list)

    def write(self, vals):
        """Track content changes for draft detection."""
        if 'content' in vals and 'last_save_date' not in vals:
            vals['is_draft'] = True
        return super().write(vals)


class NoteTag(models.Model):
    """Tags for organizing notes."""
    _name = 'qaco.note.tag'
    _description = 'Note Tag'
    _order = 'name'

    name = fields.Char(
        string='Tag Name',
        required=True,
    )
    color = fields.Integer(
        string='Color',
        default=0,
    )
    note_ids = fields.Many2many(
        'qaco.onboarding.note',
        'qaco_note_tag_rel',
        'tag_id',
        'note_id',
        string='Notes',
    )
    note_count = fields.Integer(
        string='Note Count',
        compute='_compute_note_count',
    )

    def _compute_note_count(self):
        for record in self:
            record.note_count = len(record.note_ids)

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Tag name must be unique!'),
    ]
