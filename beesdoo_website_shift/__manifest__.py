# Copyright 2017-2020 Coop IT Easy SC (http://coopiteasy.be)
#   Rémy Taymans <remy@coopiteasy.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "BEES coop Website Shift",
    "summary": """
        Show available shifts for regular and irregular workers on the
        website and let workers manage their shifts with an
        easy web interface.
    """,
    "author": "Coop IT Easy SC",
    "license": "AGPL-3",
    "version": "12.0.2.2.1",
    "website": "https://github.com/beescoop/Obeesdoo",
    "category": "Cooperative management",
    "depends": ["portal", "website", "shift"],
    "data": [
        "data/res_config_data.xml",
        "views/shift_website_templates.xml",
        "views/portal_website_templates.xml",
        "views/res_partner_views.xml",
        "views/my_shift_website_templates.xml",
        "views/res_config_views.xml",
        "views/assets.xml",
    ],
}
