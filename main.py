import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
from datetime import datetime, timedelta
import random

APP_TITLE = "CAMPUS CONNECT"
DB_FILE = "campus_connect.db"

BG = "#eef5f9"
BLUE = "#0b91d1"
DARK = "#17324d"
WHITE = "#ffffff"
RED = "#e74c3c"
GREEN = "#20a46b"
GRAY = "#6d7a86"

def money(v):
    return f"{v:.0f}"

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        self.setup()

    def setup(self):
        c = self.conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY, name TEXT, student_id TEXT, points INTEGER DEFAULT 75)""")
        c.execute("""CREATE TABLE IF NOT EXISTS items(
            id INTEGER PRIMARY KEY, name TEXT, category TEXT, available INTEGER DEFAULT 1,
            borrower_id INTEGER, due TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS lockers(
            number TEXT PRIMARY KEY, status TEXT DEFAULT 'ว่าง', owner TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS prints(
            id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, pages INTEGER,
            points INTEGER, created TEXT)""")

        if c.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            c.execute("INSERT INTO users(name,student_id,points) VALUES(?,?,?)",
                      ("สมชาย ใจดี", "65010001", 75))

        if c.execute("SELECT COUNT(*) FROM items").fetchone()[0] == 0:
            for name, cat in [
                ("ลูกบาสเกตบอล SPALDING", "กีฬา"),
                ("ลูกฟุตบอล", "กีฬา"),
                ("ไม้แบดมินตัน", "กีฬา"),
                ("เครื่องคิดเลข", "การเรียน"),
            ]:
                c.execute("INSERT INTO items(name,category) VALUES(?,?)", (name, cat))

        if c.execute("SELECT COUNT(*) FROM lockers").fetchone()[0] == 0:
            for n in ["A01", "A02", "A03", "B12", "B13", "B14"]:
                c.execute("INSERT INTO lockers(number) VALUES(?)", (n,))
        self.conn.commit()

    def user(self):
        return self.conn.execute("SELECT * FROM users LIMIT 1").fetchone()

    def items(self):
        return self.conn.execute("SELECT * FROM items ORDER BY id").fetchall()

    def lockers(self):
        return self.conn.execute("SELECT * FROM lockers ORDER BY number").fetchall()

    def borrow(self, item_id):
        u = self.user()
        due = (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
        self.conn.execute("UPDATE items SET available=0, borrower_id=?, due=? WHERE id=?",
                          (u["id"], due, item_id))
        self.conn.commit()

    def return_item(self, item_id):
        self.conn.execute("UPDATE items SET available=1, borrower_id=NULL, due=NULL WHERE id=?",
                          (item_id,))
        self.conn.commit()

    def update_points(self, delta):
        self.conn.execute("UPDATE users SET points=points+? WHERE id=?", (delta, self.user()["id"]))
        self.conn.commit()

    def add_print(self, filename, pages):
        points = pages
        self.conn.execute("INSERT INTO prints(filename,pages,points,created) VALUES(?,?,?,?)",
                          (filename, pages, points, datetime.now().strftime("%Y-%m-%d %H:%M")))
        self.update_points(-points)
        self.conn.commit()

    def unlock(self, number):
        row = self.conn.execute("SELECT * FROM lockers WHERE number=?", (number,)).fetchone()
        if not row:
            return False
        if row["status"] == "ว่าง":
            self.conn.execute("UPDATE lockers SET status='ใช้งาน', owner=? WHERE number=?",
                              (self.user()["student_id"], number))
        else:
            self.conn.execute("UPDATE lockers SET status='ว่าง', owner=NULL WHERE number=?",
                              (number,))
        self.conn.commit()
        return True

class CampusConnect(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1100x720")
        self.minsize(900, 620)
        self.configure(bg=BG)
        self.db = Database()
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure("TNotebook", background=BG, borderwidth=0)
        self.style.configure("TNotebook.Tab", padding=(22, 12), font=("Tahoma", 11, "bold"))
        self.style.configure("Treeview", rowheight=34, font=("Tahoma", 10))
        self.style.configure("Treeview.Heading", font=("Tahoma", 10, "bold"))
        self.build_header()
        self.build_notebook()
        self.refresh_all()

    def build_header(self):
        header = tk.Frame(self, bg=BLUE, height=74)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="⚽ CAMPUS CONNECT", bg=BLUE, fg=WHITE,
                 font=("Arial", 22, "bold")).pack(side="left", padx=25)
        self.points_label = tk.Label(header, text="", bg=BLUE, fg=WHITE,
                                     font=("Tahoma", 12, "bold"))
        self.points_label.pack(side="right", padx=25)

    def build_notebook(self):
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=15, pady=15)

        self.home_tab = tk.Frame(self.nb, bg=BG)
        self.borrow_tab = tk.Frame(self.nb, bg=BG)
        self.print_tab = tk.Frame(self.nb, bg=BG)
        self.locker_tab = tk.Frame(self.nb, bg=BG)
        self.admin_tab = tk.Frame(self.nb, bg=BG)

        self.nb.add(self.home_tab, text="หน้าหลัก")
        self.nb.add(self.borrow_tab, text="ยืม-คืนอุปกรณ์")
        self.nb.add(self.print_tab, text="ควบคุมการพิมพ์")
        self.nb.add(self.locker_tab, text="ตู้ล็อกเกอร์")
        self.nb.add(self.admin_tab, text="ผู้ดูแลระบบ")

        self.build_home()
        self.build_borrow()
        self.build_print()
        self.build_locker()
        self.build_admin()

    def card(self, parent, title, value, subtitle, color=BLUE):
        f = tk.Frame(parent, bg=WHITE, highlightbackground="#d5e0e8",
                     highlightthickness=1)
        f.pack(side="left", fill="both", expand=True, padx=7, pady=7)
        tk.Label(f, text=title, bg=WHITE, fg=DARK,
                 font=("Tahoma", 11, "bold")).pack(anchor="w", padx=18, pady=(18, 4))
        tk.Label(f, text=value, bg=WHITE, fg=color,
                 font=("Arial", 27, "bold")).pack(anchor="w", padx=18)
        tk.Label(f, text=subtitle, bg=WHITE, fg=GRAY,
                 font=("Tahoma", 10)).pack(anchor="w", padx=18, pady=(2, 18))
        return f

    def button(self, parent, text, command, color=BLUE):
        return tk.Button(parent, text=text, command=command, bg=color, fg=WHITE,
                         activebackground=color, activeforeground=WHITE,
                         relief="flat", bd=0, cursor="hand2",
                         font=("Tahoma", 11, "bold"), padx=18, pady=10)

    def build_home(self):
        tk.Label(self.home_tab, text="สวัสดี, สมชาย ใจดี 👋",
                 bg=BG, fg=DARK, font=("Tahoma", 23, "bold")).pack(anchor="w", padx=25, pady=(25, 5))
        tk.Label(self.home_tab, text="ระบบ Campus Connect สำหรับยืมอุปกรณ์ พิมพ์งาน และเปิดล็อกเกอร์",
                 bg=BG, fg=GRAY, font=("Tahoma", 11)).pack(anchor="w", padx=27, pady=(0, 18))

        row = tk.Frame(self.home_tab, bg=BG)
        row.pack(fill="x", padx=18)
        self.home_points = self.card(row, "โควตาการพิมพ์", "75/100", "แต้มคงเหลือ")
        self.home_items = self.card(row, "อุปกรณ์กีฬา", "พร้อมยืม", "ระบบติดตามสถานะ", GREEN)
        self.home_lockers = self.card(row, "ล็อกเกอร์", "B12", "ตัวอย่างตู้ที่ใช้งาน", "#7c5cff")

        alert = tk.Frame(self.home_tab, bg="#fff3cd", highlightbackground="#ffe08a", highlightthickness=1)
        alert.pack(fill="x", padx=25, pady=25)
        tk.Label(alert, text="⚠ แจ้งเตือน", bg="#fff3cd", fg="#7a5b00",
                 font=("Tahoma", 13, "bold")).pack(anchor="w", padx=18, pady=(14, 2))
        tk.Label(alert, text="ใกล้หมดเวลายืมอุปกรณ์ โปรดคืนก่อนครบกำหนด",
                 bg="#fff3cd", fg="#7a5b00", font=("Tahoma", 11)).pack(anchor="w", padx=18, pady=(0, 14))

        actions = tk.Frame(self.home_tab, bg=BG)
        actions.pack(pady=5)
        self.button(actions, "⚽ ยืม-คืนอุปกรณ์", lambda: self.nb.select(self.borrow_tab)).pack(side="left", padx=8)
        self.button(actions, "🖨 ปรับงาน/พิมพ์", lambda: self.nb.select(self.print_tab)).pack(side="left", padx=8)
        self.button(actions, "🔒 เปิดล็อกเกอร์", lambda: self.nb.select(self.locker_tab)).pack(side="left", padx=8)

    def build_borrow(self):
        tk.Label(self.borrow_tab, text="ยืม-คืนอุปกรณ์",
                 bg=BG, fg=DARK, font=("Tahoma", 22, "bold")).pack(anchor="w", padx=25, pady=(22, 4))
        tk.Label(self.borrow_tab, text="สแกน QR (จำลอง) หรือเลือกอุปกรณ์จากรายการ",
                 bg=BG, fg=GRAY, font=("Tahoma", 11)).pack(anchor="w", padx=27, pady=(0, 12))

        top = tk.Frame(self.borrow_tab, bg=WHITE)
        top.pack(fill="x", padx=25, pady=8)
        self.button(top, "📷 สแกน QR", self.scan_qr).pack(side="left", padx=15, pady=15)
        self.borrow_status = tk.Label(top, text="พร้อมสแกน", bg=WHITE, fg=GRAY,
                                      font=("Tahoma", 11))
        self.borrow_status.pack(side="left", padx=10)

        self.item_tree = ttk.Treeview(self.borrow_tab,
                                      columns=("id","name","cat","status","due"),
                                      show="headings")
        for col, title, width in [
            ("id","ID",60),("name","อุปกรณ์",300),("cat","ประเภท",130),
            ("status","สถานะ",130),("due","กำหนดคืน",200)]:
            self.item_tree.heading(col, text=title)
            self.item_tree.column(col, width=width)
        self.item_tree.pack(fill="both", expand=True, padx=25, pady=10)

        bar = tk.Frame(self.borrow_tab, bg=BG)
        bar.pack(pady=10)
        self.button(bar, "ยืมรายการที่เลือก", self.borrow_selected, GREEN).pack(side="left", padx=7)
        self.button(bar, "คืนรายการที่เลือก", self.return_selected, "#e67e22").pack(side="left", padx=7)

    def scan_qr(self):
        items = self.db.items()
        available = [x for x in items if x["available"]]
        if not available:
            messagebox.showinfo("QR", "ไม่มีอุปกรณ์พร้อมยืม")
            return
        item = available[0]
        self.borrow_status.config(text=f"พบ QR: {item['name']}", fg=GREEN)
        messagebox.showinfo("สแกน QR สำเร็จ", f"พบอุปกรณ์\n{item['name']}\n\nกด 'ยืมรายการที่เลือก' หลังเลือกในตาราง")

    def selected_item_id(self):
        sel = self.item_tree.selection()
        if not sel:
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกอุปกรณ์ก่อน")
            return None
        return int(self.item_tree.item(sel[0], "values")[0])

    def borrow_selected(self):
        iid = self.selected_item_id()
        if iid is None: return
        row = self.db.conn.execute("SELECT * FROM items WHERE id=?", (iid,)).fetchone()
        if not row["available"]:
            messagebox.showwarning("ไม่สำเร็จ", "อุปกรณ์นี้ถูกยืมแล้ว")
            return
        self.db.borrow(iid)
        messagebox.showinfo("สำเร็จ", f"ยืม {row['name']} สำเร็จ\nกำหนดคืนภายใน 2 ชั่วโมง")
        self.refresh_all()

    def return_selected(self):
        iid = self.selected_item_id()
        if iid is None: return
        self.db.return_item(iid)
        messagebox.showinfo("สำเร็จ", "คืนอุปกรณ์เรียบร้อยแล้ว")
        self.refresh_all()

    def build_print(self):
        tk.Label(self.print_tab, text="ควบคุมการพิมพ์",
                 bg=BG, fg=DARK, font=("Tahoma", 22, "bold")).pack(anchor="w", padx=25, pady=(22, 4))
        tk.Label(self.print_tab, text="ทุก 1 หน้า = 1 แต้ม • ระบบจะหักแต้มอัตโนมัติ",
                 bg=BG, fg=GRAY, font=("Tahoma", 11)).pack(anchor="w", padx=27)

        box = tk.Frame(self.print_tab, bg=WHITE, highlightbackground="#d5e0e8", highlightthickness=1)
        box.pack(fill="x", padx=25, pady=20)

        self.print_points = tk.Label(box, text="75", bg=WHITE, fg=BLUE, font=("Arial", 42, "bold"))
        self.print_points.pack(pady=(25, 0))
        tk.Label(box, text="แต้มคงเหลือ (เต็ม 100 แต้ม)", bg=WHITE, fg=GRAY,
                 font=("Tahoma", 11)).pack(pady=(0, 20))

        form = tk.Frame(box, bg=WHITE)
        form.pack(pady=5)
        tk.Label(form, text="ชื่อไฟล์:", bg=WHITE, font=("Tahoma", 11)).grid(row=0,column=0,padx=7,pady=7)
        self.file_entry = ttk.Entry(form, width=38)
        self.file_entry.insert(0, "รายงาน_Final.pdf")
        self.file_entry.grid(row=0,column=1,padx=7,pady=7)
        tk.Label(form, text="จำนวนหน้า:", bg=WHITE, font=("Tahoma", 11)).grid(row=1,column=0,padx=7,pady=7)
        self.pages_entry = ttk.Entry(form, width=10)
        self.pages_entry.insert(0, "5")
        self.pages_entry.grid(row=1,column=1,sticky="w",padx=7,pady=7)
        self.button(form, "🖨 ส่งพิมพ์", self.print_document, BLUE).grid(row=2,column=0,columnspan=2,pady=15)

        self.print_history = ttk.Treeview(self.print_tab, columns=("file","pages","points","date"), show="headings")
        for col,title in [("file","ไฟล์"),("pages","หน้า"),("points","แต้มที่ใช้"),("date","เวลา")]:
            self.print_history.heading(col,text=title)
        self.print_history.pack(fill="both", expand=True, padx=25, pady=8)

    def print_document(self):
        filename = self.file_entry.get().strip() or "document.pdf"
        try:
            pages = int(self.pages_entry.get())
            if pages <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("ข้อมูลไม่ถูกต้อง", "จำนวนหน้าต้องเป็นเลขจำนวนเต็มมากกว่า 0")
            return
        points = self.db.user()["points"]
        if pages > points:
            messagebox.showwarning("แต้มไม่พอ", f"ต้องใช้ {pages} แต้ม แต่เหลือ {points} แต้ม")
            return
        self.db.add_print(filename, pages)
        messagebox.showinfo("ส่งพิมพ์แล้ว", f"{filename}\nจำนวน {pages} หน้า\nใช้ {pages} แต้ม")
        self.refresh_all()

    def build_locker(self):
        tk.Label(self.locker_tab, text="ตู้ล็อกเกอร์อัจฉริยะ",
                 bg=BG, fg=DARK, font=("Tahoma", 22, "bold")).pack(anchor="w", padx=25, pady=(22, 4))
        tk.Label(self.locker_tab, text="เลือกตู้เพื่อจำลองการล็อก/ปลดล็อกผ่านแอป",
                 bg=BG, fg=GRAY, font=("Tahoma", 11)).pack(anchor="w", padx=27)

        self.locker_frame = tk.Frame(self.locker_tab, bg=BG)
        self.locker_frame.pack(fill="both", expand=True, padx=25, pady=20)

    def unlock_locker(self, number):
        self.db.unlock(number)
        self.refresh_all()
        row = self.db.conn.execute("SELECT * FROM lockers WHERE number=?", (number,)).fetchone()
        action = "เปิด/ใช้งาน" if row["status"] == "ใช้งาน" else "ล็อก"
        messagebox.showinfo("ล็อกเกอร์", f"ตู้ {number}: {action} สำเร็จ")

    def build_admin(self):
        tk.Label(self.admin_tab, text="ผู้ดูแลระบบ (ADMIN)",
                 bg=BG, fg=DARK, font=("Tahoma", 22, "bold")).pack(anchor="w", padx=25, pady=(22, 4))
        tk.Label(self.admin_tab, text="ควบคุมคิวงานพิมพ์ เช็กสถานะล็อกเกอร์ และจัดการอุปกรณ์",
                 bg=BG, fg=GRAY, font=("Tahoma", 11)).pack(anchor="w", padx=27)

        stats = tk.Frame(self.admin_tab, bg=BG)
        stats.pack(fill="x", padx=18, pady=18)
        self.admin_items = self.card(stats, "อุปกรณ์ทั้งหมด", "0", "รายการ")
        self.admin_available = self.card(stats, "พร้อมยืม", "0", "รายการ", GREEN)
        self.admin_lockers = self.card(stats, "ล็อกเกอร์ใช้งาน", "0", "ตู้", "#7c5cff")

        self.admin_log = tk.Text(self.admin_tab, height=14, bg="#102333", fg="#d8f3ff",
                                 font=("Consolas", 10), relief="flat")
        self.admin_log.pack(fill="both", expand=True, padx=25, pady=10)
        self.button(self.admin_tab, "🔄 รีเฟรชข้อมูล", self.refresh_all).pack(pady=10)

    def refresh_all(self):
        u = self.db.user()
        self.points_label.config(text=f"แต้มคงเหลือ: {u['points']}/100")
        if hasattr(self, "print_points"):
            self.print_points.config(text=str(u["points"]))

        if hasattr(self, "item_tree"):
            for x in self.item_tree.get_children(): self.item_tree.delete(x)
            for row in self.db.items():
                status = "พร้อมยืม" if row["available"] else "กำลังยืม"
                due = row["due"] or "-"
                self.item_tree.insert("", "end", values=(row["id"], row["name"], row["category"], status, due))

        if hasattr(self, "print_history"):
            for x in self.print_history.get_children(): self.print_history.delete(x)
            rows = self.db.conn.execute("SELECT * FROM prints ORDER BY id DESC LIMIT 20").fetchall()
            for r in rows:
                self.print_history.insert("", "end", values=(r["filename"],r["pages"],r["points"],r["created"]))

        if hasattr(self, "locker_frame"):
            for w in self.locker_frame.winfo_children(): w.destroy()
            for row in self.db.lockers():
                color = GREEN if row["status"] == "ว่าง" else "#e67e22"
                card = tk.Frame(self.locker_frame, bg=WHITE, highlightbackground="#d5e0e8", highlightthickness=1)
                card.pack(side="left", fill="both", expand=True, padx=7, pady=7)
                tk.Label(card, text="🔒", bg=WHITE, fg=BLUE, font=("Arial", 35)).pack(pady=(18,2))
                tk.Label(card, text=f"ตู้หมายเลข {row['number']}", bg=WHITE, fg=DARK,
                         font=("Tahoma", 13, "bold")).pack()
                tk.Label(card, text=row["status"], bg=WHITE, fg=color,
                         font=("Tahoma", 11, "bold")).pack(pady=5)
                if row["owner"]:
                    tk.Label(card, text=f"ผู้ใช้: {row['owner']}", bg=WHITE, fg=GRAY,
                             font=("Tahoma", 9)).pack()
                self.button(card, "เปิด / ล็อก", lambda n=row["number"]: self.unlock_locker(n),
                            BLUE).pack(pady=15)

        if hasattr(self, "admin_items"):
            items = self.db.items()
            available = [x for x in items if x["available"]]
            lockers = self.db.lockers()
            used = [x for x in lockers if x["status"] != "ว่าง"]
            self._set_card_value(self.admin_items, str(len(items)))
            self._set_card_value(self.admin_available, str(len(available)))
            self._set_card_value(self.admin_lockers, str(len(used)))
            self.admin_log.delete("1.0", "end")
            self.admin_log.insert("end", f"CAMPUS CONNECT ADMIN\n{'='*45}\n")
            self.admin_log.insert("end", f"เวลา: {datetime.now():%Y-%m-%d %H:%M:%S}\n")
            self.admin_log.insert("end", f"อุปกรณ์ทั้งหมด: {len(items)}\n")
            self.admin_log.insert("end", f"อุปกรณ์พร้อมยืม: {len(available)}\n")
            self.admin_log.insert("end", f"ล็อกเกอร์ใช้งาน: {len(used)}\n")
            self.admin_log.insert("end", f"แต้มผู้ใช้: {u['points']}/100\n")
            self.admin_log.insert("end", "\nระบบทำงานปกติ ✓")

        if hasattr(self, "home_points"):
            self._set_card_value(self.home_points, f"{u['points']}/100")

    def _set_card_value(self, card, value):
        labels = [w for w in card.winfo_children() if isinstance(w, tk.Label)]
        if len(labels) >= 2:
            labels[1].config(text=value)

if __name__ == "__main__":
    app = CampusConnect()
    app.mainloop()
