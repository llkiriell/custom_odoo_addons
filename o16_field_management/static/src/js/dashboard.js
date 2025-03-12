odoo.define('field_management.dashboard', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var QWeb = core.qweb;

    var FieldManagementDashboard = AbstractAction.extend({
        template: 'field_management.dashboard',
        events: {
            'click .o_dashboard_action': '_onDashboardActionClick',
        },

        init: function(parent, action) {
            this._super.apply(this, arguments);
            this.action = action;
        },

        start: function() {
            return this._super.apply(this, arguments);
        },

        _onDashboardActionClick: function(ev) {
            ev.preventDefault();
            var $action = $(ev.currentTarget);
            this.do_action($action.data('action-id'));
        },
    });

    core.action_registry.add('field_management_dashboard', FieldManagementDashboard);

    return FieldManagementDashboard;
}); 