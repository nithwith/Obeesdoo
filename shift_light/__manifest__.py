# Copyright 2020-2023 Coop IT Easy SC
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


{
    "name": "Shift Management - Light",
    "summary": """Generate and manage shifts.""",
    "author": """
        Théo MARTY
        """,
    "website": "",
    "category": "Cooperative management",
    "version": "17.0.1.1.0",
    "depends": ["mail"],
    "data": [
        "security/group.xml",
        "security/ir.model.access.csv",
        "data/system_parameter.xml",
        "views/planning.xml",
        "views/menu.xml",
        "views/shift.xml",
        "views/shift_template.xml",
        "wizard/instantiate_planning.xml",
    ],
    "demo": [
    ],
    "license": "AGPL-3",
}
