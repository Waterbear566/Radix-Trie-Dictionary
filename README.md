# 📚 English Dictionary — Radix Trie

A GUI-based English dictionary application built with Python and Tkinter, using a **Radix Trie (Patricia Trie)** as the core indexing structure.

## Features
- ➕ **Add** a word and definition
- 🔍 **Search** for a word's meaning
- 🗑️ **Delete** a word from the dictionary
- 🌲 **Live Trie Visualization** — see how the data structure changes after every operation
- 📜 **Operation Log** — timestamped history of all actions

## Requirements
- Python 3.10+
- No external packages needed (uses `tkinter` from the standard library)

## Run
```bash
python dictionary.py
```

## Project Structure
```
dictionary_app/
├── dictionary.py    # Main application (Radix Trie + Tkinter GUI)
└── README.md
```

## Data Structure
The **Radix Trie** compresses common prefixes to save memory and speed up lookups.
- **Insert / Search / Delete**: O(m) where m = word length
- **Space**: O(n × m) in the worst case, significantly reduced by prefix sharing
