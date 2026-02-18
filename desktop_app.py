import customtkinter as ctk
from tkinter import messagebox, Text, Toplevel, Label
from PIL import Image
import os
import sys
import sqlite3
import subprocess
import difflib
import re
import secrets

# --- UI AYARLARI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Renk Paleti
COLOR_BG = "#1e1e1e"
COLOR_SIDEBAR = "#252526"
COLOR_ACCENT = "#D35400"
COLOR_MARGIN = "#2d2d30"
COLOR_ERROR_ICON = "#FF5555"
COLOR_ERROR_HOVER = "#F1C40F"
COLOR_TEXT = "#d4d4d4"
COLOR_CARD = "#2D2D30"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- TOOLTIP ---
class ToolTip(object):
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
    def showtip(self, text):
        if self.tipwindow or not text: return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        Label(tw, text=text, justify='left', background="#ffffe0", relief='solid', borderwidth=1, font=("tahoma", "10", "normal")).pack(ipadx=1)
    def hidetip(self):
        if self.tipwindow: self.tipwindow.destroy(); self.tipwindow = None

class CodeReviewApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🛡️ Johnson Electric - Code Studio V36.5 (Diff Fixed)")
        self.geometry("1450x900")
        self.configure(fg_color=COLOR_BG)
        
        logo_path = resource_path("logo.png")
        self.db_name = "users.db"
        self.current_user_role = None
        self.secili_dosya = None
        self.yerel_degisenler = [] 
        self.eski_versiyon_hash = self.run_git_command(["git", "rev-parse", "HEAD"])
        self.error_data = {} 
        self.tooltip = None

        self.init_database()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")

        try:
            pil = Image.open(logo_path).convert("RGBA")
            bg = Image.new("RGBA", pil.size, (255, 255, 255, 0))
            bg.paste(pil, (0, 0), pil)
            self.logo_large = ctk.CTkImage(light_image=bg, dark_image=bg, size=(400, 200))
            self.logo_small = ctk.CTkImage(light_image=bg, dark_image=bg, size=(180, 90))
        except: self.logo_large = None; self.logo_small = None
        
        self.setup_login_screen()
        self.show_login()

    # --- DATABASE ---
    def init_database(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, role TEXT)''')
        cursor.execute("SELECT * FROM users WHERE email='admin@johnson.com'")
        if not cursor.fetchone(): cursor.execute("INSERT INTO users VALUES (NULL, 'admin@johnson.com', '1234', 'admin')")
        conn.commit(); conn.close()

    def check_login(self, email, password):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE email=? AND password=?", (email, password))
        r = cursor.fetchone(); conn.close()
        return r[0] if r else None
    
    def save_new_user(self):
        email = self.new_email.get()
        if not email: return
        pwd = secrets.token_hex(4)
        try:
            conn = sqlite3.connect(self.db_name); c = conn.cursor()
            c.execute("INSERT INTO users VALUES (NULL, ?, ?, 'user')", (email, pwd))
            conn.commit(); conn.close()
            self.lbl_result.configure(text="✅ Kayıt Başarılı! Şifre:", text_color="#27AE60")
            self.entry_pass_res.configure(state="normal"); self.entry_pass_res.delete(0,"end"); self.entry_pass_res.insert(0, pwd)
        except: messagebox.showerror("Hata", "Mail kayıtlı.")

    def show_login(self): self.main_frame.grid_forget(); self.login_frame.grid(row=0, column=0, sticky="nswe")
    def show_main(self, role): 
        self.current_user_role = role
        for w in self.main_frame.winfo_children(): w.destroy()
        self.setup_main_screen()
        self.login_frame.grid_forget(); self.main_frame.grid(row=0, column=0, sticky="nswe")
        self.scan_files_action(); self.show_history_dashboard()

    def login_event(self):
        r = self.check_login(self.entry_email.get(), self.entry_pass.get())
        if r: self.show_main(r)
        else: messagebox.showerror("Hata", "Giriş başarısız!")

    # --- UI ---
    def setup_login_screen(self):
        self.login_frame.grid_columnconfigure(0, weight=1); self.login_frame.grid_rowconfigure(0, weight=1)
        card = ctk.CTkFrame(self.login_frame, width=450, height=550, corner_radius=20, fg_color=COLOR_SIDEBAR)
        card.grid(row=0, column=0); card.grid_propagate(False)
        if self.logo_large: ctk.CTkLabel(card, text="", image=self.logo_large).pack(pady=(40, 20))
        ctk.CTkLabel(card, text="Giriş Yap", font=("Roboto", 28, "bold"), text_color="white").pack(pady=10)
        self.entry_email = ctk.CTkEntry(card, placeholder_text="E-posta", width=320); self.entry_email.pack(pady=10)
        self.entry_pass = ctk.CTkEntry(card, placeholder_text="Şifre", show="*", width=320); self.entry_pass.pack(pady=10)
        ctk.CTkButton(card, text="GİRİŞ ->", width=320, fg_color=COLOR_ACCENT, command=self.login_event).pack(pady=30)

    def setup_main_screen(self):
        sidebar = ctk.CTkFrame(self.main_frame, width=300, corner_radius=0, fg_color=COLOR_SIDEBAR)
        sidebar.pack(side="left", fill="y")
        if self.logo_small: ctk.CTkLabel(sidebar, text="", image=self.logo_small).pack(pady=(30, 10))
        
        ctk.CTkButton(sidebar, text="📊 Proje Geçmişi", fg_color="#3E3E42", command=self.show_history_dashboard).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(sidebar, text="🔄 Dosyaları Tara", fg_color="transparent", border_width=1, command=self.scan_files_action).pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(sidebar, text="KAYNAK KODLAR (C/C++)", font=("Roboto", 12, "bold"), text_color="#2ECC71").pack(pady=(20, 5), anchor="w", padx=20)
        self.source_code_frame = ctk.CTkScrollableFrame(sidebar, width=260, height=150, fg_color="#1E1E1E")
        self.source_code_frame.pack(pady=5, padx=10, fill="x")

        ctk.CTkLabel(sidebar, text="DİĞER DOSYALAR", font=("Roboto", 12, "bold"), text_color="gray").pack(pady=(10, 5), anchor="w", padx=20)
        self.other_files_frame = ctk.CTkScrollableFrame(sidebar, width=260, height=120, fg_color="#1E1E1E")
        self.other_files_frame.pack(pady=5, padx=10, fill="x")

        self.btn_misra = ctk.CTkButton(sidebar, text="🛡️ MISRA KONTROL ET", fg_color="#F39C12", text_color="black", state="disabled", command=self.run_misra_check)
        self.btn_misra.pack(fill="x", padx=15, pady=(20, 5))
        ctk.CTkButton(sidebar, text="⬇️ GÜNCELLE (PULL)", fg_color=COLOR_ACCENT, command=self.git_pull_action).pack(fill="x", padx=15, pady=5)
        self.btn_diff = ctk.CTkButton(sidebar, text="🔍 DEĞİŞİMİ GÖR", state="disabled", command=self.open_diff_window); self.btn_diff.pack(fill="x", padx=15, pady=5)
        if self.current_user_role == 'admin': ctk.CTkButton(sidebar, text="+ Personel", fg_color="#555", command=self.open_add_user_window).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(sidebar, text="Çıkış", fg_color="transparent", text_color="red", command=self.show_login).pack(side="bottom", pady=20)

        self.right_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.right_panel.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    # --- DOSYA TARAMA ---
    def scan_files_action(self):
        for w in self.source_code_frame.winfo_children(): w.destroy()
        for w in self.other_files_frame.winfo_children(): w.destroy()
        try:
            dosyalar = sorted(os.listdir(os.getcwd()))
            for dosya in dosyalar:
                if dosya.endswith((".c", ".h", ".cpp", ".hpp")):
                    ctk.CTkButton(self.source_code_frame, text=f"⚙️ {dosya}", fg_color="transparent", anchor="w", hover_color="#333", command=lambda d=dosya: self.read_file_content(d)).pack(fill="x", pady=1)
                elif dosya.endswith((".py", ".txt", ".md", ".json", ".xml")):
                    ctk.CTkButton(self.other_files_frame, text=f"📄 {dosya}", fg_color="transparent", anchor="w", hover_color="#333", command=lambda d=dosya: self.read_file_content(d)).pack(fill="x", pady=1)
        except Exception as e: print(f"Hata: {e}")

    # --- DİĞER FONKSİYONLAR ---
    def show_history_dashboard(self):
        for w in self.right_panel.winfo_children(): w.destroy()
        self.secili_dosya = None; self.btn_diff.configure(state="disabled"); self.btn_misra.configure(state="disabled", fg_color="#555")
        
        header = ctk.CTkFrame(self.right_panel, fg_color="transparent"); header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="Proje Zaman Çizelgesi", font=("Roboto", 28, "bold"), text_color="white").pack(side="left")
        ctk.CTkButton(header, text="↻ Yenile", width=100, fg_color="#34495E", command=self.show_history_dashboard).pack(side="right")
        
        scroll = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent"); scroll.pack(fill="both", expand=True)
        try: logs = self.run_git_command(["git", "log", "-n", "10", "--pretty=format:%h|%an|%ad|%s", "--date=format:%Y-%m-%d %H:%M", "--name-only"])
        except: logs = ""
        if not logs: ctk.CTkLabel(scroll, text="⚠️ Git geçmişi bulunamadı.", font=("Arial", 16)).pack(pady=50); return
        
        commits = self.parse_git_log(logs)
        for c in commits:
            card = ctk.CTkFrame(scroll, fg_color=COLOR_CARD, corner_radius=15); card.pack(fill="x", pady=8, padx=5)
            ctk.CTkFrame(card, width=6, fg_color=COLOR_ACCENT, corner_radius=5).pack(side="left", fill="y", padx=(0, 10))
            info = ctk.CTkFrame(card, fg_color="transparent"); info.pack(side="left", fill="both", expand=True, pady=10)
            ctk.CTkLabel(info, text=c['msg'], font=("Roboto", 16, "bold"), text_color="white", anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=f"👤 {c['author']}   🕒 {c['date']}", font=("Roboto", 12), text_color="gray", anchor="w").pack(fill="x", pady=(5,0))
            ctk.CTkButton(ctk.CTkFrame(card, fg_color="transparent"), text=f"#{c['hash']}", width=80, fg_color="#444", hover=False).pack(side="right", padx=20)

    def parse_git_log(self, raw):
        commits = []; lines = raw.splitlines(); curr = None
        for l in lines:
            if "|" in l and len(l.split("|")) >= 4:
                if curr: commits.append(curr)
                p = l.split("|"); curr = {"hash": p[0], "author": p[1], "date": p[2], "msg": p[3]}
        if curr: commits.append(curr)
        return commits

    def setup_editor_ui(self, dosya):
        for w in self.right_panel.winfo_children(): w.destroy()
        h = ctk.CTkFrame(self.right_panel, height=50, fg_color="transparent"); h.pack(fill="x", pady=5)
        ctk.CTkLabel(h, text=f"📝 {dosya}", font=("Roboto", 20, "bold"), text_color=COLOR_ACCENT).pack(side="left")
        self.lbl_status = ctk.CTkLabel(h, text="", font=("Roboto", 12), text_color="#F39C12"); self.lbl_status.pack(side="left", padx=20)
        ctk.CTkButton(h, text="💾 KAYDET", width=100, command=self.save_file_content).pack(side="right")
        
        cont = ctk.CTkFrame(self.right_panel, corner_radius=0, fg_color=COLOR_BG); cont.pack(fill="both", expand=True, pady=10)
        self.margin_box = Text(cont, width=4, font=("Consolas", 13), bg=COLOR_MARGIN, fg=COLOR_ERROR_ICON, bd=0, padx=5, pady=10, state="disabled"); self.margin_box.pack(side="left", fill="y")
        self.code_box = Text(cont, font=("Consolas", 13), wrap="none", bg="#1E1E1E", fg=COLOR_TEXT, insertbackground="white", undo=True, bd=0, padx=10, pady=10); self.code_box.pack(side="left", fill="both", expand=True)
        sb = ctk.CTkScrollbar(cont, command=self.sync_scroll); sb.pack(side="right", fill="y")
        self.code_box.configure(yscrollcommand=sb.set); self.margin_box.configure(yscrollcommand=sb.set)
        
        self.code_box.bind("<MouseWheel>", self.on_scroll); self.code_box.bind("<Button-4>", self.on_scroll); self.code_box.bind("<Button-5>", self.on_scroll)
        self.setup_highlight()

    def sync_scroll(self, *args): self.code_box.yview(*args); self.margin_box.yview(*args)
    def on_scroll(self, e): self.code_box.yview_scroll(int(-1*(e.delta/120)), "units"); self.margin_box.yview_scroll(int(-1*(e.delta/120)), "units"); return "break"

    def run_misra_check(self):
        if not self.secili_dosya: return
        self.error_data = {}; txt = self.code_box.get("1.0", "end").split("\n"); count = 0
        for i, l in enumerate(txt):
            ln = i+1; msg=None; sol=None
            if "goto " in l and "//" not in l: msg="MISRA Rule 15.1: 'goto' yasak."; sol="Spagetti koddan kaçının."
            elif re.search(r"\bint\b", l) and "int32_t" not in l and "main" not in l and "//" not in l: msg="MISRA Rule 4.6: Belirsiz 'int'."; sol="<stdint.h> kullanın (int32_t)."
            elif "\t" in l: msg="MISRA Dir 4.1: Tab yasak."; sol="Space kullanın."
            elif len(l)>120: msg="Style: Satır çok uzun."; sol="Kodu bölün."
            if msg: self.error_data[ln]={"msg":msg, "sol":sol}; count+=1
        
        self.update_margin()
        self.lbl_status.configure(text=f"🚨 {count} Hata!" if count else "✅ Temiz.", text_color=COLOR_ERROR_ICON if count else "green")

    def update_margin(self):
        self.margin_box.config(state="normal"); self.margin_box.delete("1.0", "end")
        lc = int(self.code_box.index('end-1c').split('.')[0])
        for i in range(1, lc+1):
            if i in self.error_data:
                self.margin_box.insert("end", "! \n"); tag=f"err_{i}"; self.margin_box.tag_add(tag, f"{i}.0", f"{i}.end")
                self.margin_box.tag_bind(tag, "<Enter>", lambda e, ln=i: self.on_hover(e, ln))
                self.margin_box.tag_bind(tag, "<Leave>", self.on_leave)
                self.margin_box.tag_bind(tag, "<Button-1>", lambda e, ln=i: self.show_popup(ln))
                self.margin_box.tag_config(tag, foreground=COLOR_ERROR_ICON)
            else: self.margin_box.insert("end", "\n")
        self.margin_box.config(state="disabled")

    def on_hover(self, e, ln):
        self.margin_box.tag_config(f"err_{ln}", foreground=COLOR_ERROR_HOVER)
        if not self.tooltip: self.tooltip=ToolTip(self.margin_box)
        self.tooltip.showtip(self.error_data[ln]["msg"])
    def on_leave(self, e): 
        if self.tooltip: self.tooltip.hidetip()
        for ln in self.error_data: self.margin_box.tag_config(f"err_{ln}", foreground=COLOR_ERROR_ICON)
    
    def show_popup(self, ln):
        d = self.error_data[ln]; win = ctk.CTkToplevel(self); win.geometry("400x250"); win.attributes("-topmost", True)
        ctk.CTkLabel(win, text="🚫 HATA:", text_color="#FF5555", font=("bold",14)).pack(pady=10)
        ctk.CTkLabel(win, text=d["msg"]).pack()
        ctk.CTkLabel(win, text="✅ ÇÖZÜM:", text_color="#2ECC71", font=("bold",14)).pack(pady=10)
        t = ctk.CTkTextbox(win, height=80); t.pack(pady=5); t.insert("1.0", d["sol"]); t.configure(state="disabled")

    def read_file_content(self, dosya):
        self.setup_editor_ui(dosya); self.secili_dosya = dosya; self.btn_diff.configure(state="normal")
        if dosya.endswith((".c", ".h", ".cpp")): self.btn_misra.configure(state="normal", fg_color="#F39C12")
        else: self.btn_misra.configure(state="disabled", fg_color="#555")
        try:
            with open(dosya, "r", encoding="utf-8") as f: c=f.read(); self.code_box.insert("1.0", c); self.setup_highlight()
            self.margin_box.config(state="normal"); self.margin_box.insert("1.0", "\n"*(c.count("\n")+1)); self.margin_box.config(state="disabled")
        except: pass

    def save_file_content(self):
        if not self.secili_dosya: return
        with open(self.secili_dosya, "w", encoding="utf-8") as f: f.write(self.code_box.get("1.0", "end-1c"))
        self.scan_files_action(); messagebox.showinfo("Bilgi", "Kaydedildi.")

    def setup_highlight(self):
        self.code_box.tag_config("kw", foreground="#569CD6", font=("Consolas", 13, "bold")); self.code_box.tag_config("cmt", foreground="#6A9955", font=("Consolas", 13, "italic"))
        c = self.code_box.get("1.0", "end")
        for m in re.finditer(r"#.*|//.*", c): self.code_box.tag_add("cmt", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        for w in ["if","else","while","for","return","int","void","float","char","include","struct","main"]:
             for m in re.finditer(r"\b"+w+r"\b", c): self.code_box.tag_add("kw", f"1.0+{m.start()}c", f"1.0+{m.end()}c")

    def run_git_command(self, c): 
        try: return subprocess.check_output(c, text=True, encoding='utf-8', errors='ignore').strip()
        except: return None
    
    # --- 🔥 DÜZELTİLEN KISIM: DIFF LOGIC 🔥 ---
    def git_pull_action(self):
        self.eski_versiyon_hash = self.run_git_command(["git", "rev-parse", "HEAD"])
        subprocess.run(["git","pull"], shell=True)
        self.scan_files_action(); messagebox.showinfo("Bilgi","Pull OK.")

    def open_diff_window(self):
        if not self.secili_dosya: return
        diff_win = ctk.CTkToplevel(self)
        diff_win.title(f"DEĞİŞİM RAPORU: {self.secili_dosya}")
        diff_win.geometry("1450x800"); diff_win.configure(fg_color="#1E1E1E")

        panel = ctk.CTkFrame(diff_win, fg_color="transparent"); panel.pack(fill="both", expand=True, padx=10, pady=10)
        
        # SOL TARAF (ESKİ)
        txt_left = Text(panel, width=60, bg="#252526", fg="#d4d4d4", font=("Consolas", 12))
        txt_left.pack(side="left", fill="both", expand=True, padx=5)
        
        # SAĞ TARAF (YENİ)
        txt_right = Text(panel, width=60, bg="#252526", fg="#d4d4d4", font=("Consolas", 12))
        txt_right.pack(side="right", fill="both", expand=True, padx=5)

        txt_right.tag_config("new_line", background="#0c4a28", foreground="white") 
        txt_left.tag_config("old_line", background="#591313", foreground="white") 

        try:
            # Önceki versiyon ile şu anki versiyonu kıyasla
            old = self.eski_versiyon_hash if self.eski_versiyon_hash else "HEAD^"
            left = self.run_git_command(["git", "show", f'{old}:{self.secili_dosya}']) or "--- DOSYA YOKTU ---"
            right = self.run_git_command(["git", "show", f'HEAD:{self.secili_dosya}']) or "--- SİLİNDİ ---"
            
            diff = difflib.ndiff(left.splitlines(), right.splitlines())
            
            for line in diff:
                if line.startswith("- "): txt_left.insert("end", line[2:]+"\n", "old_line")
                elif line.startswith("+ "): txt_right.insert("end", line[2:]+"\n", "new_line")
                elif line.startswith("  "): 
                    txt_left.insert("end", line[2:]+"\n")
                    txt_right.insert("end", line[2:]+"\n")
        except: pass

    def open_add_user_window(self):
        w = ctk.CTkToplevel(self); w.geometry("300x200"); ctk.CTkEntry(w, placeholder_text="Email").pack(pady=10); self.entry_pass_res=ctk.CTkEntry(w); self.entry_pass_res.pack(pady=5)
        self.new_email=w.winfo_children()[0] 

if __name__ == "__main__":
    app = CodeReviewApp()
    app.mainloop()