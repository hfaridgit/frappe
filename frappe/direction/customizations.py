# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.utils import cint, flt, nowdate, getdate, today, cstr, nowtime, now_datetime
from frappe import msgprint, _, throw

@frappe.whitelist()
def submit_multiple(args=None):
	"""submit selected items"""

	il = json.loads(frappe.form_dict.get('items'))
	doctype = frappe.form_dict.get('doctype')

	for i, d in enumerate(il):
		try:
			frappe.get_doc(doctype, d).submit()
			if len(il) >= 5:
				frappe.publish_realtime("progress",
					dict(progress=[i+1, len(il)], title=_('Submitting {0}').format(doctype)),
					user=frappe.session.user)
		except Exception:
			pass

@frappe.whitelist()
def approve_multiple(names, doctype, status):
	if not frappe.has_permission(doctype, "write"):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	names = json.loads(names)
	for name in names:
		d = frappe.get_doc(doctype, name)
		if d.docstatus == 0:
			d.status = status
			d.save()

@frappe.whitelist()
def update_print_counter(doctype, name):
	from watchdog.utils import has_attribute
	pc = None
	dc = frappe.get_doc(doctype,name)
	if has_attribute(dc, 'print_counter'):
		pc = dc.print_counter
		if pc != None and pc == 0:
			frappe.db.set_value(doctype, name, "print_counter", 1)
		
