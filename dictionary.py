"""
English Dictionary Application using Radix-Trie
Author: VuHung
Description: A GUI-based English dictionary with Radix-Trie indexing.
             Supports add, delete, and search operations.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json


# ─────────────────────────────────────────────
#  Radix Trie Implementation
# ─────────────────────────────────────────────

class RadixTrieNode:
    def __init__(self):
        self.children: dict[str, tuple["RadixTrieNode", str]] = {}
        # key  → (child_node, edge_label)
        self.is_end: bool = False
        self.definition: str = ""
        self.word: str = ""          # full word stored at leaf/end nodes

    def __repr__(self):
        return f"RadixTrieNode(end={self.is_end}, word='{self.word}')"


class RadixTrie:
    """Radix Trie (Patricia Trie) for English dictionary indexing."""

    def __init__(self):
        self.root = RadixTrieNode()
        self._size = 0

    # ── helpers ──────────────────────────────
    @staticmethod
    def _common_prefix(a: str, b: str) -> int:
        """Return length of common prefix of a and b."""
        length = min(len(a), len(b))
        for i in range(length):
            if a[i] != b[i]:
                return i
        return length

    # ── insert ───────────────────────────────
    def insert(self, word: str, definition: str) -> bool:
        """Insert word with definition. Returns False if word already exists."""
        word = word.lower().strip()
        if not word:
            return False

        node = self.root
        remaining = word

        while remaining:
            first_char = remaining[0]

            if first_char not in node.children:
                # No matching edge → create new leaf
                new_node = RadixTrieNode()
                new_node.is_end = True
                new_node.definition = definition
                new_node.word = word
                node.children[first_char] = (new_node, remaining)
                self._size += 1
                return True

            child_node, edge_label = node.children[first_char]
            cp = self._common_prefix(remaining, edge_label)

            if cp == len(edge_label):
                # Edge label fully consumed
                if cp == len(remaining):
                    # Exact match → update or mark as end
                    if child_node.is_end:
                        return False  # already exists
                    child_node.is_end = True
                    child_node.definition = definition
                    child_node.word = word
                    self._size += 1
                    return True
                # Dive deeper
                node = child_node
                remaining = remaining[cp:]
            else:
                # Split the edge at position cp
                split_node = RadixTrieNode()

                # Move existing child under split_node
                split_node.children[edge_label[cp]] = (child_node, edge_label[cp:])

                # New leaf for the inserted word
                new_leaf = RadixTrieNode()
                new_leaf.is_end = True
                new_leaf.definition = definition
                new_leaf.word = word

                if cp < len(remaining):
                    split_node.children[remaining[cp]] = (new_leaf, remaining[cp:])
                else:
                    # Inserted word ends exactly at split point
                    split_node.is_end = True
                    split_node.definition = definition
                    split_node.word = word

                node.children[first_char] = (split_node, edge_label[:cp])
                self._size += 1
                return True

        return False

    # ── search ───────────────────────────────
    def search(self, word: str) -> str | None:
        """Return definition if word exists, else None."""
        word = word.lower().strip()
        node = self.root
        remaining = word

        while remaining:
            first_char = remaining[0]
            if first_char not in node.children:
                return None
            child_node, edge_label = node.children[first_char]
            cp = self._common_prefix(remaining, edge_label)
            if cp < len(edge_label):
                return None
            remaining = remaining[cp:]
            node = child_node

        return node.definition if node.is_end else None

    # ── delete ───────────────────────────────
    def delete(self, word: str) -> bool:
        """Delete word. Returns True if deleted, False if not found."""
        word = word.lower().strip()
        result = self._delete_recursive(self.root, word, 0)
        if result:
            self._size -= 1
        return result

    def _delete_recursive(self, node: RadixTrieNode, word: str, depth: int) -> bool:
        if depth == len(word):
            if not node.is_end:
                return False
            node.is_end = False
            node.definition = ""
            node.word = ""
            return True

        first_char = word[depth]
        if first_char not in node.children:
            return False

        child_node, edge_label = node.children[first_char]
        cp = self._common_prefix(word[depth:], edge_label)
        if cp < len(edge_label):
            return False

        deleted = self._delete_recursive(child_node, word, depth + cp)

        if deleted:
            # Merge child into parent if child has exactly one child and is not an end node
            if not child_node.is_end and len(child_node.children) == 1:
                grandchild_key = next(iter(child_node.children))
                grandchild_node, grandchild_label = child_node.children[grandchild_key]
                node.children[first_char] = (grandchild_node, edge_label + grandchild_label)
            elif not child_node.is_end and len(child_node.children) == 0:
                del node.children[first_char]

        return deleted

    # ── trie visualisation ───────────────────
    def get_trie_structure(self) -> list[str]:
        """Return a list of lines representing the trie tree."""
        lines = []
        self._traverse_structure(self.root, "", "", lines)
        return lines

    def _traverse_structure(self, node: RadixTrieNode, prefix: str,
                             indent: str, lines: list[str]):
        for i, (char, (child, label)) in enumerate(sorted(node.children.items())):
            is_last = i == len(node.children) - 1
            connector = "└── " if is_last else "├── "
            end_marker = " ◉" if child.is_end else ""
            lines.append(f"{indent}{connector}[{label}]{end_marker}")
            child_indent = indent + ("    " if is_last else "│   ")
            self._traverse_structure(child, prefix + label, child_indent, lines)

    # ── all words ────────────────────────────
    def get_all_words(self) -> list[tuple[str, str]]:
        """Return sorted list of (word, definition) pairs."""
        results = []
        self._collect_words(self.root, results)
        return sorted(results, key=lambda x: x[0])

    def _collect_words(self, node: RadixTrieNode, results: list):
        if node.is_end:
            results.append((node.word, node.definition))
        for _, (child, _) in node.children.items():
            self._collect_words(child, results)

    @property
    def size(self) -> int:
        return self._size


# ─────────────────────────────────────────────
#  GUI Application
# ─────────────────────────────────────────────

COLORS = {
    "bg":        "#1E1E2E",
    "surface":   "#2A2A3E",
    "accent":    "#7C6AF7",
    "accent2":   "#5EEAD4",
    "danger":    "#F87171",
    "success":   "#4ADE80",
    "text":      "#E2E8F0",
    "muted":     "#94A3B8",
    "border":    "#3A3A5C",
    "highlight": "#312E81",
}

FONT_TITLE  = ("Segoe UI", 20, "bold")
FONT_HEADER = ("Segoe UI", 12, "bold")
FONT_BODY   = ("Segoe UI", 11)
FONT_MONO   = ("Consolas", 10)
FONT_SMALL  = ("Segoe UI", 9)


class DictionaryApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.trie = RadixTrie()
        self._seed_data()

        self.title("📚 English Dictionary — Radix Trie")
        self.geometry("1180x750")
        self.minsize(900, 600)
        self.configure(bg=COLORS["bg"])

        self._build_ui()
        self._refresh_word_list()
        self._refresh_trie_view()

    # ── seed data ────────────────────────────
    def _seed_data(self):
        samples = {
            "apple":      "A round fruit with red, yellow, or green skin and crisp flesh.",
            "application":"A program or piece of software designed for a specific purpose.",
            "algorithm":  "A set of rules or steps for solving a problem or accomplishing a task.",
            "banana":     "A long curved fruit with a yellow skin.",
            "binary":     "Relating to a system of numbers with only two digits, 0 and 1.",
            "cat":        "A small domesticated carnivorous mammal.",
            "computer":   "An electronic device for storing and processing data.",
            "data":       "Facts and statistics collected for reference or analysis.",
            "dictionary": "A reference book listing words with their meanings.",
            "element":    "A basic building block; in chemistry, a substance not decomposable.",
            "function":   "A block of code designed to perform a particular task.",
            "graph":      "A diagram showing the relation between variable quantities.",
            "hash":       "A function that converts data to a fixed-size value for fast lookup.",
            "index":      "A data structure to improve the speed of data retrieval.",
            "java":       "A high-level, class-based, object-oriented programming language.",
            "key":        "A value used to identify or access a record in a data structure.",
            "language":   "A system of communication used by a community.",
            "matrix":     "A rectangular array of numbers or other mathematical objects.",
            "node":       "A fundamental unit in a data structure such as a tree or graph.",
            "operator":   "A symbol that performs an operation on one or more operands.",
            "python":     "A high-level interpreted programming language emphasizing readability.",
            "queue":      "A linear data structure following the FIFO principle.",
            "recursion":  "A process in which a function calls itself as a subroutine.",
            "stack":      "A linear data structure following the LIFO principle.",
            "trie":       "A tree-like data structure for storing strings for efficient retrieval.",
            "unicode":    "A universal character-encoding standard for text.",
            "variable":   "A symbol used to represent a value that may change.",
            "word":       "A single unit of language expressing a meaning.",
        }
        for w, d in samples.items():
            self.trie.insert(w, d)

    # ── layout ───────────────────────────────
    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self, bg=COLORS["surface"], pady=12)
        header.pack(fill="x", padx=0, pady=0)
        tk.Label(header, text="📚  English Dictionary",
                 font=FONT_TITLE, bg=COLORS["surface"],
                 fg=COLORS["accent"]).pack(side="left", padx=20)
        self.status_var = tk.StringVar(value=f"📦 {self.trie.size} words indexed")
        tk.Label(header, textvariable=self.status_var,
                 font=FONT_BODY, bg=COLORS["surface"],
                 fg=COLORS["accent2"]).pack(side="right", padx=20)

        # ── Main panes ──
        paned = tk.PanedWindow(self, orient="horizontal",
                               bg=COLORS["bg"], sashwidth=6,
                               sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=10, pady=8)

        # Left panel
        left = tk.Frame(paned, bg=COLORS["bg"])
        paned.add(left, minsize=280)
        self._build_left_panel(left)

        # Right panel
        right = tk.Frame(paned, bg=COLORS["bg"])
        paned.add(right, minsize=400)
        self._build_right_panel(right)

    # ── Left panel ───────────────────────────
    def _build_left_panel(self, parent):
        # Operations card
        ops = self._card(parent, "⚙️  Operations")
        ops.pack(fill="x", pady=(0, 8))

        # --- ADD ---
        self._section_label(ops, "Add Word")
        self.add_word_var  = tk.StringVar()
        self.add_def_var   = tk.StringVar()
        self._entry(ops, "Word", self.add_word_var)
        self._entry(ops, "Definition", self.add_def_var)
        self._btn(ops, "➕  Add Word", self._do_add, COLORS["accent"])

        ttk.Separator(ops, orient="horizontal").pack(fill="x", pady=10, padx=8)

        # --- SEARCH ---
        self._section_label(ops, "Search Word")
        self.search_var = tk.StringVar()
        self._entry(ops, "Word", self.search_var)
        self._btn(ops, "🔍  Search", self._do_search, COLORS["accent2"])

        ttk.Separator(ops, orient="horizontal").pack(fill="x", pady=10, padx=8)

        # --- DELETE ---
        self._section_label(ops, "Delete Word")
        self.del_var = tk.StringVar()
        self._entry(ops, "Word", self.del_var)
        self._btn(ops, "🗑️  Delete Word", self._do_delete, COLORS["danger"])

        # Word list card
        wl = self._card(parent, "📋  Word List")
        wl.pack(fill="both", expand=True)

        self.word_listbox = tk.Listbox(
            wl, bg=COLORS["surface"], fg=COLORS["text"],
            font=FONT_MONO, selectbackground=COLORS["highlight"],
            selectforeground=COLORS["accent2"],
            relief="flat", borderwidth=0, activestyle="none",
            highlightthickness=0
        )
        sb = tk.Scrollbar(wl, orient="vertical",
                          command=self.word_listbox.yview)
        self.word_listbox.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.word_listbox.pack(fill="both", expand=True, padx=6, pady=6)
        self.word_listbox.bind("<<ListboxSelect>>", self._on_word_select)

    # ── Right panel ──────────────────────────
    def _build_right_panel(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=COLORS["bg"],
                        borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=COLORS["surface"],
                        foreground=COLORS["muted"],
                        padding=[14, 6],
                        font=FONT_BODY)
        style.map("TNotebook.Tab",
                  background=[("selected", COLORS["highlight"])],
                  foreground=[("selected", COLORS["accent2"])])

        # Tab 1: Result
        tab_result = tk.Frame(notebook, bg=COLORS["bg"])
        notebook.add(tab_result, text="📄  Result")
        self._build_result_tab(tab_result)

        # Tab 2: Trie Structure
        tab_trie = tk.Frame(notebook, bg=COLORS["bg"])
        notebook.add(tab_trie, text="🌲  Trie Structure")
        self._build_trie_tab(tab_trie)

        # Tab 3: Log
        tab_log = tk.Frame(notebook, bg=COLORS["bg"])
        notebook.add(tab_log, text="📜  Operation Log")
        self._build_log_tab(tab_log)

    def _build_result_tab(self, parent):
        frame = tk.Frame(parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="Operation Result",
                 font=FONT_HEADER, bg=COLORS["bg"],
                 fg=COLORS["accent"]).pack(anchor="w", pady=(0, 6))

        self.result_text = scrolledtext.ScrolledText(
            frame, bg=COLORS["surface"], fg=COLORS["text"],
            font=FONT_BODY, relief="flat", borderwidth=0,
            wrap="word", state="disabled",
            insertbackground=COLORS["text"],
            highlightthickness=1,
            highlightbackground=COLORS["border"]
        )
        self.result_text.pack(fill="both", expand=True)

        # Tags for coloring
        self.result_text.tag_config("success", foreground=COLORS["success"])
        self.result_text.tag_config("error",   foreground=COLORS["danger"])
        self.result_text.tag_config("info",    foreground=COLORS["accent2"])
        self.result_text.tag_config("word",    foreground=COLORS["accent"],
                                    font=("Segoe UI", 13, "bold"))
        self.result_text.tag_config("label",   foreground=COLORS["muted"])

    def _build_trie_tab(self, parent):
        frame = tk.Frame(parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        header = tk.Frame(frame, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 6))
        tk.Label(header, text="Radix Trie Structure",
                 font=FONT_HEADER, bg=COLORS["bg"],
                 fg=COLORS["accent"]).pack(side="left")
        tk.Button(header, text="🔄 Refresh",
                  command=self._refresh_trie_view,
                  bg=COLORS["surface"], fg=COLORS["accent2"],
                  font=FONT_SMALL, relief="flat",
                  padx=8, pady=3,
                  activebackground=COLORS["highlight"],
                  activeforeground=COLORS["accent2"],
                  cursor="hand2").pack(side="right")

        self.trie_text = scrolledtext.ScrolledText(
            frame, bg=COLORS["surface"], fg=COLORS["text"],
            font=FONT_MONO, relief="flat", borderwidth=0,
            wrap="none", state="disabled",
            highlightthickness=1,
            highlightbackground=COLORS["border"]
        )
        self.trie_text.pack(fill="both", expand=True)
        self.trie_text.tag_config("root",  foreground=COLORS["accent"],
                                  font=("Consolas", 11, "bold"))
        self.trie_text.tag_config("end",   foreground=COLORS["success"])
        self.trie_text.tag_config("node",  foreground=COLORS["accent2"])
        self.trie_text.tag_config("branch",foreground=COLORS["muted"])

    def _build_log_tab(self, parent):
        frame = tk.Frame(parent, bg=COLORS["bg"])
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        header = tk.Frame(frame, bg=COLORS["bg"])
        header.pack(fill="x", pady=(0, 6))
        tk.Label(header, text="Operation Log",
                 font=FONT_HEADER, bg=COLORS["bg"],
                 fg=COLORS["accent"]).pack(side="left")
        tk.Button(header, text="🗑 Clear",
                  command=self._clear_log,
                  bg=COLORS["surface"], fg=COLORS["danger"],
                  font=FONT_SMALL, relief="flat",
                  padx=8, pady=3,
                  activebackground=COLORS["highlight"],
                  activeforeground=COLORS["danger"],
                  cursor="hand2").pack(side="right")

        self.log_text = scrolledtext.ScrolledText(
            frame, bg=COLORS["surface"], fg=COLORS["text"],
            font=FONT_MONO, relief="flat", borderwidth=0,
            wrap="word", state="disabled",
            highlightthickness=1,
            highlightbackground=COLORS["border"]
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.tag_config("add",    foreground=COLORS["success"])
        self.log_text.tag_config("del",    foreground=COLORS["danger"])
        self.log_text.tag_config("search", foreground=COLORS["accent2"])
        self.log_text.tag_config("time",   foreground=COLORS["muted"])

    # ── Widget helpers ───────────────────────
    def _card(self, parent, title: str) -> tk.Frame:
        outer = tk.Frame(parent, bg=COLORS["surface"],
                         relief="flat", bd=0)
        tk.Label(outer, text=title,
                 font=FONT_HEADER, bg=COLORS["surface"],
                 fg=COLORS["accent2"]).pack(anchor="w", padx=10, pady=(8, 4))
        return outer

    def _section_label(self, parent, text: str):
        tk.Label(parent, text=text,
                 font=("Segoe UI", 9, "bold"),
                 bg=COLORS["surface"],
                 fg=COLORS["muted"]).pack(anchor="w", padx=12, pady=(4, 1))

    def _entry(self, parent, placeholder: str, var: tk.StringVar):
        e = tk.Entry(parent, textvariable=var,
                     bg=COLORS["bg"], fg=COLORS["text"],
                     font=FONT_BODY, relief="flat",
                     insertbackground=COLORS["text"],
                     highlightthickness=1,
                     highlightbackground=COLORS["border"],
                     highlightcolor=COLORS["accent"])
        e.pack(fill="x", padx=12, pady=2, ipady=5)
        # Placeholder hint
        e.insert(0, placeholder)
        e.config(fg=COLORS["muted"])
        def on_focus_in(event, _e=e, _v=var, _p=placeholder):
            if _e.get() == _p:
                _e.delete(0, "end")
                _e.config(fg=COLORS["text"])
        def on_focus_out(event, _e=e, _v=var, _p=placeholder):
            if not _e.get():
                _e.insert(0, _p)
                _e.config(fg=COLORS["muted"])
        e.bind("<FocusIn>",  on_focus_in)
        e.bind("<FocusOut>", on_focus_out)
        return e

    def _btn(self, parent, text: str, cmd, color: str):
        tk.Button(parent, text=text, command=cmd,
                  bg=color, fg="white",
                  font=("Segoe UI", 10, "bold"),
                  relief="flat", padx=10, pady=6,
                  activebackground=COLORS["highlight"],
                  activeforeground="white",
                  cursor="hand2").pack(fill="x", padx=12, pady=(3, 4))

    # ── Operations ───────────────────────────
    def _do_add(self):
        word = self.add_word_var.get().strip()
        defn = self.add_def_var.get().strip()
        placeholders = {"Word", "Definition", ""}
        if word in placeholders or defn in placeholders:
            self._show_result("⚠️ Please enter both a word and its definition.",
                              "error")
            return

        ok = self.trie.insert(word, defn)
        if ok:
            msg = f"✅  '{word}' added successfully!\n\n"
            msg += f"📖 Definition:\n   {defn}\n\n"
            msg += f"📦 Total words: {self.trie.size}"
            self._show_result(msg, "success")
            self._log(f"[ADD]    '{word}'", "add")
            self.add_word_var.set("")
            self.add_def_var.set("")
        else:
            self._show_result(f"⚠️  '{word}' already exists in the dictionary.",
                              "error")
        self._refresh_word_list()
        self._refresh_trie_view()
        self._update_status()

    def _do_search(self):
        word = self.search_var.get().strip()
        if word in {"Word", ""}:
            self._show_result("⚠️ Please enter a word to search.", "error")
            return

        defn = self.trie.search(word)
        if defn is not None:
            msg = f"🔍  Found: '{word.upper()}'\n\n"
            msg += f"📖 Definition:\n   {defn}\n"
            self._show_result(msg, "info")
            self._log(f"[SEARCH] '{word}' → found", "search")
            # Highlight in list
            self._highlight_word(word)
        else:
            self._show_result(f"❌  '{word}' not found in the dictionary.", "error")
            self._log(f"[SEARCH] '{word}' → not found", "search")
        self._update_status()

    def _do_delete(self):
        word = self.del_var.get().strip()
        if word in {"Word", ""}:
            self._show_result("⚠️ Please enter a word to delete.", "error")
            return

        ok = self.trie.delete(word)
        if ok:
            msg = f"🗑️  '{word}' deleted successfully.\n\n"
            msg += f"📦 Remaining words: {self.trie.size}"
            self._show_result(msg, "success")
            self._log(f"[DELETE] '{word}'", "del")
            self.del_var.set("")
        else:
            self._show_result(f"❌  '{word}' not found in the dictionary.", "error")
        self._refresh_word_list()
        self._refresh_trie_view()
        self._update_status()

    def _on_word_select(self, event):
        sel = self.word_listbox.curselection()
        if not sel:
            return
        item = self.word_listbox.get(sel[0])
        word = item.split("  ")[0].strip()
        defn = self.trie.search(word)
        if defn:
            self._show_result(
                f"📖  {word.upper()}\n\n{defn}\n", "info"
            )

    # ── Refresh helpers ──────────────────────
    def _refresh_word_list(self):
        self.word_listbox.delete(0, "end")
        for w, d in self.trie.get_all_words():
            preview = d[:45] + "…" if len(d) > 45 else d
            self.word_listbox.insert("end", f"{w:<18}  {preview}")

    def _refresh_trie_view(self):
        lines = self.trie.get_trie_structure()
        self.trie_text.configure(state="normal")
        self.trie_text.delete("1.0", "end")
        self.trie_text.insert("end", f"ROOT  ({self.trie.size} words)\n", "root")
        for line in lines:
            if "◉" in line:
                self.trie_text.insert("end", line + "\n", "end")
            elif "└" in line or "├" in line:
                self.trie_text.insert("end", line + "\n", "node")
            else:
                self.trie_text.insert("end", line + "\n", "branch")
        self.trie_text.configure(state="disabled")

    def _highlight_word(self, word: str):
        for i in range(self.word_listbox.size()):
            item = self.word_listbox.get(i)
            if item.startswith(word.lower()):
                self.word_listbox.selection_clear(0, "end")
                self.word_listbox.selection_set(i)
                self.word_listbox.see(i)
                break

    def _update_status(self):
        self.status_var.set(f"📦 {self.trie.size} words indexed")

    # ── Result / Log ─────────────────────────
    def _show_result(self, text: str, tag: str = "info"):
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("end", text, tag)
        self.result_text.configure(state="disabled")

    def _log(self, text: str, tag: str):
        import datetime
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{ts}]  ", "time")
        self.log_text.insert("end", text + "\n", tag)
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")


# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = DictionaryApp()
    app.mainloop()
