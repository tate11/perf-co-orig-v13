odoo.define('pcp_mrp.BackAction', function (require) {
    let core = require('web.core');

    function HistoryBack(parent) {
        if (parent.currentDialogController) {
            parent._closeDialog();
        } else {
            var length = parent.controllerStack.length;
            if (length > 1) {
                parent._restoreController(parent.controllerStack[length - 2]);
            }
        }
    }

    core.action_registry.add('history_back_action', HistoryBack);
});
