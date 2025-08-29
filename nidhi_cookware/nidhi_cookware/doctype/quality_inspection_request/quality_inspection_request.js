// Copyright (c) 2025, Abdul Mannan Shaikh	 and contributors
// For license information, please see license.txt

frappe.ui.form.on("Quality Inspection Request", {
	async refresh(frm) {},
});

frappe.ui.form.on("Quality Inspection Request Item", {
	set_parameters: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		show_parameter_dialog(frm, row);
	},
});

function show_parameter_dialog(frm, row) {
	frappe.call({
		method: "nidhi_cookware.api.get_inspection_parameters",
		args: {
			quality_inspection_request: frm.doc.name,
			child_row_reference: row.name,
		},
		callback: (r) => {
			const d = new frappe.ui.Dialog({
				title: "Set Parameters",
				fields: get_dialog_fields(),
				primary_action_label: "Update Parameters",
				primary_action: (values) => save_parameters(frm, row, r.message, values, d),
			});

			setup_manual_inspection_handler(d);
			load_existing_data(d, r.message, row);
			d.show();
		},
	});
}

function get_dialog_fields() {
	return [
		{
			fieldname: "manual_inspection",
			fieldtype: "Check",
			label: "Manual Inspection",
		},
		{
			fieldname: "parameters",
			fieldtype: "Table",
			label: "Inspection Parameters",
			cannot_add_rows: true,
			in_place_edit: true,
			data: [],
			fields: [
				{
					fieldtype: "Link",
					fieldname: "specification",
					label: "Specification",
					options: "Quality Inspection Parameter",
					in_list_view: 1,
				},
				{
					fieldtype: "Select",
					fieldname: "status",
					label: "Status",
					options: ["Accepted", "Rejected"],
					in_list_view: 1,
				},
				{
					fieldtype: "Data",
					fieldname: "reading_value",
					label: "Reading Value",
					in_list_view: 1,
				},
			],
		},
	];
}

function setup_manual_inspection_handler(dialog) {
	dialog.fields_dict.manual_inspection.df.onchange = function () {
		const params_table = dialog.fields_dict.parameters;
		params_table.df.cannot_add_rows = !this.value;
		params_table.df.cannot_delete_rows = !this.value;
		params_table.refresh();
	};
}

function load_existing_data(dialog, existing_params, row) {
	if (existing_params) {
		dialog.set_value("manual_inspection", existing_params.manual_inspection ? 1 : 0);
		dialog.fields_dict.parameters.df.data = existing_params.readings;
		dialog.fields_dict.parameters.refresh();
	} else if (row.quality_inspection_template) {
		load_template_data(dialog, row.quality_inspection_template);
	}
}

function load_template_data(dialog, template) {
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "Quality Inspection Template",
			name: template,
		},
		callback: function (r) {
			if (r.message?.item_quality_inspection_parameter) {
				dialog.fields_dict.parameters.df.data =
					r.message.item_quality_inspection_parameter;
				dialog.fields_dict.parameters.refresh();
			}
		},
	});
}

function save_parameters(frm, row, existing_params, values, dialog) {
	frappe.call({
		method: "nidhi_cookware.api.save_inspection_parameters",
		args: {
			parameters: {
				name: existing_params?.name,
				quality_inspection_request: frm.doc.name,
				child_row_reference: row.name,
				quality_inspection_template: row.quality_inspection_template,
				item_code: row.item_code,
				readings: values.parameters,
				manual_inspection: values.manual_inspection,
			},
		},
		callback: function () {
			frappe.show_alert("Parameters updated");
			dialog.hide();
		},
	});
}
