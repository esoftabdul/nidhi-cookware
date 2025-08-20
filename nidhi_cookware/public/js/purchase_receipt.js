frappe.ui.form.on('Purchase Receipt', {
    refresh: function (frm) {
        // if (frm.doc.docstatus === 1) {
        frm.add_custom_button(__('Quality Inspection Req'), function () {
            frappe.call({
                method: "nidhi_cookware.api.create_quality_inspection_request",
                args: {
                    doctype: frm.doctype,
                    docname: frm.doc.name
                },
                callback: function (r) {
                    if (!r.exc && r.message) {
                        frappe.set_route("Form", "Quality Inspection Request", r.message);
                    }
                }
            });

        }, __('Create'));
        // }
    }
});
