# 📝 Notch

A clean, minimal desktop notes app built with Python and PyQt5. Your notes are saved automatically — no buttons, no fuss.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![PyQt5](https://img.shields.io/badge/PyQt5-5.x-green?logo=qt&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## ✨ Features

- **Instant saving** — every keystroke is persisted to disk automatically
- **Sidebar navigation** — browse all your notes from a clean list panel
- **Live word count** — shown in the status bar as you type
- **Keyboard shortcuts** — `Ctrl+N` to create, `Ctrl+D` to delete
- **Persistent storage** — notes survive app restarts via a local JSON file
- **Confirmation dialogs** — no accidental deletions
  

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- PyQt5
- To install the PyQt5 package just write in the console pip install requirements.txt

### Installation

```bash
# Clone the repo
git clone https://github.com/yourusername/notch.git
cd notch

# Install dependencies
pip install PyQt5

# Run the app
python main.py
```

---

## 🗂 Project Structure

```
notch/
├── main.py           # App entry point and main window logic
├── notes_data.json   # Auto-generated notes storage (gitignored)
├── assets/
│   └── logo.png      # App icon
└── README.md
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New note |
| `Ctrl+D` | Delete selected note |

---

## 💾 Data Storage

Notes are saved locally to `notes_data.json` in the project root. The file is updated on every keystroke and on app close — no manual saving required.

It's recommended to add this file to your `.gitignore` if you don't want your notes tracked:

```
notes_data.json
```

---

## 🛠 Built With

- [Python](https://www.python.org/) — core language
- [PyQt5](https://pypi.org/project/PyQt5/) — GUI framework
- `json` / `os` — standard library for persistence

---
