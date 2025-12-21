"""Utility script to populate existing `qaco.client.onboarding` records with
active templates in the `template_library_rel_ids` many2many.

Usage (from Odoo shell or run in environment with Odoo path):

# In shell from Odoo source root
$ ./odoo-bin shell -d <db> -c <config>
>>> env['qaco.client.onboarding'].populate_template_library()

Or run standalone using `odoo shell` or by importing Odoo env in a script (advanced).
"""

# This file is intentionally a simple usage helper. It is NOT executable on its own
# without an Odoo environment. Use from `odoo-bin shell` as documented.

print('Run from: ./odoo-bin shell -d <db>')
print('Then call: env["qaco.client.onboarding"].populate_template_library()')
