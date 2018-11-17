# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import frappe
from frappe import _
from frappe.desk.reportview import get_match_cond, get_filters_cond
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, nowdate

@frappe.whitelist()
def make_stock_entry_from_purchase_receipt(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.purpose = 'Material Transfer'
		target.run_method('set_basic_rate')
		target.run_method('get_stock_and_rate')

	doclist = get_mapped_doc(
		'Purchase Receipt',
		source_name,
		{
			'Purchase Receipt': {
				'doctype': 'Stock Entry',
				'validation': { 'docstatus': ['=', 1] }
			},
			'Purchase Receipt Item': {
				'doctype': 'Stock Entry Detail',
				'field_map': { 'warehouse': 's_warehouse' },
				'condition': lambda doc: doc.qty > 0
			},
		},
		target_doc,
		set_missing_values
	)

	return doclist

@frappe.whitelist()
def make_stock_entry_from_quality_inspection(source_name, target_doc=None):
	def set_missing_values(source, target):
		from_warehouse = None

		if source.reference_type == 'Sales Invoice':
			from_warehouse = 'B2B تحت الفحص مرتجعات - M'
		elif source.reference_type == 'Purchase Receipt':
			from_warehouse = 'تحت الفحص مواد خام - B2B - M'
		elif not source.reference_type:
			from_warehouse = 'تحت الفحص منتج تام - B2B - M'

		target.purpose = 'Material Transfer'
		target.posting_date = nowdate()
		target.from_warehouse = from_warehouse

		item = frappe.new_doc('Stock Entry Detail')
		item.s_warehouse = from_warehouse
		item.item_code = source.item_code
		item.item_name = source.item_name
		item.description = source.description
		item.qty = source.accepted_quantity
		item.batch_no = source.batch_no
		item.uom = source.uom
		target.set('items', [item])

	doclist = get_mapped_doc(
		'Quality Inspection',
		source_name,
		{
			'Quality Inspection': {
				'doctype': 'Stock Entry',
				'validation': { 'docstatus': ['=', 1] }
			}
		},
		target_doc,
		set_missing_values
	)

	return doclist

@frappe.whitelist()
def make_technical_returned_from_complains_form(source_name, target_doc=None):
	def set_missing_values(source, target):
		pass

	doclist = get_mapped_doc(
		'Complains Form',
		source_name,
		{
			'Complains Form': {
				'doctype': 'Technical Returned',
				'validation': { 'docstatus': ['=', 1] }
			}
		},
		target_doc,
		set_missing_values
	)

	return doclist

@frappe.whitelist()
def get_percentage_completed_of_sales_order():
	total = frappe.db.sql(
		"SELECT COUNT(*) AS count FROM `tabSales Order` WHERE docstatus = 1 AND status != 'Closed'",
		as_dict=True
	)

	completed = frappe.db.sql(
		"SELECT COUNT(*) AS count FROM `tabSales Order` WHERE docstatus = 1 AND status = 'Completed'",
		as_dict=True
	)

	if total and completed:
		return flt(completed[0].count * 100.0 / (total[0].count or 1), 2)

@frappe.whitelist()
def get_last_selling_rate(item_code):
	rates = frappe.db.sql(
		"""
		SELECT sii.base_rate, sii.rate FROM `tabSales Invoice Item` AS `sii`
		LEFT JOIN `tabSales Invoice` AS `si` ON si.name = sii.parent
		WHERE sii.item_code = %s
		AND sii.docstatus = 1
		ORDER BY si.posting_date DESC, si.posting_time DESC
		LIMIT 1
		""",
		(item_code,),
		as_dict=True
	)

	if rates:
		return rates[0]

@frappe.whitelist()
def get_address_by_link(link_name, link_doctype='Customer'):
	if link_name:
		address_name = frappe.db.get_value(
			'Dynamic Link',
			{'parenttype': 'Address','link_doctype': link_doctype, 'link_name': link_name},
			'parent'
		)

	if address_name:
		return frappe.get_doc('Address', address_name)

@frappe.whitelist()
def sales_invoice_item_query(doctype, txt, searchfield, start, page_len, filters, as_dict=False):
	doctype = 'Sales Invoice Item'
	conditions = []

	return frappe.db.sql("""select `tabSales Invoice Item`.item_code, `tabSales Invoice Item`.item_group,
		if(length(`tabSales Invoice Item`.item_name) > 40,
			concat(substr(`tabSales Invoice Item`.item_name, 1, 40), "..."), item_name) as item_name,
		if(length(`tabSales Invoice Item`.description) > 40, \
			concat(substr(`tabSales Invoice Item`.description, 1, 40), "..."), description) as decription
		from `tabSales Invoice Item`
		where `tabSales Invoice Item`.docstatus < 2
			and (`tabSales Invoice Item`.`{key}` LIKE %(txt)s
				or `tabSales Invoice Item`.item_group LIKE %(txt)s
				or `tabSales Invoice Item`.item_name LIKE %(txt)s
				or `tabSales Invoice Item`.barcode LIKE %(txt)s
				or `tabSales Invoice Item`.description LIKE %(txt)s)
			{fcond} {mcond}
		order by
			if(locate(%(_txt)s, item_code), locate(%(_txt)s, item_code), 99999),
			if(locate(%(_txt)s, item_name), locate(%(_txt)s, item_name), 99999),
			idx desc,
			name, item_name
		limit %(start)s, %(page_len)s """.format(
			key=searchfield,
			fcond=get_filters_cond(doctype, filters, conditions).replace('%', '%%'),
			mcond=get_match_cond(doctype).replace('%', '%%')),
			{
				"today": nowdate(),
				"txt": "%%%s%%" % txt,
				"_txt": txt.replace("%", ""),
				"start": start,
				"page_len": page_len
			}, as_dict=as_dict)

@frappe.whitelist()
def get_sales_invoice_item(item_code, parent, fields=None):
	return frappe.db.get_value(
		'Sales Invoice Item',
		{'parent': parent, 'item_code': item_code},
		'*' if not fields else json.loads(fields)
	)

def check_credit_limit_in_sales_order(doc, method):
	"""
	Check credit limit on sales order validation (Used in hooks)
	"""
	from erpnext.selling.doctype.customer.customer import get_customer_outstanding, get_credit_limit

	doc.exceeded_credit_limits = 0
	customer_outstanding = get_customer_outstanding(doc.customer, doc.company)
	credit_limit = get_credit_limit(doc.customer, doc.company)

	if credit_limit > 0 and flt(customer_outstanding) > credit_limit:
		doc.exceeded_credit_limits = 1

		frappe.msgprint(_('Credit limit has been crossed for customer {0} ({1}/{2})').format(
			doc.customer, customer_outstanding, credit_limit)
		)

		credit_controller = frappe.db.get_value('Accounts Settings', None, 'credit_controller')

		if not credit_controller or credit_controller not in frappe.get_roles():
			frappe.msgprint(_('Please contact to the user who have Sales Master Manager {0} role').format(
				' / ' + credit_controller if credit_controller else ''
			))

def check_overdue_sales_invoice(doc, method):
	"""
	Check overdue sales invoice on sales order validation (Used in hooks)
	"""
	doc.has_overdue_invoice = 0

	if frappe.db.get_value('Sales Invoice', {'customer': doc.customer, 'status': 'Overdue'}):
		doc.has_overdue_invoice = 1
		frappe.msgprint(_('Customer has an overdue invoice'))
		overdue_controller = frappe.db.get_value('Accounts Settings', None, 'overdue_controller')

		if not overdue_controller or overdue_controller not in frappe.get_roles():
			message = _('Please contact to the user who have Sales Master Manager {0} role').format(
				' / ' + overdue_controller if overdue_controller else ''
			)

			if doc.has_overdue_invoice:
				frappe.throw(message)

			frappe.msgprint(message)

def on_submit_stock_entry(doc, method):
	if doc.production_order:
		pro_doc = frappe.get_doc('Production Order', doc.production_order)

		if pro_doc.material_request and pro_doc.status == 'Completed':
			frappe.get_doc('Material Request', pro_doc.material_request).db_set('status', 'Produced')
