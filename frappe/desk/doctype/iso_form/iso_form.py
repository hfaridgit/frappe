# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.naming import make_autoname
from frappe.model.document import Document

class ISOForm(Document):
	def autoname(self):
		self.name = make_autoname('ISO/' +self.iso_number + '/.#####')
