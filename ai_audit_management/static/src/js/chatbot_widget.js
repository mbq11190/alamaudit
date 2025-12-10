/** Minimal placeholder for chatbot trigger; extend with OWL component if desired. */
odoo.define('ai_audit_management.chatbot_widget', function (require) {
    "use strict";
    const { Component } = require('@odoo/owl');

    class ChatbotWidget extends Component {
        static template = 'ai_audit_management.ChatbotWidget';
    }

    return ChatbotWidget;
});
