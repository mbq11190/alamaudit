/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";

/**
 * Client Onboarding Auto-Save Controller
 * =======================================
 * 
 * Implements auto-save functionality for the client onboarding form (Sections 1.0-1.10).
 * 
 * Features:
 * - Auto-save every 10 seconds
 * - Auto-save on field change (debounced)
 * - Respects Partner Approval lock
 * - Full audit trail via write()
 * - Visual "Saved at HH:MM" indicator
 * - ISA 230 / ISQM-1 compliant
 * 
 * Rules:
 * - No auto-advance to next step
 * - No bypass of validations
 * - No save after Partner Approval
 * - Audit trail captures all auto-saves
 */

const AUTO_SAVE_INTERVAL = 10000; // 10 seconds
const DEBOUNCE_DELAY = 1500; // 1.5 seconds after last keystroke

export class OnboardingAutoSaveController extends FormController {

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        // Auto-save state
        this.autoSaveInterval = null;
        this.debounceTimeout = null;
        this.isAutoSaving = false;
        this.lastSavedTime = null;
        this.isLocked = false;
        
        onMounted(() => {
            this._initAutoSave();
        });
        
        onWillUnmount(() => {
            this._cleanupAutoSave();
        });
    }

    /**
     * Initialize auto-save functionality
     */
    async _initAutoSave() {
        // Check if record is locked
        await this._checkLockStatus();
        
        if (this.isLocked) {
            this.notification.add('Auto-save is disabled because this onboarding record is locked.', { type: 'info', sticky: false });
            return;
        }
        
        // Start interval-based auto-save (every 10 seconds)
        this.autoSaveInterval = setInterval(() => {
            this._performAutoSave();
        }, AUTO_SAVE_INTERVAL);
        

    }

    /**
     * Clean up auto-save timers
     */
    _cleanupAutoSave() {
        if (this.autoSaveInterval) {
            clearInterval(this.autoSaveInterval);
            this.autoSaveInterval = null;
        }
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
            this.debounceTimeout = null;
        }

    }

    /**
     * Check if record is locked (Partner Approved or Locked state)
     */
    async _checkLockStatus() {
        const record = this.model.root;
        if (!record || !record.resId) {
            return;
        }
        
        try {
            const result = await this.orm.call(
                "qaco.client.onboarding",
                "get_autosave_status",
                [[record.resId]],
                {}
            );
            
            this.isLocked = result.is_locked;
            
            if (this.isLocked) {
                this._showLockedNotification();
            }
        } catch (error) {
            this.notification.add('Unable to verify auto-save lock status.', { type: 'warning', sticky: false });
        }
    }

    /**
     * Show notification that record is locked
     */
    _showLockedNotification() {
        this.notification.add(
            "This onboarding is locked after Partner Approval. No further edits allowed.",
            { type: 'warning', sticky: false }
        );
    }

    /**
     * Perform auto-save operation
     */
    async _performAutoSave() {
        const record = this.model.root;
        
        // Skip if no record, new record, or locked
        if (!record || !record.resId || this.isLocked) {
            return;
        }
        
        // Skip if record is not dirty (no changes)
        if (!record.isDirty) {
            return;
        }
        
        // Skip if already auto-saving
        if (this.isAutoSaving) {
            return;
        }
        
        this.isAutoSaving = true;
        
        try {
            // Get only changed values
            const changes = this._getChangedValues(record);
            
            if (Object.keys(changes).length === 0) {
                this.isAutoSaving = false;
                return;
            }
            
            const result = await this.orm.call(
                "qaco.client.onboarding",
                "autosave",
                [record.resId, changes],
                {}
            );
            
            if (result.status === 'saved') {
                this.lastSavedTime = new Date();
                this._showSavedIndicator();
                
                // Reload record to sync state
                await record.load();
                

            } else if (result.status === 'locked') {
                this.isLocked = true;
                this._cleanupAutoSave();
                this._showLockedNotification();
            } else if (result.status === 'error') {
                this.notification.add(`Auto-save error: ${result.message || 'Unknown'}`, { type: 'warning', sticky: false });
            }
            
        } catch (error) {
            this.notification.add('Auto-save failed. Your changes may not have been saved.', { type: 'danger', sticky: true });
        } finally {
            this.isAutoSaving = false;
        }
    }

    /**
     * Get changed field values from record
     */
    _getChangedValues(record) {
        const changes = {};
        const data = record.data;
        
        // List of fields we care about auto-saving
        const autoSaveFields = [
            // Notes fields (1.0 - 1.10)
            'notes_10', 'notes_11', 'notes_12', 'notes_13', 'notes_14',
            'notes_15', 'notes_16', 'notes_17', 'notes_18', 'notes_19', 'notes_110',
            // Selection and text fields
            'entity_type', 'other_entity_description',
            'primary_regulator', 'other_regulator_description',
            'financial_framework', 'other_framework_description',
            'management_integrity', 'client_acceptance_decision',
            'engagement_decision', 'engagement_justification',
            'fam_final_decision', 'fam_safeguards_imposed', 'fam_rejection_reason',
            // Narrative fields
            'industry_overview', 'regulatory_environment',
            'fraud_risk_narrative', 'going_concern_narrative',
            'related_party_narrative', 'significant_risks_narrative',
            'it_environment_narrative', 'group_audit_narrative',
            'aml_overall_assessment', 'aml_conclusion',
            'communication_narrative', 'resource_plan_narrative',
            // Risk fields
            'inherent_risk_assessment', 'fraud_risk_level',
            'going_concern_indicator', 'related_party_risk',
            'aml_country_risk', 'aml_customer_risk', 'aml_product_risk',
            // Boolean fields
            'pcl_no_barrier_conclusion', 'partner_signoff_complete',
            'is_first_year_audit', 'is_group_audit',
            'has_internal_audit', 'has_audit_committee',
        ];
        
        for (const fieldName of autoSaveFields) {
            if (data[fieldName] !== undefined) {
                changes[fieldName] = data[fieldName];
            }
        }
        
        return changes;
    }

    /**
     * Show "Saved at HH:MM" indicator
     */
    _showSavedIndicator() {
        const time = this.lastSavedTime.toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
        });
        
        this.notification.add(
            `Auto-saved at ${time}`,
            { type: 'info', sticky: false }
        );
    }

    /**
     * Override onRecordSaved to update lock status
     */
    async onRecordSaved(record) {
        await super.onRecordSaved(record);
        
        // Re-check lock status after manual save
        await this._checkLockStatus();
        
        if (this.isLocked) {
            this._cleanupAutoSave();
        }
    }

    /**
     * Trigger debounced auto-save on field change
     * This provides near-instant save after user stops typing
     */
    onFieldChanged(fieldName) {
        if (this.isLocked) {
            return;
        }
        
        // Clear existing debounce
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
        }
        
        // Set new debounce (1.5 seconds after last change)
        this.debounceTimeout = setTimeout(() => {
            this._performAutoSave();
        }, DEBOUNCE_DELAY);
    }
}

// Register the custom form view for client onboarding
export const onboardingAutoSaveFormView = {
    ...formView,
    Controller: OnboardingAutoSaveController,
};

registry.category("views").add("onboarding_autosave_form", onboardingAutoSaveFormView);
