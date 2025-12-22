/** @odoo-module */
import { Component } from '@odoo/owl';

// ES5-compatible component definition
function ChatbotWidget() {
    Component.apply(this, arguments);
}
ChatbotWidget.prototype = Object.create(Component.prototype);
ChatbotWidget.prototype.constructor = ChatbotWidget;
ChatbotWidget.template = 'ai_audit_management.ChatbotWidget';

// Expose widget as a global for non-module environments
window.ChatbotWidget = ChatbotWidget;
