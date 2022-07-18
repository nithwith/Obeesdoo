# Copyright 2017 - 2020 BEES coop SCRLfs
#   - Robin Keunen <robin@coopiteasy.be>
#   - Houssine bakkali <houssine@coopiteasy.be>
#   - Rémy Taymans <remy@coopiteasy.be>
#   - Elise Dupont
#   - Thibault François
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Beescoop Base Module",
    "summary": """
    Module that customize the base module and contains some python tools
     """,
    "author": "Beescoop - Cellule IT, Coop IT Easy SC",
    "website": "https://github.com/beescoop/Obeesdoo",
    "category": "Sales",
    "version": "12.0.2.0.0",
    "depends": ["point_of_sale", "purchase", "portal", "partner_firstname"],
    "data": [
        "views/partner.xml",
        "wizard/views/partner.xml",
    ],
    "installable": True,
    "demo": ["demo/cooperators.xml", "demo/eaters.xml"],
    "license": "AGPL-3",
}
