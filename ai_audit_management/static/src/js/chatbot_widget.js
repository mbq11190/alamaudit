/** Minimal placeholder for chatbot trigger; extend with OWL component if desired. */
odoo.define('ai_audit_management.chatbot_widget', ['@odoo/owl'], function (owl) {
    "use strict";
    var Component = owl.Component;

    // ES5-compatible component definition
    function ChatbotWidget() {
        Component.apply(this, arguments);
    }
    ChatbotWidget.prototype = Object.create(Component.prototype);
    ChatbotWidget.prototype.constructor = ChatbotWidget;
    ChatbotWidget.template = 'ai_audit_management.ChatbotWidget';

    return ChatbotWidget;
});
