odoo.define('qaco_audit.audit_engagement_js', function (require) {
    'use strict';

    const FormController = require('web.FormController');

    FormController.include({
        _onFieldChanged: function (event) {
            if (event.data.changes && event.data.changes.risk_rating === 'very_high') {
                this.displayNotification({
                    title: 'Very High Risk Alert',
                    message: 'EQCR approval and partner oversight are mandatory for this engagement.',
                    type: 'danger',
                });
            }
            return this._super.apply(this, arguments);
        },
    });
});