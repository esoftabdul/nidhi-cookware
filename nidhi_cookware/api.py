import frappe

@frappe.whitelist()
def create_quality_inspection_request(doctype, docname):
    source_doc = frappe.get_doc(doctype, docname)

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
                fields=["serial_no"]
            )

            for s in serial_nos:
                qir.append("inspection_item", {
                    "item_code": item.item_code,
                    "item_serial_no": s.serial_no,
                    "batch_no": getattr(item, "batch_no", None),
                    "bom_no": getattr(item, "bom_no", None),
                    "quality_inspection_template": frappe.db.get_value(
                        "Item",
                        item.item_code,
                        "quality_inspection_template"
                    ),
                    "qty_received": 1
                })

        elif getattr(item, "serial_no", None) or getattr(item, "batch_no", None):
            # Case 2: single row with serial/batch
            qir.append("inspection_item", {
                "item_code": item.item_code,
                "item_serial_no": getattr(item, "serial_no", None),
                "batch_no": getattr(item, "batch_no", None),
                "bom_no": getattr(item, "bom_no", None),
                "quality_inspection_template": frappe.db.get_value(
                    "Item",
                    item.item_code,
                    "quality_inspection_template"
                ),
                "qty_received": item.qty
            })

        else:
            # Case 3: no serial, no batch → use summary fields
            for _ in range(int(item.qty or 0)):
                qir.append("inspection_item", {
                    "item_code": item.item_code,
                    "bom_no": getattr(item, "bom_no", None),
                    "quality_inspection_template": frappe.db.get_value(
                        "Item",
                        item.item_code,
                        "quality_inspection_template"
                    ),
                    # "manual_qty": True,
                    # "qty_received": item.qty,
                })


    qir.insert(ignore_permissions=True)
    frappe.db.commit()
    return qir.name


# purchased 10 items
# item 1 has 4
# item 1 has 4
# item 1 has 4
