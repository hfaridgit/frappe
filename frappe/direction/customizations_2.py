# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

import six

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt

@frappe.whitelist()
def make_stock_entry_with_accepted_qty_from_purchase_receipt(source_name, target_doc=None):
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
def make_stock_entry_with_rejected_qty_from_purchase_receipt(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.purpose = 'Material Issue'
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
				'field_map': {
					'rejected_qty': 'qty',
					'rejected_warehouse': 's_warehouse'
				},
				'condition': lambda doc: doc.rejected_qty > 0
			},
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
		return flt(completed[0].count * 100.0 / total[0].count, 2)

@frappe.whitelist()
def get_actual_qty_for_sample(doc):
	if isinstance(doc, six.string_types):
		doc = frappe._dict(json.loads(doc))

	conversion_factor = frappe.db.get_value('UOM Conversion Detail', {'parent': doc.item_code, 'uom': 'Kg'}, 'conversion_factor')

	bin = frappe.db.sql(
		"SELECT SUM(actual_qty) AS 'actual_qty' FROM `tabBin` WHERE item_code = %(item_code)s GROUP BY item_code",
		{'item_code': doc.item_code},
		as_dict=True
	)

	if conversion_factor and bin:
		return flt(doc.sample_weight) * flt(conversion_factor) <= flt(bin[0].actual_qty)

def sendmail_on_invalid_rate(doc, method):
	pass
