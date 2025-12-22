/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

/**
 * Auto-Save Manager for Onboarding Notes
 * Handles:
 * - Auto-save every 30 seconds
 * - Draft content persistence
 * - Save & Next navigation
 * - Session recovery
 */
class AutoSaveManager {
    constructor(env, options = {}) {
        this.env = env;
        this.orm = env.services.orm;
        this.notification = env.services.notification;
        this.action = env.services.action;
        
        // Configuration
        this.autoSaveInterval = options.autoSaveInterval || 30000; // 30 seconds
        this.modelName = 'qaco.onboarding.note';
        
        // State
        this.intervalId = null;
        this.isDirty = false;
        this.lastSavedContent = null;
        this.currentRecordId = null;
        this.isAutoSaving = false;
    }

    /**
     * Start auto-save timer for a specific record
     */
    start(recordId, initialContent = null) {
        this.stop(); // Clear any existing interval
        
        this.currentRecordId = recordId;
        this.lastSavedContent = initialContent;
        this.isDirty = false;
        
        if (recordId && recordId !== 'new') {
            this.intervalId = setInterval(() => {
                this.autoSave();
            }, this.autoSaveInterval);

        }
    }

    /**
     * Stop auto-save timer
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    /**
     * Mark content as changed
     */
    markDirty(currentContent) {
        if (currentContent !== this.lastSavedContent) {
            this.isDirty = true;
        }
    }

    /**
     * Perform auto-save operation
     */
    async autoSave() {
        if (!this.isDirty || !this.currentRecordId || this.isAutoSaving) {
            return;
        }

        this.isAutoSaving = true;
        
        try {
            const result = await this.orm.call(
                this.modelName,
                'auto_save_draft',
                [[this.currentRecordId]],
                {}
            );
            
            if (result && result.success) {
                this.isDirty = false;
                this.lastSavedContent = result.draft_content;
                
                this.notification.add(
                    "Draft auto-saved",
                    { type: 'info', sticky: false }
                );

            }
        } catch (error) {
            this.notification.add(
                "Auto-save failed. Your changes may not be saved.",
                { type: 'warning', sticky: true }
            );
        } finally {
            this.isAutoSaving = false;
        }
    }

    /**
     * Force immediate save
     */
    async forceSave() {
        if (this.currentRecordId) {
            this.isDirty = true; // Force dirty flag
            await this.autoSave();
        }
    }

    /**
     * Save and navigate to next note
     */
    async saveAndNext() {
        if (!this.currentRecordId) {
            return null;
        }

        try {
            // First, force save current content
            await this.forceSave();
            
            // Then call save_and_next action
            const result = await this.orm.call(
                this.modelName,
                'action_save_and_next',
                [[this.currentRecordId]],
                {}
            );
            
            if (result && result.res_id) {
                this.notification.add(
                    "Saved! Moving to next note...",
                    { type: 'success', sticky: false }
                );
                
                return result;
            } else if (result && result.type === 'ir.actions.client') {
                // No next note - show notification
                this.notification.add(
                    "This is the last note in the notebook",
                    { type: 'info', sticky: false }
                );
            }
            
            return result;
        } catch (error) {
            this.notification.add(
                "Error saving note. Please try again.",
                { type: 'danger', sticky: true }
            );
            return null;
        }
    }

    /**
     * Restore draft content
     */
    async restoreDraft() {
        if (!this.currentRecordId) {
            return null;
        }

        try {
            const result = await this.orm.call(
                this.modelName,
                'action_restore_draft',
                [[this.currentRecordId]],
                {}
            );
            
            if (result) {
                this.notification.add(
                    "Draft restored successfully",
                    { type: 'success', sticky: false }
                );
            }
            
            return result;
        } catch (error) {
            this.notification.add(
                "Error restoring draft",
                { type: 'danger', sticky: true }
            );
            return null;
        }
    }
}

/**
 * Patch FormController to add auto-save functionality for notes
 */
