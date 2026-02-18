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

COLOR_BG = "#1e1e1e"
COLOR_SIDEBAR = "#252526"
COLOR_ACCENT = "#D35400"
COLOR_MARGIN = "#2d2d30"
COLOR_ERROR_ICON = "#FF5555"
COLOR_ERROR_HOVER = "#F1C40F"
COLOR_TEXT = "#d4d4d4"
COLOR_CARD = "#2D2D30"

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class ToolTip(object):
    def __init__(self, widget): self.widget = widget; self.tipwindow = None
    def showtip(self, text):
        if self.tipwindow or not text: return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = Toplevel(self.widget); tw.wm_overrideredirect(1); tw.wm_geometry("+%d+%d" % (x, y))
        Label(tw, text=text, justify='left', background="#ffffe0", relief='solid', borderwidth=1, font=("tahoma", "10", "normal")).pack(ipadx=1)
    def hidetip(self):
        if self.tipwindow: self.tipwindow.destroy(); self.tipwindow = None

class CodeReviewApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🛡️ Johnson Electric - Code Studio V41.0 (Admin Push Only)")
        self.geometry("1450x900"); self.configure(fg_color=COLOR_BG)
        logo_path = resource_path("logo.png"); self.db_name = "users.db"
        self.current_user_role = None; self.secili_dosya = None
        self.eski_versiyon_hash = self.run_git_command(["git", "rev-parse", "HEAD"])
        self.error_data = {}; self.tooltip = None; self.init_database()
        self.grid_columnconfigure(0, weight=1); self.grid_rowconfigure(0, weight=1)
        self.login_frame = ctk.CTkFrame(self, fg_color="transparent"); self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        try:
            pil = Image.open(logo_path).convert("RGBA"); bg = Image.new("RGBA", pil.size, (255, 255, 255, 0)); bg.paste(pil, (0, 0), pil)
            self.logo_large = ctk.CTkImage(light_image=bg, dark_image=bg, size=(400, 200))
            self.logo_small = ctk.CTkImage(light_image=bg, dark_image=bg, size=(180, 90))
        except: self.logo_large = None; self.logo_small = None
        self.setup_login_screen(); self.show_login()

    def init_database(self):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, role TEXT)''')
        c.execute("SELECT * FROM users WHERE email='admin@johnson.com'")
        if not c.fetchone(): c.execute("INSERT INTO users VALUES (NULL, 'admin@johnson.com', '1234', 'admin')")
        conn.commit(); conn.close()
    
    def check_login(self, email, password):
        conn = sqlite3.connect(self.db_name); c = conn.cursor()
        c.execute("SELECT role FROM users WHERE email=? AND password=?", (email, password)); r = c.fetchone(); conn.close()
        return r[0] if r else None

    def show_login(self): self.main_frame.grid_forget(); self.login_frame.grid(row=0, column=0, sticky="nswe")
    def show_main(self, role): 
        self.current_user_role = role; 
        for w in self.main_frame.winfo_children(): w.destroy()
        self.setup_main_screen(); self.login_frame.grid_forget(); self.main_frame.grid(row=0, column=0, sticky="nswe")
        self.scan_files_action(); self.show_history_dashboard()
    def login_event(self):
        r = self.check_login(self.entry_email.get(), self.entry_pass.get())
        if r: self.show_main(r)
        else: messagebox.showerror("Hata", "Giriş başarısız!")

    def setup_main_screen(self):
        sidebar = ctk.CTkFrame(self.main_frame, width=300, corner_radius=0, fg_color=COLOR_SIDEBAR)
        sidebar.pack(side="left", fill="y")
        if self.logo_small: ctk.CTkLabel(sidebar, text="", image=self.logo_small).pack(pady=(30, 10))
        ctk.CTkButton(sidebar, text="📊 Proje Geçmişi", fg_color="#3E3E42", command=self.show_history_dashboard).pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(sidebar, text="🔄 Dosyaları Tara", fg_color="transparent", border_width=1, command=self.scan_files_action).pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(sidebar, text="KAYNAK KODLAR (C/C++)", font=("Roboto", 12, "bold"), text_color="#2ECC71").pack(pady=(20, 5), anchor="w", padx=20)
        self.source_code_frame = ctk.CTkScrollableFrame(sidebar, width=260, height=150, fg_color="#1E1E1E"); self.source_code_frame.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(sidebar, text="DİĞER DOSYALAR", font=("Roboto", 12, "bold"), text_color="gray").pack(pady=(10, 5), anchor="w", padx=20)
        self.other_files_frame = ctk.CTkScrollableFrame(sidebar, width=260, height=120, fg_color="#1E1E1E"); self.other_files_frame.pack(pady=5, padx=10, fill="x")
        
        self.btn_misra = ctk.CTkButton(sidebar, text="🛡️ MISRA KONTROL ET", fg_color="#F39C12", text_color="black", state="disabled", command=self.run_misra_check)
        self.btn_misra.pack(fill="x", padx=15, pady=(20, 5))
        ctk.CTkButton(sidebar, text="⬇️ GÜNCELLE (PULL)", fg_color=COLOR_ACCENT, command=self.git_pull_action).pack(fill="x", padx=15, pady=5)
        self.btn_diff = ctk.CTkButton(sidebar, text="🔍 DEĞİŞİMİ GÖR", state="disabled", command=self.open_diff_window); self.btn_diff.pack(fill="x", padx=15, pady=5)
        
        if self.current_user_role == 'admin': 
            ctk.CTkButton(sidebar, text="+ Personel Ekle", fg_color="#555", command=self.open_add_user_window).pack(fill="x", padx=15, pady=5)
        
        ctk.CTkButton(sidebar, text="Çıkış", fg_color="transparent", text_color="red", command=self.show_login).pack(side="bottom", pady=20)
        self.right_panel = ctk.CTkFrame(self.main_frame, fg_color="transparent"); self.right_panel.pack(side="right", fill="both", expand=True, padx=20, pady=20)

    def setup_editor_ui(self, dosya):
        for w in self.right_panel.winfo_children(): w.destroy()
        h = ctk.CTkFrame(self.right_panel, height=50, fg_color="transparent"); h.pack(fill="x", pady=5)
        ctk.CTkLabel(h, text=f"📝 {dosya}", font=("Roboto", 20, "bold"), text_color=COLOR_ACCENT).pack(side="left")
        self.lbl_status = ctk.CTkLabel(h, text="", font=("Roboto", 12), text_color="#F39C12"); self.lbl_status.pack(side="left", padx=20)
        
        # --- BUTON PANELİ ---
        btn_box = ctk.CTkFrame(h, fg_color="transparent"); btn_box.pack(side="right")
        
        # 🔥 GİTE GÖNDER BUTONU (SADECE ADMIN AKTİF)
        push_state = "normal" if self.current_user_role == 'admin' else "disabled"
        self.btn_push = ctk.CTkButton(btn_box, text="🚀 GİTE GÖNDER", width=120, fg_color="#27AE60", state=push_state, command=self.git_push_action)
        self.btn_push.pack(side="right", padx=5)
        
        ctk.CTkButton(btn_box, text="💾 KAYDET", width=100, command=self.save_file_content).pack(side="right", padx=5)
        
        cont = ctk.CTkFrame(self.right_panel, corner_radius=0, fg_color=COLOR_BG); cont.pack(fill="both", expand=True, pady=10)
        self.line_nums = Text(cont, width=4, font=("Consolas", 13), bg="#1e1e1e", fg="gray", bd=0, padx=5, pady=10, state="disabled"); self.line_nums.pack(side="left", fill="y")
        self.margin_box = Text(cont, width=3, font=("Consolas", 13), bg=COLOR_MARGIN, fg=COLOR_ERROR_ICON, bd=0, padx=2, pady=10, state="disabled"); self.margin_box.pack(side="left", fill="y")
        self.code_box = Text(cont, font=("Consolas", 13), wrap="none", bg="#1E1E1E", fg=COLOR_TEXT, insertbackground="white", undo=True, bd=0, padx=10, pady=10); self.code_box.pack(side="left", fill="both", expand=True)
        sb = ctk.CTkScrollbar(cont, command=self.sync_scroll); sb.pack(side="right", fill="y")
        self.code_box.configure(yscrollcommand=sb.set); self.margin_box.configure(yscrollcommand=sb.set); self.line_nums.configure(yscrollcommand=sb.set)
        self.code_box.bind("<MouseWheel>", self.on_scroll); self.code_box.bind("<KeyRelease>", self.update_line_numbers); self.setup_highlight()

    # --- 🔥 YENİ: GİTE GÖNDER (PUSH) MANTIĞI 🔥 ---
    def git_push_action(self):
        if self.current_user_role != 'admin':
            messagebox.showerror("Yetki Hatası", "Kodu GitHub'a sadece Admin gönderebilir!")
            return
            
        try:
            # 1. Kaydedilmemiş bir şey varsa kaydet (opsiyonel ama güvenli)
            self.save_file_content()
            
            # 2. Git Komutlarını Sırayla Çalıştır
            subprocess.run(["git", "add", "."], shell=True)
            subprocess.run(["git", "commit", "-m", f"MISRA Duzeltmesi: {self.secili_dosya}"], shell=True)
            
            # 3. Push işlemini dene
            result = subprocess.run(["git", "push", "origin", "main"], shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                messagebox.showinfo("Başarılı", "Kod başarıyla GitHub'a gönderildi! 🚀")
                self.show_history_dashboard() # Dashboard'u yenile
            else:
                messagebox.showerror("Git Hatası", f"Push yapılamadı!\n{result.stderr}")
        except Exception as e:
            messagebox.showerror("Hata", f"Beklenmedik bir hata oluştu: {str(e)}")

    # --- DİĞER FONKSİYONLAR (V40.0 İLE AYNI) ---
    def sync_scroll(self, *args): [w.yview(*args) for w in [self.code_box, self.margin_box, self.line_nums]]
    def on_scroll(self, e):
        s = int(-1*(e.delta/120))
        [w.yview_scroll(s, "units") for w in [self.code_box, self.margin_box, self.line_nums]]
        return "break"
    def update_line_numbers(self, event=None):
        lc = int(self.code_box.index('end-1c').split('.')[0])
        self.line_nums.config(state="normal"); self.line_nums.delete("1.0", "end"); self.line_nums.insert("1.0", "\n".join(str(i) for i in range(1, lc + 1))); self.line_nums.config(state="disabled")
    def run_misra_check(self):
        if not self.secili_dosya: return
        self.error_data = {}; txt = self.code_box.get("1.0", "end-1c").split("\n"); count = 0
        for i, l in enumerate(txt):
            ln = i+1; msg=None; sol=None; cl = l.split("//")[0] 
            if "goto " in cl: msg="MISRA Rule 15.1: 'goto' yasak."; sol="Spagetti koddan kaçının."
            elif re.search(r"\bint\b", cl) and "int32_t" not in cl and "main" not in cl: msg="MISRA Rule 4.6: Belirsiz 'int'."; sol="<stdint.h> kullanın (int32_t)."
            elif len(l)>120: msg="Style: Satır çok uzun."; sol="Kodu bölün."
            if msg: self.error_data[ln]={"msg":msg, "sol":sol}; count+=1
        self.update_margin(); self.lbl_status.configure(text=f"🚨 {count} Hata!" if count else "✅ Temiz.", text_color=COLOR_ERROR_ICON if count else "green")
    def update_margin(self):
        self.margin_box.config(state="normal"); self.margin_box.delete("1.0", "end"); lc = int(self.code_box.index('end-1c').split('.')[0])
        for i in range(1, lc + 1):
            if i in self.error_data:
                self.margin_box.insert("end", " ! ")
                tag=f"err_{i}"; self.margin_box.tag_add(tag, f"{i}.0", f"{i}.end")
                self.margin_box.tag_bind(tag, "<Enter>", lambda e, ln=i: self.on_hover(e, ln)); self.margin_box.tag_bind(tag, "<Button-1>", lambda e, ln=i: self.show_popup(ln)); self.margin_box.tag_config(tag, foreground=COLOR_ERROR_ICON)
            self.margin_box.insert("end", "\n")
        self.margin_box.config(state="disabled")
    def on_hover(self, e, ln):
        if not self.tooltip: self.tooltip=ToolTip(self.margin_box)
        self.tooltip.showtip(self.error_data[ln]["msg"])
    def show_popup(self, ln):
        d = self.error_data[ln]; win = ctk.CTkToplevel(self); win.geometry("400x250"); win.attributes("-topmost", True)
        ctk.CTkLabel(win, text="🚫 HATA:", text_color="#FF5555", font=("bold",14)).pack(pady=10); ctk.CTkLabel(win, text=d["msg"]).pack(); ctk.CTkLabel(win, text="✅ ÇÖZÜM:", text_color="#2ECC71", font=("bold",14)).pack(pady=10); t = ctk.CTkTextbox(win, height=80); t.pack(pady=5); t.insert("1.0", d["sol"]); t.configure(state="disabled")
    def read_file_content(self, dosya):
        self.setup_editor_ui(dosya); self.secili_dosya = dosya; self.btn_diff.configure(state="normal")
        if dosya.endswith((".c", ".h", ".cpp")): self.btn_misra.configure(state="normal", fg_color="#F39C12")
        else: self.btn_misra.configure(state="disabled", fg_color="#555")
        try:
            with open(dosya, "r", encoding="utf-8") as f: c=f.read(); self.code_box.insert("1.0", c); self.setup_highlight(); self.update_line_numbers()
        except: pass
    def save_file_content(self):
        if not self.secili_dosya: return
        with open(self.secili_dosya, "w", encoding="utf-8") as f: f.write(self.code_box.get("1.0", "end-1c"))
        self.scan_files_action(); messagebox.showinfo("Bilgi", "Kaydedildi.")
    def scan_files_action(self):
        for w in self.source_code_frame.winfo_children(): w.destroy()
        for w in self.other_files_frame.winfo_children(): w.destroy()
        try:
            dosyalar = sorted(os.listdir(os.getcwd()))
            for dosya in dosyalar:
                if dosya.endswith((".c", ".h", ".cpp", ".hpp")): ctk.CTkButton(self.source_code_frame, text=f"⚙️ {dosya}", fg_color="transparent", anchor="w", command=lambda d=dosya: self.read_file_content(d)).pack(fill="x", pady=1)
                elif dosya.endswith((".py", ".txt", ".md", ".json")): ctk.CTkButton(self.other_files_frame, text=f"📄 {dosya}", fg_color="transparent", anchor="w", command=lambda d=dosya: self.read_file_content(d)).pack(fill="x", pady=1)
        except: pass
    def setup_highlight(self):
        self.code_box.tag_config("kw", foreground="#569CD6", font=("Consolas", 13, "bold")); self.code_box.tag_config("cmt", foreground="#6A9955", font=("Consolas", 13, "italic"))
        c = self.code_box.get("1.0", "end")
        for m in re.finditer(r"#.*|//.*", c): self.code_box.tag_add("cmt", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
        for w in ["if","else","while","for","return","int","void","float","char","include","struct","main"]:
             for m in re.finditer(r"\b"+w+r"\b", c): self.code_box.tag_add("kw", f"1.0+{m.start()}c", f"1.0+{m.end()}c")
    def run_git_command(self, c): 
        try: return subprocess.check_output(c, text=True, encoding='utf-8', errors='ignore').strip()
        except: return None
    def git_pull_action(self):
        self.eski_versiyon_hash = self.run_git_command(["git", "rev-parse", "HEAD"])
        subprocess.run(["git", "fetch", "origin"], shell=True); subprocess.run(["git", "reset", "--hard", "origin/main"], shell=True)
        self.scan_files_action(); messagebox.showinfo("Bilgi", "Zorla Eşitlendi.")
    def open_diff_window(self):
        if not self.secili_dosya: return
        diff_win = ctk.CTkToplevel(self); diff_win.title(f"FARK: {self.secili_dosya}"); diff_win.geometry("1400x800"); diff_win.configure(fg_color="#1E1E1E")
        p = ctk.CTkFrame(diff_win, fg_color="transparent"); p.pack(fill="both", expand=True, padx=10, pady=10)
        l_txt = Text(p, width=60, bg="#252526", fg="#d4d4d4", font=("Consolas", 12)); l_txt.pack(side="left", fill="both", expand=True, padx=5)
        r_txt = Text(p, width=60, bg="#252526", fg="#d4d4d4", font=("Consolas", 12)); r_txt.pack(side="right", fill="both", expand=True, padx=5)
        r_txt.tag_config("new", background="#0c4a28"); l_txt.tag_config("old", background="#591313")
        try:
            o = self.eski_versiyon_hash if self.eski_versiyon_hash != self.run_git_command(["git", "rev-parse", "HEAD"]) else "HEAD^"
            l = self.run_git_command(["git", "show", f'{o}:{self.secili_dosya}']); r = self.run_git_command(["git", "show", f'HEAD:{self.secili_dosya}'])
            diff = difflib.ndiff(l.splitlines(), r.splitlines())
            for line in diff:
                if line.startswith("- "): l_txt.insert("end", line[2:]+"\n", "old")
                elif line.startswith("+ "): r_txt.insert("end", line[2:]+"\n", "new")
                elif line.startswith("  "): l_txt.insert("end", line[2:]+"\n"); r_txt.insert("end", line[2:]+"\n")
        except: pass
    def show_history_dashboard(self):
        for w in self.right_panel.winfo_children(): w.destroy()
        h = ctk.CTkFrame(self.right_panel, fg_color="transparent"); h.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(h, text="Proje Zaman Çizelgesi", font=("Roboto", 28, "bold")).pack(side="left")
        scroll = ctk.CTkScrollableFrame(self.right_panel, fg_color="transparent"); scroll.pack(fill="both", expand=True)
        try:
            logs = self.run_git_command(["git", "log", "-n", "10", "--pretty=format:%h|%an|%ad|%s", "--date=format:%Y-%m-%d %H:%M"]).splitlines()
            for line in logs:
                p = line.split("|"); card = ctk.CTkFrame(scroll, fg_color=COLOR_CARD, corner_radius=15); card.pack(fill="x", pady=8, padx=5)
                ctk.CTkFrame(card, width=6, fg_color=COLOR_ACCENT).pack(side="left", fill="y", padx=(0,10))
                ctk.CTkLabel(card, text=p[3], font=("Roboto",16,"bold")).pack(anchor="w", pady=5); ctk.CTkLabel(card, text=f"👤 {p[1]}  🕒 {p[2]}", font=("Roboto",12), text_color="gray").pack(anchor="w")
        except: pass
    def setup_login_screen(self):
        self.login_frame.grid_columnconfigure(0, weight=1); self.login_frame.grid_rowconfigure(0, weight=1)
        card = ctk.CTkFrame(self.login_frame, width=450, height=500, corner_radius=20, fg_color=COLOR_SIDEBAR)
        card.grid(row=0, column=0); card.grid_propagate(False)
        if self.logo_large: ctk.CTkLabel(card, text="", image=self.logo_large).pack(pady=30)
        self.entry_email = ctk.CTkEntry(card, placeholder_text="E-posta", width=300); self.entry_email.pack(pady=10)
        self.entry_pass = ctk.CTkEntry(card, placeholder_text="Şifre", show="*", width=300); self.entry_pass.pack(pady=10)
        ctk.CTkButton(card, text="GİRİŞ", width=300, fg_color=COLOR_ACCENT, command=self.login_event).pack(pady=20)
    def open_add_user_window(self):
        w = ctk.CTkToplevel(self); w.geometry("400x350"); w.title("Personel"); w.attributes("-topmost", True)
        self.new_email = ctk.CTkEntry(w, placeholder_text="E-posta", width=250); self.new_email.pack(pady=20)
        ctk.CTkButton(w, text="KAYDET", command=self.save_new_user).pack(pady=10)
        self.entry_pass_res = ctk.CTkEntry(w, width=250); self.entry_pass_res.pack(pady=10); self.lbl_result = ctk.CTkLabel(w, text=""); self.lbl_result.pack()
    def save_new_user(self):
        e = self.new_email.get(); p = secrets.token_hex(4)
        try:
            conn = sqlite3.connect(self.db_name); c = conn.cursor()
            c.execute("INSERT INTO users VALUES (NULL, ?, ?, 'user')", (e, p)); conn.commit(); conn.close()
            self.lbl_result.configure(text=f"Şifre: {p}", text_color="green"); self.entry_pass_res.delete(0, "end"); self.entry_pass_res.insert(0, p)
        except: self.lbl_result.configure(text="Hata!", text_color="red")

if __name__ == "__main__":
    app = CodeReviewApp()
    app.mainloop()