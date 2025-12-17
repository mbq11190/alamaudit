/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class PlanningDashboard extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            entity: 0,
            analytics: 0,
            materiality: 0,
            controls: 0,
            risk: 0,
            checklist: 0,
            overall: 0,
        });
        onWillStart(this.loadProgress.bind(this));
    }

    async loadProgress() {
        const resId = this.props.record.resId;
        if (!resId) {
            return;
        }
        const fields = [
            "entity_progress",
            "analytics_progress",
            "materiality_progress",
            "controls_progress",
            "risk_progress",
            "checklist_completion",
            "overall_progress",
        ];
        const [vals] = await this.rpc("/web/dataset/call_kw", {
            model: "audit.planning",
            method: "read",
            args: [[resId], fields],
            kwargs: {},
        });
        this.state.entity = vals.entity_progress || 0;
        this.state.analytics = vals.analytics_progress || 0;
        this.state.materiality = vals.materiality_progress || 0;
        this.state.controls = vals.controls_progress || 0;
        this.state.risk = vals.risk_progress || 0;
        this.state.checklist = vals.checklist_completion || 0;
        this.state.overall = vals.overall_progress || 0;
    }

    progressClass(value) {
        if (value >= 90) return "bg-success";
        if (value >= 60) return "bg-info";
        if (value >= 30) return "bg-warning";
        return "bg-danger";
    }
}

PlanningDashboard.template = "audit_planning.PlanningDashboard";

registry.category("fields" ).add("planning_dashboard", {
    component: PlanningDashboard,
});

export default PlanningDashboard;
