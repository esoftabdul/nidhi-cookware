// Copyright (c) 2025, Abdul Mannan Shaikh	 and contributors
// For license information, please see license.txt

frappe.ui.form.on("Quality Inspection Request", {
    refresh(frm) {

    },
});
frappe.ui.form.on("Quality Inspection Request Item", {
    set_parameters: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (!row.quality_inspection_template) {
            frappe.msgprint("Please select a Quality Inspection Template first.");
            return;
        }

        // Fetch template parameters
        frappe.call({
            method: "frappe.client.get",
            args: {
                doctype: "Quality Inspection Template",
                name: row.quality_inspection_template
            },
            callback: function (r) {
                if (r.message) {
                    let template = r.message;
                    console.log(r);

                    let d = new frappe.ui.Dialog({
                        title: "Set Parameters",
                        fields: [
                            {
                                fieldname: "parameters",
                                fieldtype: "Table",
                                label: "Inspection Parameters",
                                cannot_add_rows: true,
                                in_place_edit: true,
                                data: [],
                                fields: [
                                    {
                                        fieldtype: "Data",
                                        fieldname: "specification",
                                        label: "Specification",
                                        read_only: 1,
                                        in_list_view: 1,
                                    },
                                    {
                                        fieldtype: "Float",
                                        fieldname: "min_value",
                                        label: "Min Value",
                                        in_list_view: 1,
                                        read_only: 1
                                    },
                                    {
                                        fieldtype: "Float",
                                        fieldname: "max_value",
                                        label: "Max Value",
                                        read_only: 1,
                                        in_list_view: 1,
                                    },
                                    {
                                        fieldtype: "Float",
                                        fieldname: "reading_value",
                                        label: "Reading Value",
                                        in_list_view: 1,
                                    },
                                    {
                                        fieldtype: "Check",
                                        fieldname: "is_numeric",
                                        label: "Is Numeric",
                                        in_list_view: 1,
                                    },
                                    {
                                        fieldtype: "Select",
                                        fieldname: "status",
                                        label: "Status",
                                        options: ["Accepted", "Rejected"],
                                        read_only: 1,
                                        in_list_view: 1,
                                    }
                                ]
                            }
                        ],
                        primary_action_label: "Apply Parameters",
                        primary_action(values) {
                            // assign dialog data to child row
                            row.inspection_parameters = values.parameters;
                            d.hide();
                            frm.refresh_field("inspection_item");
                        }
                    });

                    // populate data from template readings
                    if (template?.item_quality_inspection_parameter) {
                        d.fields_dict.parameters.df.data = template.item_quality_inspection_parameter.map(r => {
                            return {
                                specification: r.specification,
                                min_value: r.min_value,
                                max_value: r.max_value,
                                is_numeric: r.numeric,
                                status: "Accepted"
                            };
                        });
                        d.fields_dict.parameters.refresh();
                    }

                    d.show();
                }
            }
        });
    }
});