patch(FormController.prototype, {
    setup() {
        super.setup();
        
        // Only activate for qaco.onboarding.note model
        if (this.props.resModel === 'qaco.onboarding.note') {
            this.autoSaveManager = new AutoSaveManager(this.env);
            
            onMounted(() => {
                this._initializeAutoSave();
            });
            
            onWillUnmount(() => {
                this._cleanupAutoSave();
            });
        }
    },

    /**
     * Initialize auto-save when form is mounted
     */
    _initializeAutoSave() {
        if (!this.autoSaveManager) return;
        
        const record = this.model.root;
        if (record && record.resId) {
            const content = record.data.content || '';
            this.autoSaveManager.start(record.resId, content);
            
            // Watch for content changes
            this._setupContentWatcher(record);
        }
    },

    /**
     * Set up watcher for content field changes
     */
    _setupContentWatcher(record) {
        if (!this.autoSaveManager) return;
        
        // Monitor field changes
        const originalOnUpdate = record.onUpdate;
        record.onUpdate = (data) => {
            if (data && data.content !== undefined) {
                this.autoSaveManager.markDirty(data.content);
            }
            if (originalOnUpdate) {
                return originalOnUpdate.call(record, data);
            }
        };
    },

    /**
     * Cleanup auto-save on unmount
     */
    _cleanupAutoSave() {
        if (this.autoSaveManager) {
            // Force save before leaving
            this.autoSaveManager.forceSave().then(() => {
                this.autoSaveManager.stop();
            });
        }
    },

    /**
     * Override save to update auto-save state
     */
    async save(params) {
        const result = await super.save(params);
        
        if (this.autoSaveManager && result) {
            const record = this.model.root;
            if (record) {
                this.autoSaveManager.lastSavedContent = record.data.content;
                this.autoSaveManager.isDirty = false;
            }
        }
        
        return result;
    },
});

/**
 * Auto-Save Status Widget Component
 * Shows auto-save status indicator in the form
 */
export class AutoSaveStatusWidget extends Component {
    static template = "qaco_client_onboarding.AutoSaveStatus";
    static props = {
        record: { type: Object },
    };

    setup() {
        this.state = useState({
            lastSaved: null,
            isSaving: false,
            hasDraft: false,
        });
        
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        onMounted(() => {
            this._checkDraftStatus();
        });
    }

    async _checkDraftStatus() {
        const recordId = this.props.record.resId;
        if (!recordId) return;
        
        try {
            const record = await this.orm.read(
                'qaco.onboarding.note',
                [recordId],
                ['is_draft', 'last_save_date', 'draft_content']
            );
            
            if (record && record.length > 0) {
                this.state.hasDraft = record[0].is_draft;
                this.state.lastSaved = record[0].last_save_date;
            }
        } catch (error) {
            this.notification?.add('Could not check draft status.', { type: 'warning' });
        }
    }

    get statusText() {
        if (this.state.isSaving) {
            return "Saving...";
        }
        if (this.state.hasDraft) {
            return "Draft available";
        }
        if (this.state.lastSaved) {
            return `Last saved: ${this.state.lastSaved}`;
        }
        return "Auto-save enabled";
    }

    get statusClass() {
        if (this.state.isSaving) {
            return "text-warning";
        }
        if (this.state.hasDraft) {
            return "text-info";
        }
        return "text-muted";
    }
}

/**
 * Save & Next Button Widget
 * Custom button that triggers save and navigation
 */
export class SaveNextButton extends Component {
    static template = "qaco_client_onboarding.SaveNextButton";
    static props = {
        record: { type: Object },
    };

    setup() {
        this.state = useState({
            isLoading: false,
        });
        
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
    }

    async onSaveAndNext() {
        if (this.state.isLoading) return;
        
        this.state.isLoading = true;
        
        try {
            const recordId = this.props.record.resId;
            if (!recordId) {
                this.notification.add(
                    "Please save the record first",
                    { type: 'warning' }
                );
                return;
            }
            
            const result = await this.orm.call(
                'qaco.onboarding.note',
                'action_save_and_next',
                [[recordId]],
                {}
            );
            
            if (result && result.type) {
                await this.action.doAction(result);
            }
        } catch (error) {
            this.notification.add(
                "Error navigating to next note",
                { type: 'danger' }
            );
        } finally {
            this.state.isLoading = false;
        }
    }
}

// Register widgets in the registry
registry.category("fields").add("auto_save_status", AutoSaveStatusWidget);
registry.category("fields").add("save_next_button", SaveNextButton);

// Export for external use
export { AutoSaveManager };
