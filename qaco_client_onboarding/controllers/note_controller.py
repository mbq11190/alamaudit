# -*- coding: utf-8 -*-

import json
import logging

from odoo import http
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class NoteController(http.Controller):
    """
    Controller for Onboarding Note auto-save and navigation operations.
    Provides REST-like endpoints for the JavaScript widget.
    """

    # =========================================================================
    # AUTO-SAVE ENDPOINTS
    # =========================================================================

    @http.route('/qaco/note/auto_save', type='json', auth='user', methods=['POST'])
    def auto_save_note(self, note_id, draft_content):
        """
        Auto-save draft content for a note.
        Called periodically by the JavaScript widget (every 30 seconds).
        
        Args:
            note_id (int): The ID of the note to save
            draft_content (str): The current content to save as draft
            
        Returns:
            dict: Success status and saved content info
        """
        try:
            if not note_id:
                return {'success': False, 'error': 'Missing note_id'}
            
            note = request.env['qaco.onboarding.note'].sudo().browse(int(note_id))
            
            if not note.exists():
                return {'success': False, 'error': 'Note not found'}
            
            # Check user has write access
            note.check_access_rights('write')
            note.check_access_rule('write')
            
            # Perform auto-save
            result = note.auto_save_draft(draft_content)
            
            _logger.info(
                "Auto-saved draft for note %s by user %s",
                note_id, request.env.user.id
            )
            
            return result
            
        except Exception as e:
            _logger.exception("Error auto-saving note %s: %s", note_id, str(e))
            return {'success': False, 'error': str(e)}

    @http.route('/qaco/note/save_draft', type='json', auth='user', methods=['POST'])
    def save_draft(self, note_id):
        """
        Explicitly save current content as draft.
        
        Args:
            note_id (int): The ID of the note
            
        Returns:
            dict: Action result or error
        """
        try:
            if not note_id:
                return {'success': False, 'error': 'Missing note_id'}
            
            note = request.env['qaco.onboarding.note'].browse(int(note_id))
            
            if not note.exists():
                return {'success': False, 'error': 'Note not found'}
            
            result = note.action_save_draft()
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            _logger.exception("Error saving draft for note %s: %s", note_id, str(e))
            return {'success': False, 'error': str(e)}

    @http.route('/qaco/note/restore_draft', type='json', auth='user', methods=['POST'])
    def restore_draft(self, note_id):
        """
        Restore draft content to main content field.
        
        Args:
            note_id (int): The ID of the note
            
        Returns:
            dict: Restored content or error
        """
        try:
            if not note_id:
                return {'success': False, 'error': 'Missing note_id'}
            
            note = request.env['qaco.onboarding.note'].browse(int(note_id))
            
            if not note.exists():
                return {'success': False, 'error': 'Note not found'}
            
            if not note.is_draft:
                return {'success': False, 'error': 'No draft available to restore'}
            
            result = note.action_restore_draft()
            
            return {
                'success': True,
                'content': note.content,
                'result': result
            }
            
        except Exception as e:
            _logger.exception("Error restoring draft for note %s: %s", note_id, str(e))
            return {'success': False, 'error': str(e)}

    @http.route('/qaco/note/clear_draft', type='json', auth='user', methods=['POST'])
    def clear_draft(self, note_id):
        """
        Clear draft content without restoring.
        
        Args:
            note_id (int): The ID of the note
            
        Returns:
            dict: Success status
        """
        try:
            if not note_id:
                return {'success': False, 'error': 'Missing note_id'}
            
            note = request.env['qaco.onboarding.note'].browse(int(note_id))
            
            if not note.exists():
                return {'success': False, 'error': 'Note not found'}
            
            note.action_discard_draft()
            
            return {'success': True}
            
        except Exception as e:
            _logger.exception("Error clearing draft for note %s: %s", note_id, str(e))
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # SAVE & NEXT NAVIGATION ENDPOINTS
    # =========================================================================

    @http.route('/qaco/note/save_and_next', type='json', auth='user', methods=['POST'])
    def save_and_next(self, note_id):
        """
        Save current note and navigate to next note in sequence.
        
        Args:
            note_id (int): The ID of the current note
            
        Returns:
            dict: Action to navigate to next note or notification
        """
        try:
            if not note_id:
                return {'success': False, 'error': 'Missing note_id'}
            
            note = request.env['qaco.onboarding.note'].browse(int(note_id))
            
            if not note.exists():
                return {'success': False, 'error': 'Note not found'}
            
            result = note.action_save_and_next()
            
            return {
                'success': True,
                'action': result,
                'next_note_id': result.get('res_id') if result else None
            }
            
        except Exception as e:
            _logger.exception("Error in save_and_next for note %s: %s", note_id, str(e))
            return {'success': False, 'error': str(e)}

    @http.route('/qaco/note/get_next', type='json', auth='user', methods=['POST'])
    def get_next_note(self, note_id):
        """
        Get the next note in sequence without saving.
        
        Args:
            note_id (int): The ID of the current note
            
        Returns:
            dict: Next note info or null if no next note
        """
        try:
            if not note_id:
                return {'success': False, 'error': 'Missing note_id'}
            
            note = request.env['qaco.onboarding.note'].browse(int(note_id))
            
            if not note.exists():
                return {'success': False, 'error': 'Note not found'}
            
            if not note.parent_notebook_id:
                return {'success': True, 'next_note': None}
            
            next_note = request.env['qaco.onboarding.note'].search([
                ('parent_notebook_id', '=', note.parent_notebook_id.id),
                ('sequence', '>', note.sequence)
            ], order='sequence asc', limit=1)
            
            if next_note:
                return {
                    'success': True,
                    'next_note': {
                        'id': next_note.id,
                        'title': next_note.title,
                        'sequence': next_note.sequence
                    }
                }
            
            return {'success': True, 'next_note': None}
            
        except Exception as e:
            _logger.exception("Error getting next note for %s: %s", note_id, str(e))
            return {'success': False, 'error': str(e)}

    @http.route('/qaco/note/get_previous', type='json', auth='user', methods=['POST'])
    def get_previous_note(self, note_id):
        """
        Get the previous note in sequence.
        
        Args:
            note_id (int): The ID of the current note
            
        Returns:
            dict: Previous note info or null if no previous note
        """
        try:
            if not note_id:
                return {'success': False, 'error': 'Missing note_id'}
            
            note = request.env['qaco.onboarding.note'].browse(int(note_id))
            
            if not note.exists():
                return {'success': False, 'error': 'Note not found'}
            
            if not note.parent_notebook_id:
                return {'success': True, 'previous_note': None}
            
            prev_note = request.env['qaco.onboarding.note'].search([
                ('parent_notebook_id', '=', note.parent_notebook_id.id),
                ('sequence', '<', note.sequence)
            ], order='sequence desc', limit=1)
            
            if prev_note:
                return {
                    'success': True,
                    'previous_note': {
                        'id': prev_note.id,
                        'title': prev_note.title,
                        'sequence': prev_note.sequence
                    }
                }
            
            return {'success': True, 'previous_note': None}
            
        except Exception as e:
            _logger.exception("Error getting previous note for %s: %s", note_id, str(e))
            return {'success': False, 'error': str(e)}

    @http.route('/qaco/note/navigate', type='json', auth='user', methods=['POST'])
    def navigate_to_note(self, note_id):
        """
        Get action to navigate to a specific note.
        
        Args:
            note_id (int): The ID of the note to navigate to
            
        Returns:
            dict: Action to open the note form
        """
        try:
            if not note_id:
                return {'success': False, 'error': 'Missing note_id'}
            
            note = request.env['qaco.onboarding.note'].browse(int(note_id))
            
            if not note.exists():
                return {'success': False, 'error': 'Note not found'}
            
            action = {
                'type': 'ir.actions.act_window',
                'res_model': 'qaco.onboarding.note',
                'view_mode': 'form',
                'res_id': note.id,
                'target': 'current',
            }
            
            return {'success': True, 'action': action}
            
        except Exception as e:
            _logger.exception("Error navigating to note %s: %s", note_id, str(e))
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # NOTEBOOK ENDPOINTS
    # =========================================================================

    @http.route('/qaco/notebook/get_notes', type='json', auth='user', methods=['POST'])
    def get_notebook_notes(self, notebook_id):
        """
        Get all notes for a notebook with their status.
        
        Args:
            notebook_id (int): The ID of the notebook
            
        Returns:
            dict: List of notes with status info
        """
        try:
            if not notebook_id:
                return {'success': False, 'error': 'Missing notebook_id'}
            
            notebook = request.env['qaco.onboarding.notebook'].browse(int(notebook_id))
            
            if not notebook.exists():
                return {'success': False, 'error': 'Notebook not found'}
            
            notes = []
            for note in notebook.note_ids.sorted('sequence'):
                notes.append({
                    'id': note.id,
                    'title': note.title,
                    'sequence': note.sequence,
                    'is_draft': note.is_draft,
                    'has_content': bool(note.content),
                    'last_save_date': note.last_save_date.isoformat() if note.last_save_date else None
                })
            
            return {
                'success': True,
                'notes': notes,
                'total_count': len(notes),
                'draft_count': sum(1 for n in notes if n['is_draft']),
                'completed_count': sum(1 for n in notes if n['has_content'] and not n['is_draft'])
            }
            
        except Exception as e:
            _logger.exception("Error getting notes for notebook %s: %s", notebook_id, str(e))
            return {'success': False, 'error': str(e)}

    @http.route('/qaco/notebook/progress', type='json', auth='user', methods=['POST'])
    def get_notebook_progress(self, notebook_id):
        """
        Get progress statistics for a notebook.
        
        Args:
            notebook_id (int): The ID of the notebook
            
        Returns:
            dict: Progress statistics
        """
        try:
            if not notebook_id:
                return {'success': False, 'error': 'Missing notebook_id'}
            
            notebook = request.env['qaco.onboarding.notebook'].browse(int(notebook_id))
            
            if not notebook.exists():
                return {'success': False, 'error': 'Notebook not found'}
            
            return {
                'success': True,
                'progress': {
                    'total': notebook.note_count,
                    'completed': notebook.completed_notes,
                    'draft': notebook.draft_notes,
                    'percentage': notebook.progress_percentage
                }
            }
            
        except Exception as e:
            _logger.exception("Error getting progress for notebook %s: %s", notebook_id, str(e))
            return {'success': False, 'error': str(e)}

    # =========================================================================
    # SESSION PERSISTENCE ENDPOINTS
    # =========================================================================

    @http.route('/qaco/note/session/save', type='json', auth='user', methods=['POST'])
    def save_session_state(self, notebook_id, current_note_id, scroll_position=0):
        """
        Save the current session state for later recovery.
        Stores in user's browser localStorage via JavaScript.
        
        Args:
            notebook_id (int): Current notebook ID
            current_note_id (int): Current note being edited
            scroll_position (int): Current scroll position
            
        Returns:
            dict: Session state to be stored client-side
        """
        try:
            session_state = {
                'notebook_id': notebook_id,
                'current_note_id': current_note_id,
                'scroll_position': scroll_position,
                'user_id': request.env.user.id,
                'timestamp': str(request.env.cr.now()),
            }
            
            return {
                'success': True,
                'session_state': session_state
            }
            
        except Exception as e:
            _logger.exception("Error saving session state: %s", str(e))
            return {'success': False, 'error': str(e)}

    @http.route('/qaco/note/session/restore', type='json', auth='user', methods=['POST'])
    def restore_session_state(self, session_state):
        """
        Validate and return action to restore previous session.
        
        Args:
            session_state (dict): Previously saved session state
            
        Returns:
            dict: Action to restore session or error
        """
        try:
            if not session_state:
                return {'success': False, 'error': 'No session state provided'}
            
            # Validate user
            if session_state.get('user_id') != request.env.user.id:
                return {'success': False, 'error': 'Session belongs to different user'}
            
            note_id = session_state.get('current_note_id')
            if not note_id:
                return {'success': False, 'error': 'No note ID in session'}
            
            note = request.env['qaco.onboarding.note'].browse(int(note_id))
            
            if not note.exists():
                return {'success': False, 'error': 'Note no longer exists'}
            
            action = {
                'type': 'ir.actions.act_window',
                'res_model': 'qaco.onboarding.note',
                'view_mode': 'form',
                'res_id': note.id,
                'target': 'current',
                'context': {
                    'restore_scroll_position': session_state.get('scroll_position', 0)
                }
            }
            
            return {
                'success': True,
                'action': action,
                'note_title': note.title,
                'notebook_name': note.parent_notebook_id.name if note.parent_notebook_id else None
            }
            
        except Exception as e:
            _logger.exception("Error restoring session state: %s", str(e))
            return {'success': False, 'error': str(e)}
