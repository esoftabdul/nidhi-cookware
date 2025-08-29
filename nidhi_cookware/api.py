import frappe


def create_inspection_parameters(qir_name, child_row, item_code, template):
	params = frappe.new_doc("Quality Inspection Request Parameter")
	params.quality_inspection_request = qir_name
	params.child_row_reference = child_row.name
	params.item_code = item_code
	params.quality_inspection_template = template

	if template:
		template_doc = frappe.get_doc("Quality Inspection Template", template)
		for param in template_doc.item_quality_inspection_parameter:
			params.append(
				"readings",
				{
					"specification": param.specification,
					"numeric": param.numeric,
					"value": param.value,
					"min_value": param.min_value,
					"max_value": param.max_value,
				},
			)

	params.insert(ignore_permissions=True)


@frappe.whitelist()
def create_quality_inspection_request(doctype, docname):
	source_doc = frappe.get_doc(doctype, docname)
	rows_to_process = []  # Store rows to create parameters later

	qir = frappe.new_doc("Quality Inspection Request")
	qir.company = source_doc.company
	qir.inspection_type = "Incoming"
	qir.reference_type = doctype
	qir.reference_name = source_doc.name
	qir.report_date = frappe.utils.nowdate()
	qir.inspected_by = frappe.session.user

	for item in source_doc.items:
		if getattr(item, "serial_and_batch_bundle", None):
			serial_nos = frappe.db.get_all(
				"Serial and Batch Entry",
				filters={"parent": item.serial_and_batch_bundle},
				fields=["serial_no"],
			)

			for s in serial_nos:
				row = qir.append(
					"inspection_item",
					{
						"item_code": item.item_code,
						"item_serial_no": s.serial_no,
						"batch_no": getattr(item, "batch_no", None),
						"bom_no": getattr(item, "bom_no", None),
						"quality_inspection_template": frappe.db.get_value(
							"Item", item.item_code, "quality_inspection_template"
						),
						"qty_received": 1,
					},
				)
				rows_to_process.append((row, item.item_code))

		elif getattr(item, "serial_no", None) or getattr(item, "batch_no", None):
			# Case 2: single row with serial/batch
			row = qir.append(
				"inspection_item",
				{
					"item_code": item.item_code,
					"item_serial_no": getattr(item, "serial_no", None),
					"batch_no": getattr(item, "batch_no", None),
					"bom_no": getattr(item, "bom_no", None),
					"quality_inspection_template": frappe.db.get_value(
						"Item", item.item_code, "quality_inspection_template"
					),
					"qty_received": item.qty,
				},
			)
			rows_to_process.append((row, item.item_code))

		else:
			# Case 3: no serial, no batch → use summary fields
			for _ in range(int(item.qty or 0)):
				row = qir.append(
					"inspection_item",
					{
						"item_code": item.item_code,
						"bom_no": getattr(item, "bom_no", None),
						"quality_inspection_template": frappe.db.get_value(
							"Item", item.item_code, "quality_inspection_template"
						),
					},
				)
				rows_to_process.append((row, item.item_code))

	qir.insert(ignore_permissions=True)

	# Create parameters after QIR is inserted and rows have names
	for row, item_code in rows_to_process:
		create_inspection_parameters(qir.name, row, item_code, row.quality_inspection_template)

	frappe.db.commit()
	return qir.name


@frappe.whitelist()
def get_inspection_parameters(quality_inspection_request, child_row_reference):
	try:
		params = frappe.get_cached_doc(
			"Quality Inspection Request Parameter",
			{
				"quality_inspection_request": quality_inspection_request,
				"child_row_reference": child_row_reference,
			},
		)
		return params
	except frappe.DoesNotExistError:
		return None


@frappe.whitelist()
def save_inspection_parameters(parameters):
	parameters = frappe.parse_json(parameters)

	if parameters.get("name"):
		doc = frappe.get_doc("Quality Inspection Request Parameter", parameters.get("name"))
		doc.readings = []  # Clear existing readings
		doc.manual_inspection = parameters.get("manual_inspection")

	else:
		doc = frappe.new_doc("Quality Inspection Request Parameter")
		doc.quality_inspection_request = parameters.get("quality_inspection_request")
		doc.child_row_reference = parameters.get("child_row_reference")
		doc.quality_inspection_template = parameters.get("quality_inspection_template")
		doc.item_code = parameters.get("item_code")
		doc.manual_inspection = parameters.get("manual_inspection")

	for reading in parameters.get("readings", []):
		doc.append(
			"readings",
			{
				"specification": reading.get("specification"),
				"manual_inspection": 1,
				"status": reading.get("status", "Rejected"),
				"reading_value": reading.get("reading_value"),
				"numeric": 0,
				# "manual_inspection": reading.get("manual_inspection", 0)
			},
		)

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return doc.name
