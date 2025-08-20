# Copyright (c) 2025, Abdul Mannan Shaikh	 and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class QualityInspectionRequest(Document):

	def before_save(self):
		for row in self.inspection_item:
			qi = frappe.new_doc("Quality Inspection")
			qi.inspection_type = self.inspection_type
			qi.reference_type = self.reference_type
			qi.reference_name = self.reference_name
			qi.report_date = frappe.utils.nowdate()
			qi.inspected_by = self.inspected_by or frappe.session.user

			qi.item_code = row.item_code
			qi.item_serial_no = row.item_serial_no
			qi.batch_no = row.batch_no
			qi.bom_no = row.bom_no
			qi.quality_inspection_template = row.quality_inspection_template

			qi.qty = row.qty_received or 0
			qi.qty_inspected = row.qty_inspected or 0
			qi.qty_accepted = row.qty_accepted or 0
			qi.qty_rejected = row.qty_rejected or 0
			qi.sample_size = 1
			qi.insert(ignore_permissions=True)
			# qi.submit()
