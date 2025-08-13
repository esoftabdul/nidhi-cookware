import frappe
from collections import defaultdict
from frappe.utils import flt
from erpnext.manufacturing.doctype.bom.bom import get_bom_items_as_dict

def on_submit(doc,method=None):
    create_po_from_so(doc)

def create_po_from_so(doc):
    warehouse = doc.set_warehouse
    if not warehouse:
        frappe.throw("Set Warehouse is required in Sales Order")

    to_purchase = defaultdict(float)

    def process_bom_items(item_code, qty, warehouse, to_purchase):
        item_details = frappe.get_cached_value("Item", item_code, ["default_bom", "safety_stock", "is_purchase_item"], as_dict=1)
        has_bom = bool(item_details.default_bom)
        is_purchase_item = item_details.is_purchase_item
        safety = item_details.safety_stock or 0

        projected = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "projected_qty") or 0
        reorder_level, reorder_qty = get_reorder_info(item_code, warehouse)

        net_required = max(0, qty - projected)
        below_level = projected < reorder_level or projected < safety
        additional = reorder_qty if below_level else 0
        total_needed = net_required + additional

        if total_needed <= 0:
            return

        if has_bom:
            bom = item_details.default_bom
            bom_items = get_bom_items_as_dict(
                bom=bom,
                company=doc.company,
                qty=total_needed,
                fetch_exploded=1,
                fetch_scrap_items=0,
                include_non_stock_items=False,
                fetch_qty_in_stock_uom=True
            )
            for bom_item in bom_items.values():
                child_code = bom_item.item_code
                child_qty = flt(bom_item.qty)
                process_bom_items(child_code, child_qty, warehouse, to_purchase)
        elif is_purchase_item:
            to_purchase[item_code] += total_needed
        else:
            frappe.msgprint(f"Item {item_code} cannot be purchased or manufactured to meet demand.")

    def get_reorder_info(item_code, warehouse):
        item_doc = frappe.get_cached_doc("Item", item_code)
        for row in item_doc.reorder_levels or []:
            if row.warehouse == warehouse:
                return row.warehouse_reorder_level or 0, row.warehouse_reorder_qty or 0
        return 0, 0

    for so_item in doc.items:
        process_bom_items(so_item.item_code, so_item.qty, warehouse, to_purchase)

    if not to_purchase:
        return

    supplier_items = defaultdict(list)

    for item, qty in to_purchase.items():
        supplier = get_supplier_for_item(item)
        if supplier:
            supplier_items[supplier].append({"item_code": item, "qty": qty, "warehouse": warehouse})

    for supplier, items_list in supplier_items.items():
        po = frappe.new_doc("Purchase Order")
        po.supplier = supplier
        for it in items_list:
            po.append("items", {
                "item_code": it["item_code"],
                "qty": it["qty"],
                "schedule_date": doc.delivery_date,
                "warehouse": it["warehouse"]
            })
        po.insert()

def get_supplier_for_item(item):
    pos = frappe.db.sql("""
        SELECT po.supplier, poi.rate, po.transaction_date
        FROM `tabPurchase Order` po
        JOIN `tabPurchase Order Item` poi ON po.name = poi.parent
        WHERE poi.item_code = %s AND po.docstatus = 1
        ORDER BY po.transaction_date DESC, po.modified DESC
        LIMIT 10
    """, item, as_dict=True)

    if not pos:
        last_supplier = frappe.db.get_value(
            "Item Supplier",
            filters={"parent": item},
            fieldname="supplier",
            order_by="idx desc"
        )
        if last_supplier:
            return last_supplier
        else:
            frappe.throw(f"No supplier found for Item: <b>{item}</b>. Please add a supplier in the 'Suppliers' section of the Item master to proceed.")

    supplier_rates = {}
    for row in pos:
        if row.supplier not in supplier_rates:
            supplier_rates[row.supplier] = row.rate

    if supplier_rates:
        min_rate = min(supplier_rates.values())
        for sup, rate in supplier_rates.items():
            if rate == min_rate:
                return sup

    return None
