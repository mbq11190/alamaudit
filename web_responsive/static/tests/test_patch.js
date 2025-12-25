/* Copyright 2021 ITerra - Sergey Shebanin
 * Copyright 2025 Carlos Lopez - Tecnativa
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
odoo.define(
    "web_responsive.test_patch",
    ["require"],
    function (require) {
        "use strict";

        // Optional modules - only apply patches if available (allows running in environments without web_tour)
        let stepUtils = null;
        let patch = null;
        try {
            const mod = require("@web_tour/tour_service/tour_utils");
            stepUtils = mod && mod.stepUtils ? mod.stepUtils : mod;
        } catch (e) {
            console.warn("Optional module @web_tour/tour_service/tour_utils not available: skipping patch.");
        }
        try {
            const mod2 = require("@web/core/utils/patch");
            patch = mod2 && mod2.patch ? mod2.patch : mod2;
        } catch (e) {
            console.warn("Optional module @web/core/utils/patch not available: skipping patch.");
        }

        if (stepUtils && patch) {
            patch(stepUtils, {
                /* Make base odoo JS tests working */
                showAppsMenuItem() {
                    return {
                        edition: "community",
                        trigger: "button.o_grid_apps_menu__button",
                        auto: true,
                        position: "bottom",
                    };
                },
            });
        }
    }
);
