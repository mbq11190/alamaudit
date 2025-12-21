/** @odoo-module */

import { patch } from '@web/core/utils/patch';
import { stepUtils } from '@web_tour/tour_service/tour_utils';

/* Make base odoo JS tests working */
patch(stepUtils, {
    showAppsMenuItem() {
        return {
            edition: 'community',
            trigger: '.o_navbar_apps_menu',
            auto: true,
            position: 'bottom',
        };
    },
});
