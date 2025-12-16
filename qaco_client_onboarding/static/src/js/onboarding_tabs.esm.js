/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormRenderer } from "@web/views/form/form_renderer";
import { useService } from "@web/core/utils/hooks";
import { onMounted, onPatched } from "@odoo/owl";

const superSetup = FormRenderer.prototype.setup;

function isDebugAssets() {
    try {
        return /(^|[?&])debug=assets([&#]|$)/.test(window.location.search || "");
    } catch (e) {
        return false;
    }
}

function debugLog(...args) {
    if (isDebugAssets()) {
        // eslint-disable-next-line no-console
        console.log(...args);
    }
}

function parseSectionIndexFromLabel(label) {
    // Expects labels like "1.5 Independence & Ethics" or "1.10 Audit Trail"
    const match = String(label || "").trim().match(/^1\.(\d{1,2})\b/);
    if (!match) {
        return null;
    }
    const n = parseInt(match[1], 10);
    return Number.isFinite(n) ? n : null;
}

function statusToClass(status) {
    if (status === "green") return "o_onboarding_tab--complete";
    if (status === "amber") return "o_onboarding_tab--inprogress";
    return "";
}

function getCachedSectionIndex(linkEl) {
    const cached = linkEl && linkEl.dataset && linkEl.dataset.qacoSectionIndex;
    if (cached) {
        const n = parseInt(cached, 10);
        return Number.isFinite(n) ? n : null;
    }
    const idx = parseSectionIndexFromLabel(linkEl && linkEl.textContent);
    if (idx && linkEl && linkEl.dataset) {
        linkEl.dataset.qacoSectionIndex = String(idx);
    }
    return idx;
}

patch(FormRenderer.prototype, "qaco_client_onboarding.onboarding_tabs", {
    setup() {
        superSetup.call(this);
        try {
            this.notification = useService("notification");
        } catch (e) {
            this.notification = null;
            debugLog("[qaco_client_onboarding] notification service unavailable", e);
        }
        this.__qacoActivatedSection = null;
        onMounted(() => {
            try {
                this._qacoWireOnboardingTabGuards();
                this._qacoApplyOnboardingTabStates();
                this._qacoActivateRequestedSection();
            } catch (e) {
                debugLog("[qaco_client_onboarding] onboarding tab setup failed", e);
            }
        });
        onPatched(() => {
            try {
                this._qacoApplyOnboardingTabStates();
                this._qacoActivateRequestedSection();
            } catch (e) {
                debugLog("[qaco_client_onboarding] onboarding tab update failed", e);
            }
        });
    },

    _qacoGetContext() {
        // Action context is typically merged into props.context in form views.
        return (this.props && this.props.context) || {};
    },

    _qacoGetSectionStatus(sectionIndex) {
        const record = this.props && this.props.record;
        const data = record && record.data;
        if (!data) return "red";
        const field = `section${sectionIndex}_status`;
        return data[field] || "red";
    },

    _qacoUnlockedMaxSection() {
        // Sequential gating: unlock tabs up to the first non-green section + 1.
        for (let i = 1; i <= 10; i++) {
            if (this._qacoGetSectionStatus(i) !== "green") {
                return i; // current incomplete
            }
        }
        return 10;
    },

    _qacoNotebookRoot() {
        return this.el && this.el.querySelector(".o_onboarding_tabs");
    },

    _qacoApplyOnboardingTabStates() {
        const root = this._qacoNotebookRoot();
        if (!root) return;

        const unlockedMax = this._qacoUnlockedMaxSection();
        const links = root.querySelectorAll(".nav.nav-tabs .nav-link");
        for (const link of links) {
            const idx = getCachedSectionIndex(link);
            if (!idx) continue;

            link.classList.remove(
                "o_onboarding_tab--complete",
                "o_onboarding_tab--inprogress",
                "o_onboarding_tab--locked"
            );

            link.classList.add(statusToClass(this._qacoGetSectionStatus(idx)));

            if (idx > unlockedMax) {
                link.classList.add("o_onboarding_tab--locked");
                link.setAttribute("aria-disabled", "true");
            } else {
                link.removeAttribute("aria-disabled");
            }
        }
    },

    _qacoActivateRequestedSection() {
        const root = this._qacoNotebookRoot();
        if (!root) return;

        const ctx = this._qacoGetContext();
        const target = parseInt(ctx.onboarding_active_section, 10);
        if (!target || target < 1 || target > 10) return;

        const active = root.querySelector(".nav.nav-tabs .nav-link.active");
        const activeIdx = active ? getCachedSectionIndex(active) : null;
        if (activeIdx === target) {
            this.__qacoActivatedSection = target;
            return;
        }
        if (this.__qacoActivatedSection === target) return;

        const links = root.querySelectorAll(".nav.nav-tabs .nav-link");
        for (const link of links) {
            const idx = getCachedSectionIndex(link);
            if (idx === target) {
                // Avoid endless loops: only click if not already active.
                if (!link.classList.contains("active")) {
                    link.click();
                }
                this.__qacoActivatedSection = target;
                break;
            }
        }
    },

    _qacoWireOnboardingTabGuards() {
        const root = this._qacoNotebookRoot();
        if (!root || root.__qacoWired) return;
        root.__qacoWired = true;

        root.addEventListener(
            "click",
            (ev) => {
                if (typeof HTMLElement === "undefined") return;
                const target = ev.target;
                if (!(target instanceof HTMLElement)) return;
                const link = target.closest(".nav.nav-tabs .nav-link");
                if (!link) return;

                const idx = getCachedSectionIndex(link);
                if (!idx) return;

                const unlockedMax = this._qacoUnlockedMaxSection();
                if (idx > unlockedMax) {
                    ev.preventDefault();
                    ev.stopPropagation();
                    if (this.notification && this.notification.add) {
                        this.notification.add(
                            "Complete the current section before moving ahead.",
                            { type: "warning" }
                        );
                    } else {
                        debugLog("[qaco_client_onboarding] blocked tab navigation", idx);
                    }
                }
            },
            true
        );
    },
});
