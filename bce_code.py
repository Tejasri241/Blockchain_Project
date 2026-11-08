"""
Blockchain-Based Supply Chain Analytics and Vendor Performance Intelligence System
-----------------------------------------------------------------------------------
Features
  1. Stores supply-chain shipment records in a blockchain (SHA-256, proof-of-work)
  2. Uses exactly 10 manual inputs (defined in MANUAL_INPUTS below)
  3. Simulates tampering with a block's data
  4. Validates the chain (hash check, link check, proof-of-work check)
  5. Shows the blockchain view (block list + full block details)
  6. Vendor performance analytics (on-time %, defect %, score, rating)

Only the Python standard library is used (tkinter, hashlib, json, time, copy).
Run:  python supply_chain_blockchain.py
"""

import copy
import hashlib
import json
import time
import tkinter as tk
from tkinter import ttk, messagebox

# ----------------------------------------------------------------------
# 10 MANUAL INPUTS  (the only data this project uses)
# promised / actual = delivery days, defects = defective units received
# ----------------------------------------------------------------------
MANUAL_INPUTS = [
    {"shipment_id": "SH-1001", "vendor": "Alpha Traders",  "product": "Steel Rods",     "quantity": 500,  "unit_price": 42.0,  "promised_days": 5, "actual_days": 5, "defects": 4,  "location": "Hyderabad"},
    {"shipment_id": "SH-1002", "vendor": "Beta Supplies",  "product": "Copper Wire",    "quantity": 300,  "unit_price": 88.5,  "promised_days": 7, "actual_days": 9, "defects": 12, "location": "Chennai"},
    {"shipment_id": "SH-1003", "vendor": "Gamma Logistics","product": "Plastic Pellets","quantity": 1000, "unit_price": 15.2,  "promised_days": 4, "actual_days": 4, "defects": 6,  "location": "Mumbai"},
    {"shipment_id": "SH-1004", "vendor": "Alpha Traders",  "product": "Aluminium Sheets","quantity": 250, "unit_price": 120.0, "promised_days": 6, "actual_days": 7, "defects": 3,  "location": "Bengaluru"},
    {"shipment_id": "SH-1005", "vendor": "Delta Components","product": "Circuit Boards","quantity": 150,  "unit_price": 310.0, "promised_days": 10,"actual_days": 10,"defects": 2,  "location": "Pune"},
    {"shipment_id": "SH-1006", "vendor": "Beta Supplies",  "product": "Rubber Seals",   "quantity": 800,  "unit_price": 6.75,  "promised_days": 3, "actual_days": 6, "defects": 40, "location": "Chennai"},
    {"shipment_id": "SH-1007", "vendor": "Gamma Logistics","product": "Packaging Boxes","quantity": 2000, "unit_price": 3.4,   "promised_days": 2, "actual_days": 3, "defects": 25, "location": "Delhi"},
    {"shipment_id": "SH-1008", "vendor": "Delta Components","product": "Sensors",       "quantity": 400,  "unit_price": 55.0,  "promised_days": 8, "actual_days": 8, "defects": 5,  "location": "Pune"},
    {"shipment_id": "SH-1009", "vendor": "Alpha Traders",  "product": "Bolts & Nuts",   "quantity": 3000, "unit_price": 1.8,   "promised_days": 3, "actual_days": 3, "defects": 9,  "location": "Hyderabad"},
    {"shipment_id": "SH-1010", "vendor": "Beta Supplies",  "product": "Cables",         "quantity": 600,  "unit_price": 22.0,  "promised_days": 5, "actual_days": 5, "defects": 18, "location": "Kolkata"},
]

DIFFICULTY = 3  # hash must start with this many zeros (proof of work)


