# Copyright (c) 2025, Abdul Mannan Shaikh	 and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class QualityInspectionRequest(Document):
	def before_save(self):
		for row in self.inspection_item:
			# Create Quality Inspection
			qi = frappe.new_doc("Quality Inspection")

			# Set basic fields
			qi.inspection_type = self.inspection_type
			qi.reference_type = self.reference_type
			qi.reference_name = self.reference_name
			qi.report_date = frappe.utils.nowdate()
			qi.inspected_by = self.inspected_by or frappe.session.user

			# Set item details
			qi.item_code = row.item_code
			qi.item_serial_no = row.item_serial_no
			qi.batch_no = row.batch_no
			qi.bom_no = row.bom_no
			qi.quality_inspection_template = row.quality_inspection_template

			qi.sample_size = 1

			# Get and set parameters
			try:
				param_doc = frappe.get_cached_doc(
					"Quality Inspection Request Parameter",
					{"quality_inspection_request": self.name, "child_row_reference": row.name},
				)
				qi.manual_inspection = param_doc.manual_inspection
				for reading in param_doc.readings:
					qi.append(
						"readings",
						{
							"specification": reading.specification,
							"reading_value": reading.reading_value,
							"numeric": reading.numeric,
							"status": reading.status,
						},
					)
			except frappe.DoesNotExistError:
				frappe.msgprint(f"No parameters found for row {row.idx}")

			qi.insert(ignore_permissions=True)

			# Update status based on readings
			if any(r.status == "Rejected" for r in qi.readings):
				qi.status = "Rejected"
			else:
				qi.status = "Accepted"

			qi.submit()
			qi.submit()
