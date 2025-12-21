/** @odoo-module */

import { stepUtils } from '@web_tour/tour_service/tour_utils';
import { patch } from '@web/core/utils/patch';

patch(stepUtils, {
    /* Make base odoo JS tests working */
    showAppsMenuItem() {
        return {
            edition: 'community',
            trigger: 'button.o_grid_apps_menu__button',
            auto: true,
            position: 'bottom',
        };
    },
});