# ======================================================================
# BLOCKCHAIN CORE
# ======================================================================
class Block:
    def __init__(self, index, data, previous_hash, timestamp=None):
        self.index = index
        self.timestamp = timestamp or time.strftime("%Y-%m-%d %H:%M:%S")
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.compute_hash()

    def compute_hash(self):
        payload = json.dumps(
            {"index": self.index, "timestamp": self.timestamp, "data": self.data,
             "previous_hash": self.previous_hash, "nonce": self.nonce},
            sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def mine(self, difficulty):
        while not self.hash.startswith("0" * difficulty):
            self.nonce += 1
            self.hash = self.compute_hash()


class Blockchain:
    def __init__(self, difficulty=DIFFICULTY):
        self.difficulty = difficulty
        self.chain = []
        genesis = Block(0, {"info": "Genesis Block - Supply Chain Ledger"}, "0" * 64)
        genesis.mine(difficulty)
        self.chain.append(genesis)

    def add_block(self, data):
        block = Block(len(self.chain), data, self.chain[-1].hash)
        block.mine(self.difficulty)
        self.chain.append(block)
        return block

    def validate(self):
        """Return (is_valid, list of (index, reason))."""
        problems = []
        for i, blk in enumerate(self.chain):
            if blk.hash != blk.compute_hash():
                problems.append((blk.index, "Hash mismatch - block data was modified"))
            if not blk.hash.startswith("0" * self.difficulty):
                problems.append((blk.index, "Proof-of-work invalid"))
            if i > 0 and blk.previous_hash != self.chain[i - 1].hash:
                problems.append((blk.index, "Broken link - previous_hash does not match block %d" % (i - 1)))
        return (len(problems) == 0), problems


def vendor_analytics(chain):
    """Aggregate vendor KPIs from the shipment blocks."""
    vendors = {}
    for blk in chain.chain[1:]:
        d = blk.data
        v = vendors.setdefault(d["vendor"], {"shipments": 0, "on_time": 0, "units": 0,
                                             "defects": 0, "spend": 0.0, "delay_days": 0})
        v["shipments"] += 1
        v["on_time"] += 1 if d["actual_days"] <= d["promised_days"] else 0
        v["units"] += d["quantity"]
        v["defects"] += d["defects"]
        v["spend"] += d["quantity"] * d["unit_price"]
        v["delay_days"] += max(0, d["actual_days"] - d["promised_days"])
    rows = []
    for name, v in vendors.items():
        on_time_pct = 100.0 * v["on_time"] / v["shipments"]
        defect_pct = 100.0 * v["defects"] / v["units"]
        # Score: 60% delivery reliability + 40% quality (defect rate penalised x10)
        score = 0.6 * on_time_pct + 0.4 * max(0.0, 100.0 - defect_pct * 10)
        rating = "Excellent" if score >= 85 else "Good" if score >= 70 else "Average" if score >= 50 else "Poor"
        rows.append((name, v["shipments"], round(on_time_pct, 1), round(defect_pct, 2),
                     v["delay_days"], round(v["spend"], 2), round(score, 1), rating))
    rows.sort(key=lambda r: r[6], reverse=True)
    return rows


# ======================================================================
# TKINTER GUI
# ======================================================================
class App(tk.Tk):
    BG = "#f4f6fb"
    NAVY = "#1f2a44"

    def __init__(self):
        super().__init__()
        self.title("Blockchain-Based Supply Chain Analytics & Vendor Performance Intelligence System")
        self.geometry("1180x720")
        self.minsize(980, 620)
        self.configure(bg=self.BG)

        self.bc = Blockchain()
        self.original = {}      # index -> deepcopy of original data (for restore)
        self.bad_blocks = set()

        self._style()
        self._header()
        self._tabs()
        self._status_bar()
        self.load_inputs()

    # ---------------- layout ----------------
    def _style(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        s.configure("TNotebook.Tab", padding=(16, 6), font=("Segoe UI", 10, "bold"))
        s.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        s.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        s.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), padding=6)

    def _header(self):
        h = tk.Frame(self, bg=self.NAVY)
        h.pack(fill="x")
        tk.Label(h, text="Blockchain-Based Supply Chain Analytics and Vendor Performance Intelligence System",
                 bg=self.NAVY, fg="white", font=("Segoe UI", 14, "bold"), pady=10).pack()

    def _tabs(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(10, 4))
        self.tab_chain = tk.Frame(nb, bg=self.BG)
        self.tab_tamper = tk.Frame(nb, bg=self.BG)
        self.tab_analytics = tk.Frame(nb, bg=self.BG)
        nb.add(self.tab_chain, text="1. Blockchain View")
        nb.add(self.tab_tamper, text="2. Tamper & Validate")
        nb.add(self.tab_analytics, text="3. Vendor Analytics")
        self._build_chain_tab()
        self._build_tamper_tab()
        self._build_analytics_tab()

    def _status_bar(self):
        self.status = tk.StringVar()
        tk.Label(self, textvariable=self.status, anchor="w", bg="#e3e8f3",
                 font=("Segoe UI", 10, "bold"), padx=10, pady=6).pack(fill="x", side="bottom")

    # ---------------- tab 1: chain view ----------------
    def _build_chain_tab(self):
        top = tk.Frame(self.tab_chain, bg=self.BG)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Button(top, text="Reload 10 Manual Inputs (rebuild chain)", style="Accent.TButton",
                   command=self.load_inputs).pack(side="left")
        ttk.Button(top, text="Validate Chain", style="Accent.TButton",
                   command=self.validate).pack(side="left", padx=8)
        tk.Label(top, text="Select a block to see its full details below.", bg=self.BG,
                 fg="#555").pack(side="left", padx=10)

        cols = ("idx", "ts", "ship", "vendor", "product", "prev", "hash", "state")
        self.tree = ttk.Treeview(self.tab_chain, columns=cols, show="headings", height=11)
        heads = [("idx", "Block #", 60), ("ts", "Timestamp", 140), ("ship", "Shipment", 80),
                 ("vendor", "Vendor", 130), ("product", "Product", 130),
                 ("prev", "Previous Hash", 150), ("hash", "Block Hash", 150), ("state", "Status", 80)]
        for c, t, w in heads:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="center")
        self.tree.tag_configure("ok", background="#e6f6ea")
        self.tree.tag_configure("bad", background="#fde2e2", foreground="#a00000")
        self.tree.pack(fill="x", padx=8)
        self.tree.bind("<<TreeviewSelect>>", self.show_detail)

        tk.Label(self.tab_chain, text="Block Details", bg=self.BG, font=("Segoe UI", 10, "bold")
                 ).pack(anchor="w", padx=10, pady=(10, 2))
        self.detail = tk.Text(self.tab_chain, height=12, font=("Consolas", 10), bg="white", wrap="word")
        self.detail.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    # ---------------- tab 2: tamper & validate ----------------
    def _build_tamper_tab(self):
        f = tk.LabelFrame(self.tab_tamper, text=" Simulate Tampering ", bg=self.BG,
                          font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        f.pack(fill="x", padx=10, pady=10)

        tk.Label(f, text="Block #", bg=self.BG).grid(row=0, column=0, sticky="w")
        self.t_block = ttk.Combobox(f, state="readonly", width=8, values=list(range(1, 11)))
        self.t_block.grid(row=0, column=1, padx=6)
        self.t_block.current(2)

        tk.Label(f, text="Field", bg=self.BG).grid(row=0, column=2, sticky="w", padx=(14, 0))
        self.t_field = ttk.Combobox(f, state="readonly", width=14,
                                    values=["quantity", "unit_price", "actual_days", "defects", "vendor", "location"])
        self.t_field.grid(row=0, column=3, padx=6)
        self.t_field.current(3)

        tk.Label(f, text="New value", bg=self.BG).grid(row=0, column=4, sticky="w", padx=(14, 0))
        self.t_value = ttk.Entry(f, width=16)
        self.t_value.grid(row=0, column=5, padx=6)
        self.t_value.insert(0, "0")

        ttk.Button(f, text="Tamper Block", style="Accent.TButton", command=self.tamper
                   ).grid(row=0, column=6, padx=10)
        ttk.Button(f, text="Restore Original Data", style="Accent.TButton", command=self.restore
                   ).grid(row=0, column=7)

        v = tk.LabelFrame(self.tab_tamper, text=" Validation ", bg=self.BG,
                          font=("Segoe UI", 10, "bold"), padx=10, pady=10)
        v.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        ttk.Button(v, text="Validate Blockchain", style="Accent.TButton", command=self.validate
                   ).pack(anchor="w")
        self.result_lbl = tk.Label(v, text="Not validated yet", bg=self.BG, font=("Segoe UI", 13, "bold"))
        self.result_lbl.pack(anchor="w", pady=8)
        self.report = tk.Text(v, font=("Consolas", 10), bg="white", height=14, wrap="word")
        self.report.tag_configure("good", foreground="#0a7a2f")
        self.report.tag_configure("bad", foreground="#b00020")
        self.report.pack(fill="both", expand=True)

    # ---------------- tab 3: analytics ----------------
    def _build_analytics_tab(self):
        tk.Label(self.tab_analytics, text="Vendor Performance Intelligence (computed from blockchain data)",
                 bg=self.BG, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 4))
        cols = ("vendor", "ship", "ontime", "defect", "delay", "spend", "score", "rating")
        self.a_tree = ttk.Treeview(self.tab_analytics, columns=cols, show="headings", height=6)
        for c, t, w in [("vendor", "Vendor", 160), ("ship", "Shipments", 80), ("ontime", "On-Time %", 90),
                        ("defect", "Defect %", 90), ("delay", "Delay Days", 90),
                        ("spend", "Total Spend", 120), ("score", "Score /100", 90), ("rating", "Rating", 100)]:
            self.a_tree.heading(c, text=t)
            self.a_tree.column(c, width=w, anchor="center")
        self.a_tree.tag_configure("Excellent", background="#d6f5dc")
        self.a_tree.tag_configure("Good", background="#e8f5d0")
        self.a_tree.tag_configure("Average", background="#fff4cc")
        self.a_tree.tag_configure("Poor", background="#fde2e2")
        self.a_tree.pack(fill="x", padx=10)

        self.warn = tk.Label(self.tab_analytics, text="", bg=self.BG, fg="#b00020", font=("Segoe UI", 10, "bold"))
        self.warn.pack(anchor="w", padx=10, pady=4)

        self.canvas = tk.Canvas(self.tab_analytics, bg="white", height=260, highlightthickness=1,
                                highlightbackground="#ccd")
        self.canvas.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.canvas.bind("<Configure>", lambda e: self.draw_chart())

    # ---------------- actions ----------------
    def load_inputs(self):
        self.bc = Blockchain()
        self.original.clear()
        for rec in MANUAL_INPUTS:
            blk = self.bc.add_block(copy.deepcopy(rec))
            self.original[blk.index] = copy.deepcopy(rec)
        self.bad_blocks.clear()
        self.refresh_all()
        self.set_status("Blockchain built with 10 manual inputs (+ genesis block). Chain is VALID.", True)
        self.result_lbl.config(text="Not validated yet", fg="black")
        self.report.delete("1.0", "end")

    def refresh_all(self):
        self.refresh_tree()
        self.refresh_analytics()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for b in self.bc.chain:
            d = b.data
            tag = "bad" if b.index in self.bad_blocks else "ok"
            self.tree.insert("", "end", iid=str(b.index), tags=(tag,), values=(
                b.index, b.timestamp, d.get("shipment_id", "-"), d.get("vendor", "Genesis"),
                d.get("product", "-"), b.previous_hash[:14] + "...", b.hash[:14] + "...",
                "INVALID" if tag == "bad" else "Valid"))

    def show_detail(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        b = self.bc.chain[int(sel[0])]
        self.detail.delete("1.0", "end")
        self.detail.insert("end", "Block #%d\nTimestamp     : %s\nNonce         : %d\n" % (b.index, b.timestamp, b.nonce))
        self.detail.insert("end", "Previous Hash : %s\nStored Hash   : %s\n" % (b.previous_hash, b.hash))
        self.detail.insert("end", "Recomputed    : %s\n" % b.compute_hash())
        self.detail.insert("end", "\nData:\n" + json.dumps(b.data, indent=2))

    def tamper(self):
        idx = int(self.t_block.get())
        field = self.t_field.get()
        raw = self.t_value.get().strip()
        if not raw:
            messagebox.showwarning("Tamper", "Enter a new value.")
            return
        blk = self.bc.chain[idx]
        old = blk.data[field]
        try:
            new = type(old)(raw) if not isinstance(old, str) else raw
        except ValueError:
            messagebox.showerror("Tamper", "'%s' needs a numeric value." % field)
            return
        blk.data[field] = new  # data changed WITHOUT re-mining -> hash no longer matches
        self.report.delete("1.0", "end")
        self.report.insert("end", "TAMPERED: Block %d, field '%s': %r -> %r\n"
                                  "(hash NOT recomputed, as an attacker would try to hide it)\n"
                                  "Click 'Validate Blockchain' to detect it.\n" % (idx, field, old, new), "bad")
        self.set_status("Block %d was tampered. Run validation to detect it." % idx, False)
        self.result_lbl.config(text="Chain modified - validation pending", fg="#b36b00")
        self.refresh_analytics()

    def validate(self):
        ok, problems = self.bc.validate()
        self.bad_blocks = {i for i, _ in problems}
        self.report.delete("1.0", "end")
        if ok:
            self.result_lbl.config(text="BLOCKCHAIN IS VALID", fg="#0a7a2f")
            self.report.insert("end", "All %d blocks passed:\n  - hash recomputation\n  - previous-hash linkage\n"
                                      "  - proof-of-work (%d leading zeros)\n" % (len(self.bc.chain), self.bc.difficulty), "good")
            self.set_status("Validation passed: blockchain is intact.", True)
        else:
            self.result_lbl.config(text="BLOCKCHAIN IS INVALID - TAMPERING DETECTED", fg="#b00020")
            self.report.insert("end", "Found %d problem(s). First broken block: #%d\n\n" % (len(problems), problems[0][0]), "bad")
            for i, why in problems:
                self.report.insert("end", "  Block %d : %s\n" % (i, why), "bad")
            self.set_status("Validation FAILED: tampering detected at block %d." % problems[0][0], False)
        self.refresh_all()

    def restore(self):
        for i, data in self.original.items():
            self.bc.chain[i].data = copy.deepcopy(data)
        self.bad_blocks.clear()
        self.refresh_all()
        self.result_lbl.config(text="Original data restored - run validation", fg="black")
        self.report.delete("1.0", "end")
        self.set_status("Original data restored.", True)

    def refresh_analytics(self):
        self.a_tree.delete(*self.a_tree.get_children())
        for r in vendor_analytics(self.bc):
            self.a_tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], "%.2f" % r[5], r[6], r[7]), tags=(r[7],))
        changed = any(self.bc.chain[i].data != d for i, d in self.original.items())
        self.warn.config(text="WARNING: analytics are based on TAMPERED data!" if changed else "")
        self.draw_chart()

    def draw_chart(self):
        c = self.canvas
        c.delete("all")
        rows = vendor_analytics(self.bc)
        if not rows:
            return
        W, H = c.winfo_width(), c.winfo_height()
        if W < 50:
            return
        c.create_text(W / 2, 16, text="Vendor Performance Score (out of 100)", font=("Segoe UI", 11, "bold"))
        left, bottom, top = 50, H - 40, 40
        c.create_line(left, top, left, bottom, fill="#888")
        c.create_line(left, bottom, W - 20, bottom, fill="#888")
        for g in (0, 25, 50, 75, 100):
            y = bottom - (bottom - top) * g / 100
            c.create_line(left, y, W - 20, y, fill="#eee")
            c.create_text(left - 6, y, text=str(g), anchor="e", font=("Segoe UI", 8))
        n = len(rows)
        slot = (W - left - 30) / n
        colors = {"Excellent": "#2e9e4f", "Good": "#8bc34a", "Average": "#f2b134", "Poor": "#d9534f"}
        for i, r in enumerate(rows):
            x0 = left + i * slot + slot * 0.2
            x1 = left + (i + 1) * slot - slot * 0.2
            y = bottom - (bottom - top) * r[6] / 100
            c.create_rectangle(x0, y, x1, bottom, fill=colors[r[7]], outline="")
            c.create_text((x0 + x1) / 2, y - 10, text="%.1f" % r[6], font=("Segoe UI", 9, "bold"))
            c.create_text((x0 + x1) / 2, bottom + 14, text=r[0], font=("Segoe UI", 9))

    def set_status(self, msg, good):
        self.status.set("  " + msg)


if __name__ == "__main__":
    App().mainloop()