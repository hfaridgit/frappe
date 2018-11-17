from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Tools"),
			"icon": "octicon octicon-briefcase",
			"items": [
				{
					"type": "doctype",
					"name": "ISO Form",
					"label": _("ISO Form"),
					"description": _("ISO Documents."),
				},
				{
					"type": "doctype",
					"name": "ToDo",
					"label": _("To Do"),
					"description": _("Documents assigned to you and by you."),
				},
				{
					"type": "doctype",
					"name": "File",
					"label": _("Files"),
				},
				{
					"type": "doctype",
					"name": "Event",
					"label": _("Calendar"),
					"link": "List/Event/Calendar",
					"description": _("Event and other calendars."),
				},
				{
					"type": "page",
					"label": _("Chat"),
					"name": "chat",
					"description": _("Chat messages and other notifications."),
					"data_doctype": "Communication"
				},
				{
					"type": "doctype",
					"name": "Note",
					"description": _("Private and public Notes."),
				},
				{
					"type": "page",
					"label": _("Activity"),
					"name": "activity",
					"description": _("Activity log of all users."),
				},
				{
					"type": "doctype",
					"name": "Procedure",
					"label": _("Procedure"),
					"description": _("Procedure"),
				},
				{
					"type": "doctype",
					"name": "Products documents",
					"label": _("Products Documents"),
					"description": _("Products Documents."),
				},
			]
		},
		{
			'label': _('Email'),
			'items': [
				{
					"type": "doctype",
					"name": "Newsletter",
					"description": _("Newsletters to contacts, leads."),
				},
				{
					"type": "doctype",
					"name": "Email Group",
					"description": _("Email Group List"),
				},
			]
		}
	]
