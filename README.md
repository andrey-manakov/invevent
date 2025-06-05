

WIZARD STRUCTURE (to be implemented)
your_project_root/
│
├── bot.py
├── config.py
├── callbacks.py
├── database.py
├── helpers.py
├── menus/                        ← menu handlers package
├── models.py
├── routes.py
│
├── wizard/                         ← new “wizard” package
│   ├── __init__.py
│   │
│   ├── wizard.py                   ← state‐management (step index, start/get/reset)
│   ├── wizard_utils.py             ← shared helpers (TAG list, random‐suffix, snippet)
│   ├── wizard_start.py             ← “➕ Create event” handler (step 0 prompt)
│   ├── wizard_dispatcher.py        ← “in‐wizard” dispatcher (cancel check + step routing)
│   │
│   └── steps/                      ← one file per logical step
│       ├── __init__.py
│       ├── step0_title.py          ← handle title‐entry (moves to step 1)
│       ├── step1_description.py    ← handle description (back ↔ step 0, then step 2)
│       ├── step2_datetime.py       ← handle “today/tomorrow” (back ↔ step 1, then step 3)
│       ├── step3_tags.py           ← handle tag selection (back ↔ step 2, then step 4)
│       ├── step4_location.py       ← handle “moscow” (back ↔ step 3, then step 5)
│       └── step5_visibility.py     ← handle visibility & creation (back ↔ step 4, then create)
│
└── … (other files unchanged)
