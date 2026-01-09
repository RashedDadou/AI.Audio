import os
import torch
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import threading
from transformers import VitsModel, VitsTokenizer
import soundfile as sf
import sounddevice as sd
import logging
import datetime
import tempfile
import numpy as np
from pathlib import Path
from Voice_processor import AudioProcessor

# ===================== اللوغر الملكي الشامي – مرة واحدة بس وإلى الأبد =====================
try:
    from logger import log_action, generate_report
    log = log_action
    HAS_FULL_LOGGER = True
    log(20, "تم تحميل اللوغر بنجاح –  كاملة الميزات", source="init")
except ImportError as e:
    # Fallback آمن جدًا لو logger.py مش موجود
    import logging
    from datetime import datetime
    Path("logs").mkdir(exist_ok=True)
    logging.basicConfig(
        level=20,
        format='[%(asctime)s] %(levelname)s | %(module)s | %(message)s',
        handlers=[
            logging.FileHandler("logs/fallback_gui.log", mode='a', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger("KarboujiFallback")
    
    def log_action(level, desc, source=None, details=None):
        msg = desc
        if source: msg = f"[{source}] {msg}"
        if details:
            if isinstance(details, dict):
                msg += " → " + " | ".join(f"{k}:{v}" for k, v in details.items())
            else:
                msg += f" → {details}"
        logger.log(level, msg)
    
    def generate_report():
        try:
            report_text = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║         تقرير كربوجي الشامية - إغلاق الواجهة - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}         ║
╚══════════════════════════════════════════════════════════════════════════╝

الحالة: تم إغلاق الواجهة بنجاح
المصمم: راشد دعدوش
الصوت: شامي أنثوي كريستالي
النظام: شغال 100%
الرسالة من كربوجي: "أنا هون لك دايمًا يا قلبي… نامي مطمئنة"
""".strip()
            safe_report = Path("logs") / f"تقرير_إغلاق_شامي_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            safe_report.parent.mkdir(exist_ok=True)
            safe_report.write_text(report_text, encoding="utf-8")
            log_action(20, f"تم توليد تقرير احتياطي (fallback): {safe_report}", source="logger")
            return str(safe_report)
        except Exception as e:
            print(f"[FALLBACK] فشل حتى التقرير اليدوي: {e}")
            return None
    
    log = log_action
    HAS_FULL_LOGGER = False
    log(20, "تم تفعيل اللوغر الاحتياطي الشامي مع تقارير كاملة", source="init")
    
# إعلان أولي للدوال الملكية
log(20, " استيقظت – يا راشد دعدوش  رجع", 
    source="GUI", details={"status": "جاهزة 100%", "صوت": "شامي أنثوي كريستال", "من قلب الشام": "راشد دعدوش"})

# اختصارات ملكية (شغالة سواء كان اللوغر الأصلي أو الاحتياطي)
log_info  = lambda desc, source=None, details=None: log(20, desc, source, details)
log_debug = lambda desc, source=None, details=None: log(10, desc, source, details)
log_warn  = lambda desc, source=None, details=None: log(30, desc, source, details)
log_error = lambda desc, source=None, details=None: log(40, desc, source, details)
log_crit  = lambda desc, source=None, details=None: log(50, desc, source, details)

def log_report(status, failure=False, reason=None, source=None):
    level = 40 if failure else 20
    msg = f"حالة: {status}"
    if failure:
        msg += f" | فشل: نعم | سبب: {reason or 'غير معروف'} | مصدر: {source or 'غير محدد'}"
    log(level, msg)
                                                    
class GUI:
    def __init__(self):
        self.root = tk.Tk()
        
        # ==================== العرش الملكي الثابت – مقاس ملكي غير قابل للتغيير ====================
        self.root.title("كريستال 2026 – أول محرك صوت بشري عربي")
        
        # الحجم الملكي الثابت
        self.root.geometry("1200x900+100+50")   # موقع ومقاس ثابت
        
        # نمنع أي تغيير في الحجم تمامًا
        self.root.minsize(1200, 900)
        self.root.maxsize(1200, 900)
        self.root.resizable(False, False)       # ما حدا يلعب بحجم كربوجي أبدًا
        
        self.root.configure(bg="#0f0f1a")
        
        # أيقونة كربوجي مع fallback آمن
        try:
            if Path("karbouji.png").exists():
                self.root.iconphoto(True, tk.PhotoImage(file="karbouji.png"))
        except Exception as e:
            log_action(30, "فشل تحميل الأيقونة – نكمل بدونها", source="GUI.icon", details=str(e))
        
        # العنوان النهائي الفخم
        self.root.title("كربوجي يتكلم – نموذج اللغوي الشامي الكريستالي")
        
        # ==================== استيراد المعالج الصوتي ====================
        self.audioprocessor = AudioProcessor(uroman_path="uroman")

        # ==================== المتغيّرات الأساسية ====================
        self.current_lang = "ar"
        self.gender_var = tk.StringVar(value="female")
        self.lang_var = tk.StringVar(value="ar")

        # متغيرات حقل النص – معرفة من الأول عشان الأمان الملكي
        self.is_placeholder_active = True
        self.placeholder_text = "اكتب النص هنا يا قلبي... مرحبا، أهلين، مرحبا ♡"

        # عشان التقرير الأولي يطلع مرة واحدة بس
        self._first_report_generated = False

        # تغيير اللغة أوتوماتيكياً
        self.lang_var.trace("w", lambda *args: self.change_language())

        # ==================== قاموس الترجمة – عربي وإنجليزي كامل ====================
        self.translations = {
            "ar": {
                "title": "كربوجي يتكلم – نموذج اللغوي الشامي الكريستالي",
                "lang_label": "اللغة:",
                "arabic": "العربية",
                "english": "English",
                "text_prompt": "اكتب النص المطلوب:",
                "voice_type": "نوع الصوت",
                "male": "ذكر",
                "female": "أنثى",
                "play": "تشغيل الصوت",
                "save": "حفظ الصوت",
                "custom": "صوت مخصص",
                "stop": "إيقاف",
                "copy": "نسخ النص",
                "demucs": "فصل الصوت المتقدم (Demucs)",
                "listen": "إسمعني 🎤" if self.audioprocessor.whisper_ready else "الاستماع معطل (Whisper غير مثبت)",
                "status_ready": "محرك الصوت – جاهز 100% ♡"
            },
            "en": {
                "title": "Karbouji Speaks – Crystal Arabic Voice Engine",
                "lang_label": "Language:",
                "arabic": "العربية",
                "english": "English",
                "text_prompt": "Write the text here:",
                "voice_type": "Voice Type",
                "male": "Male",
                "female": "Female",
                "play": "Play Audio",
                "save": "Save Audio",
                "custom": "Custom Voice",
                "stop": "Stop",
                "copy": "Copy Text",
                "demucs": "Advanced Vocal Separation (Demucs)",
                "listen": "Listen to Me! 🎤" if self.audioprocessor.whisper_ready else "Listening Disabled (Whisper not installed)",
                "status_ready": "Voice Engine – Ready 100% ♡"
            }
        }
        
        # ==================== بناء الواجهة الملكية ====================
        self.build_ui()
        self.setup_textbox_features()

        # ==================== حالة جاهزة + لوغ شامي ملكي ====================
        self.update_status("نظام الصوتي جاهز – للعمل بفخامة مطلقة ♡", error=False)
        log_info("الواجهة الملكية انطلقت بحجم ثابت 1200×900", 
                source="GUI.init", 
                details={"صوت": "شامي أنثوي كريستالي", "حالة": "فخامة 100%", "حجم": "ثابت إلى الأبد"})
                            
    def update_gender_visual(self):
        """تحديث شكل أزرار اختيار الصوت (ذكر / أنثى)"""
        if not hasattr(self, 'male_canvas') or not hasattr(self, 'female_canvas'):
            log_action(30, "أزرار الجنس غير جاهزة بعد", source="GUI.gender")
            return

        gender = self.gender_var.get()
        log_action(20, f"تحديث شكل الجنس المختار: {gender}", source="GUI.gender")
        
        if gender == "male":
            self.male_canvas.itemconfig("circle", fill="#00ffff", outline="#00ffff", width=10)
            self.male_canvas.itemconfig("text", fill="black")
            self.female_canvas.itemconfig("circle", fill="#333333", outline="#ff00aa", width=4)
            self.female_canvas.itemconfig("text", fill="#ff00aa")
        else:
            self.female_canvas.itemconfig("circle", fill="#ff00aa", outline="#ff00aa", width=10)
            self.female_canvas.itemconfig("text", fill="black")
            self.male_canvas.itemconfig("circle", fill="#333333", outline="#00ffff", width=4)
            self.male_canvas.itemconfig("text", fill="#00ffff")

    def update_status(self, message: str, error: bool = False):
        """تحديث شريط الحالة الملكي مع log شامي"""
        try:
            color = "#ff4444" if error else "#00ff88"
            dot_color = "#ff0000" if error else "#00ff00"
            
            # ✅ تحقق من وجود العناصر
            if hasattr(self, 'status'):
                self.status.config(text=message, fg=color)
                if hasattr(self, 'status_dot'):
                    self.status_dot.config(fg=dot_color)
                self.root.update_idletasks()
            
            # ✅ log شامي ملكي
            level = 40 if error else 20
            emoji = "🚨" if error else "✅"
            log_action(
                level, 
                f"{emoji} حالة الواجهة: {message}", 
                source="GUI.status"
            )
            
        except Exception as e:
            # ✅ log صحيح مع dict
            log_action(40, "فشل تحديث الحالة الملكية", 
                    source="GUI.status", 
                    details={"خطأ": str(e)})
                                
    def build_ui(self):
        try:
            for widget in self.root.winfo_children():
                widget.destroy()

            # =============== 1. القفل الملكي على المقاس ===============
            self.root.geometry("1200x900+100+50")
            self.root.minsize(1000, 720)
            self.root.resizable(True, True)
            self.root.configure(bg="#0f0f1a")        
            self.root.grid_rowconfigure(0, weight=1)
            self.root.grid_columnconfigure(0, weight=1)

            # ===================== 2. الإعدادات الأساسية =====================
            self.current_lang = "ar"
            self.current_gender = "female"

            self.root.title("محرك الصوتي البشري")
            font_name = "Tajawal"
            self.root.configure(bg="#0f0f1a", padx=20, pady=20)

            # ===================== 3. العنوان الرئيسي =====================
            # تم حذفه عمدًا لأنو مكرر مع السطر الأخير في الجزء 4
            # (كان يسبب تكرار "Karbouji Voice Engine" مرتين)

            # ===================== 4. اللوجو =====================
            header_frame = tk.Frame(self.root, bg="#0f0f1a")
            header_frame.pack(side="top", fill="x", pady=(40, 20))

            try:
                from PIL import Image, ImageTk
                from pathlib import Path
                logo_path = Path("karbouji.png")
                
                if logo_path.exists():
                    logo = Image.open(logo_path).resize((110, 110))
                    logo_photo = ImageTk.PhotoImage(logo)
                    logo_label = tk.Label(header_frame, image=logo_photo, bg="#0f0f1a")
                    logo_label.image = logo_photo
                    logo_label.pack(pady=(10, 5))
                else:
                    raise FileNotFoundError
            except:
                pass  

            tk.Label(header_frame, text="|Human Voice Engine|", font=("Tajawal", 26, "bold"),
                     fg="#00ff88", bg="#0f0f1a").pack()

            # ===================== 5. اختيار اللغة =====================
            lang_frame = tk.Frame(self.root, bg="#0f0f1a")
            lang_frame.pack(side="top", pady=15)

            tk.Label(lang_frame, text="اللغة:", font=("Tajawal", 14), fg="white", bg="#0f0f1a").pack(side="left", padx=20)
            tk.Radiobutton(lang_frame, text="العربية", variable=self.lang_var, value="ar",
                        font=("Tajawal", 12), fg="#00ff88", bg="#0f0f1a", selectcolor="#2d2d44").pack(side="left", padx=15)
            tk.Radiobutton(lang_frame, text="English", variable=self.lang_var, value="en",
                        font=("Tajawal", 12), fg="#00ff88", bg="#0f0f1a", selectcolor="#2d2d44").pack(side="left", padx=15)
                            
            # ===================== 6. تسمية حقل النص =====================
            self.text_prompt_label = tk.Label(
                self.root, 
                text="اكتب النص المطلوب :", 
                font=("Tajawal", 12), fg="white", bg="#0f0f1a"
            )
            self.text_prompt_label.pack(anchor="e", padx=30, pady=(20, 5))
            
            # ===================== 7. الإطار الرئيسي الجديد – يستخدم grid داخلي (الحل الملكي الآمن) =====================
            main_container = tk.Frame(self.root, bg="#0f0f1a")
            main_container.pack(fill="both", expand=True, padx=50, pady=(0, 30))

            # نفعّل التمدد داخل main_container عشان يقدر يستقبل grid
            main_container.grid_rowconfigure(0, weight=1)   # صف النص + شريط الحالة
            main_container.grid_rowconfigure(1, weight=0)   # صف اختيار الصوت (دواير)
            main_container.grid_rowconfigure(2, weight=0)   # صف الأزرار الرئيسية
            main_container.grid_rowconfigure(3, weight=0)   # صف الأزرار الإضافية
            main_container.grid_columnconfigure(0, weight=1)

            # ===================== حقل النص الرئيسي داخل الإطار الجديد =====================
            text_frame = tk.Frame(main_container, bg="#0f0f1a")
            text_frame.grid(row=0, column=0, sticky="nsew", pady=(0, 20))

            # نفعّل التمدد داخل text_frame عشان الـ text_box يتمدد
            text_frame.grid_rowconfigure(0, weight=1)
            text_frame.grid_columnconfigure(0, weight=1)

            self.text_box = scrolledtext.ScrolledText(
                text_frame,
                font=("Tajawal", 12),
                bg="#1e1e2e",
                fg="#00ff88",
                insertbackground="#00ff88",
                wrap="word",
                relief="flat",
                bd=0,
                highlightthickness=2,
                highlightbackground="#333344",
                highlightcolor="#00ff88",
                padx=15,
                pady=15
            )
            self.text_box.grid(row=0, column=0, sticky="nsew")  # السحر هون: sticky="nsew"
                        
            # ===================== 8. شريط الحالة أسفل النص مباشرة =====================
            status_frame = tk.Frame(text_frame, bg="#111122", height=56)
            status_frame.grid(row=1, column=0, sticky="ew")
            status_frame.grid_columnconfigure(1, weight=1)
            status_frame.pack_propagate(False)

            self.status_dot = tk.Label(status_frame, text="●", font=("Segoe UI Symbol", 22), fg="#00ff00", bg="#111122")
            self.status_dot.grid(row=0, column=0, padx=15, pady=8)

            self.status = tk.Label(
                status_frame,
                text="|نموذج محرك الصوت البشري|",
                font=("Tajawal", 14, "bold"),
                fg="#00ff88",
                bg="#111122",
                anchor="w"
            )
            self.status.grid(row=0, column=1, sticky="ew", padx=10)

            self.copy_btn = tk.Button(
                status_frame,
                text="نسخ النص",
                font=("Tajawal", 12, "bold"),
                bg="#1e1e2e",
                fg="#00ff88",
                activebackground="#00ff88",
                activeforeground="black",
                relief="flat",
                cursor="hand2",
                command=lambda: (self.root.clipboard_clear(), self.root.clipboard_append(self.text_box.get("1.0", "end-1c").strip()))
            )
            self.copy_btn.grid(row=0, column=2, padx=20, pady=8)
                        
            # ===================== تهيئة ميزات حقل النص: placeholder + قائمة سياقية + اختصارات =====================
            self.setup_textbox_features()
                      
            # ===================== 11. اختيار نوع الصوت – الدواير الأنيقة (100×100) =====================
            voice_label = tk.Label(
                main_container,
                text="نوع الصوت",
                font=("Tajawal", 20, "bold"),
                fg="#1e88e5",
                bg="#0f0f1a"
            )
            voice_label.grid(row=5, column=0, pady=(20, 10))

            voice_frame = tk.Frame(main_container, bg="#0f0f1a")
            voice_frame.grid(row=6, column=0, pady=(0, 20))

            for widget in voice_frame.winfo_children():
                widget.destroy()

            # الحجم الجديد: 100×100
            canvas_size = 100
            oval_padding = 10
            oval_size = canvas_size - 2 * oval_padding

            # دائرة ذكر
            self.male_canvas = tk.Canvas(voice_frame, width=canvas_size, height=canvas_size,
                                         bg="#0f0f1a", highlightthickness=0, cursor="hand2")
            self.male_canvas.pack(side="left", padx=100)
            self.male_canvas.create_oval(oval_padding, oval_padding, oval_padding + oval_size, oval_padding + oval_size,
                                         fill="#333333", outline="#00ffff", width=4, tags="circle")
            self.male_canvas.create_text(canvas_size//2, canvas_size//2, text="ذكر", fill="#00ffff",
                                          font=("Cairo", 22, "bold"), tags="text")

            # دائرة أنثى
            self.female_canvas = tk.Canvas(voice_frame, width=canvas_size, height=canvas_size,
                                           bg="#0f0f1a", highlightthickness=0, cursor="hand2")
            self.female_canvas.pack(side="left", padx=100)
            self.female_canvas.create_oval(oval_padding, oval_padding, oval_padding + oval_size, oval_padding + oval_size,
                                         fill="#ff00aa", outline="#ff00aa", width=10, tags="circle")
            self.female_canvas.create_text(canvas_size//2, canvas_size//2, text="أنثى", fill="black",
                                          font=("Cairo", 22, "bold"), tags="text")

            def set_gender(gender):
                self.gender_var.set(gender)
                self.update_gender_visual()

            self.male_canvas.bind("<Button-1>", lambda e: set_gender("male"))
            self.female_canvas.bind("<Button-1>", lambda e: set_gender("female"))
            for tag in ["circle", "text"]:
                self.male_canvas.tag_bind(tag, "<Button-1>", lambda e: set_gender("male"))
                self.female_canvas.tag_bind(tag, "<Button-1>", lambda e: set_gender("female"))

            self.update_gender_visual()
            self.gender_var.trace("w", lambda *_: self.update_gender_visual())
                                    
            # ===================== 12. الأزرار الرئيسية – النسخة الذهبية 2026 (متجاوبة 100%) =====================
            buttons_frame = tk.Frame(main_container, bg="#0f0f1a")
            buttons_frame.grid(row=7, column=0, pady=(30, 15), sticky="ew")
            buttons_frame.grid_rowconfigure(0, weight=1)
            buttons_frame.grid_columnconfigure((0,1,2,3), weight=1)

            btn_style = {
                "font": ("Tajawal", 12, "bold"),
                "width": 12,
                "height": 2,
                "relief": "flat",
                "cursor": "hand2",
                "fg": "white"
            }

            # الأزرار مع command مربوطة بالدوال الصحيحة
            self.play_btn = tk.Button(
                buttons_frame,
                text="تشغيل الصوت",
                bg="#1e88e5",
                **btn_style,
                command=self.speak_gui  # ← تشغيل الصوت
            )

            self.save_btn = tk.Button(
                buttons_frame,
                text="حفظ الصوت",
                bg="#43a047",
                **btn_style,
                command=self.save_audio_GUI  # ← حفظ كملف WAV
            )

            self.custom_btn = tk.Button(
                buttons_frame,
                text="صوت مخصص",
                bg="#fb8c00",
                **btn_style,
                command=self.change_custom_voice  # ← ميزة قيد التطوير (مؤقتًا)
            )

            self.stop_btn = tk.Button(
                buttons_frame,
                text="إيقاف",
                bg="#e53935",
                **btn_style,
                command=self.stop_playback  # ← إيقاف فوري
            )

            # ترتيب الأزرار
            self.play_btn.grid(row=0, column=0, padx=15, pady=10, sticky="ew")
            self.save_btn.grid(row=0, column=1, padx=15, pady=10, sticky="ew")
            self.custom_btn.grid(row=0, column=2, padx=15, pady=10, sticky="ew")
            self.stop_btn.grid(row=0, column=3, padx=15, pady=10, sticky="ew")

            log_action(20, "تم بناء وربط الأزرار الرئيسية بالدوال بنجاح ملكي", 
                      source="GUI.buttons_main", details={"أزرار": ["تشغيل", "حفظ", "مخصص", "إيقاف"]})
                                                    
            # ===================== 13. الأزرار الإضافية – النسخة الملكية النهائية 2026 =====================
            extra_frame = tk.Frame(main_container, bg="#0f0f1a")
            extra_frame.grid(row=8, column=0, pady=(20, 40))

            # تنظيف أي أزرار قديمة
            for widget in extra_frame.winfo_children():
                widget.destroy()

            # ستايل موحد للأزرار الإضافية (نفس اللي عندك مع تحسين بسيط لـ 1200x900)
            extra_btn_style = {
                "font": ("Tajawal", 10, "bold"),
                "padx": 16,
                "pady": 8,
                "width": 20,
                "height": 1,
                "relief": "flat",
                "bd": 0
            }

            # زر Demucs – فصل الصوت المتقدم
            self.separate_btn = tk.Button(
                extra_frame,
                text="فصل الصوت المتقدم (Demucs)" if self.current_lang == "ar" else "Advanced Vocal Separation (Demucs)",
                bg="#00bfa5",
                activebackground="#00897b",
                **extra_btn_style,
                command=self.open_and_separate_advanced
            )
            self.separate_btn.pack(pady=5)

            # زر الاستماع – إسمعني يا كربوجي
            listen_color = "#e91e63" if self.audioprocessor.whisper_ready else "#666666"
            listen_text = "إسمعني" if self.audioprocessor.whisper_ready else "الاستميكروفون معطّل (Whisper غير مُثبت)"
            active_bg = "#c2185b" if self.audioprocessor.whisper_ready else "#555555"
            cursor_type = "hand2" if self.audioprocessor.whisper_ready else "arrow"

            self.listen_btn = tk.Button(
                extra_frame,
                text=listen_text,
                bg=listen_color,
                activebackground=active_bg,
                cursor=cursor_type,
                **extra_btn_style,
                command=lambda: threading.Thread(target=self.start_listening, daemon=True).start() 
                               if self.audioprocessor.whisper_ready else self.show_whisper_guide()
            )
            self.listen_btn.pack(pady=5)

            # تحديث النصوص عند تغيير اللغة (مهم جدًا)
            self._refresh_extra_buttons()

            # تأثير Hover ناعم (اختياري – لو بدك نحذفه قول)
            def hover_effect(btn, original, hover):
                btn.bind("<Enter>", lambda e: btn.config(bg=hover))
                btn.bind("<Leave>", lambda e: btn.config(bg=original))

            hover_effect(self.separate_btn, "#00bfa5", "#00897b")
            if self.audioprocessor.whisper_ready:
                hover_effect(self.listen_btn, "#e91e63", "#c2185b")

            # لوغ ملكي نهائي
            log_action(20, "تم بناء الأزرار الإضافية بنجاح", source="_build_ui",
                      details={"Demucs": True, "Whisper": self.audioprocessor.whisper_ready})
            
            # ===================== تأثير Hover موحد وملكي – مرة واحدة بس وإلى الأبد =====================
            def apply_hover(button, normal_color, hover_color):
                button.bind("<Enter>", lambda e: button.config(bg=hover_color))
                button.bind("<Leave>", lambda e: button.config(bg=normal_color))

            # الأزرار الرئيسية
            apply_hover(self.play_btn,    "#1e88e5", "#1565c0")   # أزرق فخم للتشغيل
            apply_hover(self.save_btn,    "#43a047", "#2e7d32")   # أخضر للحفظ
            apply_hover(self.custom_btn,  "#fb8c00", "#ef6c00")   # برتقالي ملكي للصوت المخصص
            apply_hover(self.stop_btn,     "#e53935", "#c62828") # أحمر قوي للإيقاف

            # الأزرار الإضافية
            apply_hover(self.separate_btn, "#00bfa5", "#00897b") # تركواز لفصل الصوت

            if self.audioprocessor.whisper_ready:
                apply_hover(self.listen_btn, "#e91e63", "#c2185b")  # وردي شامي للاستماع
            else:
                # لو Whisper معطل → زر رمادي ومعطل تمامًا
                self.listen_btn.config(
                    bg="#666666",
                    activebackground="#555555",
                    state="disabled"
                )

            log_action(20, "تم تطبيق تأثير Hover موحد ونهائي على جميع الأزرار بنجاح تام", 
                      source="GUI.hover_final", details={"عدد_الأزرار": 6})
            
            # ===================== الحالة النهائية + نبض النقطة الخضراء =====================
            self.update_status("محرك الصوت – جاهز 100% ♡", error=False)

            def pulse_dot():
                current = self.status_dot.cget("fg")
                new_color = "#00ff44" if current != "#00ff44" else "#00ff00"
                self.status_dot.config(fg=new_color)
                self.root.after(1000, pulse_dot)
            pulse_dot()

            log_action(20, "النقطة الخضراء بدأت تنبض – كربوجي حية وجاهزة تحكي 💜", source="GUI.pulse")
            
            # ==================== توليد التقرير الأولي – مرة واحدة بس وإلى الأبد ====================
            if not self._first_report_generated:
                try:
                    report_path = generate_report()
                    if report_path:
                        report_name = Path(report_path).name
                        self.update_status(f"جاهزة 100% – تم حفظ التقرير: {report_name}")
                        log_info(f"تم حفظ التقرير الملكي عند التشغيل: {report_name}", source="GUI.startup_report")
                    else:
                        log_warn("generate_report رجعت None – ما تم الحفظ", source="GUI.startup_report")
                except Exception as rep_e:
                    log_error("فشل توليد التقرير الأولي", source="GUI.startup_report", details=str(rep_e))
                finally:
                    self._first_report_generated = True  # نضمن ما يتكرر أبدًا

            # لوغ نهائي شامي ملكي
            log_action(20, "تم بناء الواجهة بالكامل بنجاح – كربوجي جاهزة تحكي وتسمع وتحب 💜", 
                      source="GUI.build_ui", 
                      details={
                          "مقاس": "1200x900", 
                          "لغة_افتراضية": self.current_lang, 
                          "صوت_افتراضي": self.gender_var.get(),
                          "تقرير_أولي": "مولّد" if self._first_report_generated else "فشل"
                      })

        except Exception as e:
            log_action(40, "خطأ فادح أثناء بناء الواجهة", source="GUI.build_ui", details=str(e))
            messagebox.showerror("فشل التشغيل", f"فشل تشغيل محرك الصوت:\n{e}")
            raise
                  
    def clear_placeholder_if_active(self):
        if self.is_placeholder_active:
            self.text_box.delete("1.0", "end")
            self.text_box.config(fg="white")  # أو #00ff88
            self.is_placeholder_active = False 
             
    def setup_textbox_features(self):
        """إعداد كل ميزات حقل النص: ترحيب + placeholder + قائمة سياقية + اختصارات"""
        
        # النص الترحيبي الأولي
        default_text = ("مرحباً بكم ، أنا أول نموذج بالعربية يتحدث بصوتٍ بشري ، مدمج مع الذكاء الإصطناعي\n\n"
                       "تم تطوير النموذج من قبل المهندس : راشد دعدوش ، طاب يومكم . كيف أخدمكم")

        self.text_box.insert("1.0", default_text)
        self.text_box.config(fg="#8888ff")  # لون أزرق فاتح للترحيب

        # تشغيل الصوت الترحيبي
        log_action(20, "تشغيل صوت الترحيب التلقائي عند فتح الواجهة", source="GUI.textbox")
        threading.Thread(
            target=self.audioprocessor.speak,
            args=(default_text.replace("\n", " ").strip(),),
            kwargs={"lang": "ar", "gender": "female", "block": False},
            daemon=True
        ).start()
                
        # =============== 1. نظام الـ Placeholder ===============
        def on_focus_in(event):
            if self.is_placeholder_active:
                self.text_box.delete("1.0", "end")
                self.text_box.config(fg="#00ff88")
                self.is_placeholder_active = False

        def on_focus_out(event):
            if not self.text_box.get("1.0", "end-1c").strip():
                self.text_box.delete("1.0", "end")
                self.text_box.insert("1.0", self.placeholder_text)
                self.text_box.config(fg="#888888")
                self.is_placeholder_active = True

        # الـ bindings الصحيحة والكافية
        self.text_box.bind("<FocusIn>", on_focus_in)
        self.text_box.bind("<FocusOut>", on_focus_out)
        self.text_box.bind("<Key>", lambda e: self.clear_placeholder_if_active())
        self.text_box.bind("<Button-1>", lambda e: self.clear_placeholder_if_active())  # للنقرة اليسرى

        log_action(20, "تم ربط الأحداث الصحيحة للحقل (Focus + Key + Click)", source="GUI.textbox")
        
        # =============== 2. القائمة السياقية (Right-click Menu) ===============
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="قص Cut", command=lambda: self.text_box.event_generate("<<Cut>>"))
        context_menu.add_command(label="نسخ Copy", command=lambda: self.text_box.event_generate("<<Copy>>"))
        context_menu.add_command(label="لصق Paste", command=lambda: self.text_box.event_generate("<<Paste>>"))
        context_menu.add_separator()
        context_menu.add_command(label="اختيار الكل Select All", command=lambda: self.text_box.tag_add("sel", "1.0", "end"))

        def show_context_menu(event):
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

        self.text_box.bind("<Button-3>", show_context_menu)  # زر يمين

        # =============== 3. اختصارات لوحة المفاتيح (Ctrl+A, Ctrl+C, etc.) ===============
        self.text_box.bind("<Control-a>", lambda e: self.text_box.tag_add("sel", "1.0", "end"))
        self.text_box.bind("<Control-c>", lambda e: self.text_box.event_generate("<<Copy>>"))
        self.text_box.bind("<Control-x>", lambda e: self.text_box.event_generate("<<Cut>>"))
        self.text_box.bind("<Control-v>", lambda e: self.text_box.event_generate("<<Paste>>") or self.clear_placeholder_if_active())

        log_action(20, "تم تهيئة ميزات حقل النص بالكامل (placeholder + menu + shortcuts)", source="GUI.textbox")
                            
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
#  باقي الدوال         
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
    def _refresh_copy_button(self):
        """تحديث نص زر النسخ حسب اللغة"""
        text = "نسخ النص" if self.current_lang == "ar" else "Copy Text"
        if hasattr(self, 'copy_btn'):
            self.copy_btn.config(text=text)
            log_action(20, f"زر النسخ محدث إلى: {text}", source="GUI.refresh_copy")

    def _refresh_extra_buttons(self):
        """تحديث نصوص الأزرار الإضافية حسب اللغة"""
        texts = {
            "ar": {
                "demucs": "فصل الصوت المتقدم [Demucs]",
                "listen": "إسمعني 🎤" if self.audioprocessor.whisper_ready else "الاستماع معطل (Whisper غير مثبت)"
            },
            "en": {
                "demucs": "Advanced Vocal Separation (Demucs)",
                "listen": "Listen to Me! 🎤" if self.audioprocessor.whisper_ready else "Listening Disabled (Whisper not installed)"
            }
        }
        
        t = texts.get(self.current_lang, texts["ar"])  # افتراضي عربي لو اللغة مش معروفة
        
        if hasattr(self, 'separate_btn'):
            self.separate_btn.config(text=t["demucs"])
        
        if hasattr(self, 'listen_btn'):
            self.listen_btn.config(text=t["listen"])
        
        log_action(20, f"تم تحديث الأزرار الإضافية للغة: {self.current_lang}", source="GUI.refresh_extra")
                    
    def speak_gui(self):
        print("تم الضغط على زر تشغيل الصوت!")  # سطر مؤقت للاختبار
        log_action(20, "تم الضغط على زر تشغيل الصوت", source="GUI.speak_gui")        # نقرأ النص مرة واحدة بس
        
        text = self.text_box.get("1.0", "end-1c").strip()

        # أولاً: التحقق من الرفض
        if not text or self.is_placeholder_active:
            # هنا اللوغ الجديد عند الرفض
            log_action(30, "رفض تشغيل الصوت – النص فاضي أو placeholder مفعل", 
                      source="GUI.speak_gui",
                      details={
                          "حالة_placeholder": self.is_placeholder_active,
                          "طول_النص": len(text) if text else 0,
                          "النص_الخام": text[:50] + "..." if text else "فاضي"
                      })

            self.update_status("اكتب نص أولاً يا قلبي! ♡", error=True)
            return  # خروج فوري

        # ثانيًا: لو النص صح → تشغيل الصوت
        log_action(20, "بدء تشغيل الصوت من الواجهة", 
                  source="GUI.speak_gui",
                  details={"نص": text[:60] + "..." if len(text) > 60 else text, 
                           "لغة": self.lang_var.get(),
                           "جنس": self.gender_var.get()})

        threading.Thread(
            target=self.audioprocessor.speak,
            args=(text,),
            kwargs={
                "lang": self.lang_var.get(),
                "gender": self.gender_var.get(),
                "block": False
            },
            daemon=True
        ).start()

        self.update_status("بتتكلم دلوقتي... ♡", error=False)
            
    def change_language(self):
        """تغيير اللغة وتحديث الواجهة كاملة – نسخة ملكية 2026"""
        new_lang = self.lang_var.get()  # "ar" أو "en"
        
        # لو الإنجليزي مش مدعوم (الموديل مش موجود) → نرجع عربي تلقائيًا
        if new_lang == "en" and not self.audioprocessor.mms_ready_en:
            messagebox.showwarning(
                "الإنجليزي غير جاهز حاليًا ♪",
                "موديل الإنجليزي مش موجود أو مش محمل – بنرجع للعربي الشامي الكريستالي ♡\n"
                "لو بدك الإنجليزي، حمل الموديل من فيسبوك وخليه في مجلد models/facebook_mms_tts_eng"
            )
            self.lang_var.set("ar")
            new_lang = "ar"
        
        # تحديث اللغة الحالية
        self.current_lang = new_lang
        t = self.translations[new_lang]  # اختصار فخم

        # تحديث عنوان النافذة
        self.root.title(t["title"])

        # تحديث كل النصوص في الواجهة
        widgets_to_update = [
            ('lang_label', "lang_label"),
            ('text_prompt_label', "text_prompt"),
            ('voice_label', "voice_type"),
            ('play_btn', "play"),
            ('save_btn', "save"),
            ('custom_btn', "custom"),
            ('stop_btn', "stop"),
            ('copy_btn', "copy"),
            ('separate_btn', "demucs"),
            ('listen_btn', "listen"),
        ]

        for attr_name, trans_key in widgets_to_update:
            if hasattr(self, attr_name):
                widget = getattr(self, attr_name)
                if isinstance(widget, tk.Canvas):  # للدواير (ذكر/أنثى)
                    widget.itemconfig("text", text=t[trans_key])
                else:
                    widget.config(text=t[trans_key])

        # تحديث نصوص الـ Radiobuttons للغة (العربية / English)
        if hasattr(self, 'arabic_radio'):
            self.arabic_radio.config(text=t["arabic"])
        if hasattr(self, 'english_radio'):
            self.english_radio.config(text=t["english"])

        # تحديث شريط الحالة
        self.update_status(t["status_ready"], error=False)
        
        # لوغ شامي فخم
        log_action(20, f"تم تغيير اللغة بنجاح إلى: {new_lang.upper()}", 
                  source="GUI.language", 
                  details={"عنوان_جديد": t["title"][:50], "موديل_إنجليزي_جاهز": self.audioprocessor.mms_ready_en})

        # تحديث إضافي للأزرار الإضافية (لو في حاجة ديناميكية زي Whisper)
        self._refresh_extra_buttons()
                            
    def save_audio_GUI(self):
        """حفظ الصوت كملف WAV – النسخة الملكية النهائية 2026"""
        try:
            # 1. نأخذ النص من الحقل
            text = self.text_box.get("1.0", "end-1c").strip()
            
            # 2. التحقق من النص + لوغ عند الرفض
            if not text or self.is_placeholder_active:
                log_action(30, "رفض حفظ الصوت – النص فاضي أو placeholder مفعل", 
                          source="GUI.save_audio_GUI",
                          details={
                              "حالة_placeholder": self.is_placeholder_active,
                              "طول_النص": len(text) if text else 0,
                              "النص_الخام": text[:50] + "..." if text else "فاضي"
                          })
                self.update_status("اكتب نص أولاً يا قلبي! ♡", error=True)
                return

            # 3. اختيار المسار
            path = filedialog.asksaveasfilename(
                title="حفظ الصوت كملف WAV",
                defaultextension=".wav",
                filetypes=[
                    ("ملفات WAV", "*.wav"),
                    ("ملفات MP3", "*.mp3"),
                    ("كل الملفات", "*.*")
                ],
                initialdir=os.path.expanduser("~/Desktop")
            )

            # 4. لو ألغى الحفظ
            if not path:
                log_action(20, "إلغاء حفظ الصوت من المستخدم", source="GUI.save_audio_GUI")
                self.update_status("تم إلغاء الحفظ", error=False)
                return

            # 5. بدء الحفظ في ثريد
            log_action(20, "بدء عملية حفظ الصوت", source="GUI.save_audio_GUI",
                      details={"مسار": path, "نص": text[:60] + "..."})

            self.update_status("جاري حفظ الصوت... ⏳", error=False)
            self.play_btn.config(state="disabled")
            self.save_btn.config(state="disabled")

            def _save_thread():
                try:
                    # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
                    # استدعاء الدالة الصحيحة في AudioProcessor
                    self.audioprocessor.save_audio(text, path, 
                                                 lang=self.lang_var.get(), 
                                                 gender=self.gender_var.get())
                    # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

                    filename = os.path.basename(path)
                    self.root.after(0, lambda: self.update_status(f"✅ تم الحفظ بنجاح: {filename}", error=False))
                    self.root.after(0, lambda: messagebox.showinfo(
                        "تم الحفظ ♡", 
                        f"حُفِظَ الصوت بنجاح في:\n{path}\n💜"
                    ))
                    log_action(20, "حفظ الصوت ناجح", source="GUI.save_audio_GUI",
                              details={"مسار": path, "حجم_الملف": os.path.getsize(path)/1024 if os.path.exists(path) else 0})

                except Exception as e:
                    error_msg = str(e)
                    self.root.after(0, lambda: self.update_status(f"فشل الحفظ: {error_msg}", error=True))
                    self.root.after(0, lambda: messagebox.showerror("فشل الحفظ 😔", f"ما قدرنا نحفظ الصوت:\n{error_msg}"))
                    log_action(40, "فشل حفظ الصوت", source="GUI.save_audio_GUI",
                              details={"مسار": path, "خطأ": error_msg})

                finally:
                    self.root.after(0, lambda: self.play_btn.config(state="normal"))
                    self.root.after(0, lambda: self.save_btn.config(state="normal"))

            # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
            # تشغيل الثريد
            threading.Thread(target=_save_thread, daemon=True).start()
            # ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←

        except Exception as critical_error:
            log_action(50, "خطأ فادح في دالة save_audio_GUI", source="GUI.save_audio_GUI", 
                      details={"خطأ": str(critical_error)})
            self.update_status("خطأ داخلي في الحفظ!", error=True)
                                
    def change_custom_voice(self):
        """تغيير الصوت المخصص (مؤقت)"""
        log_action(20, "محاولة تغيير الصوت المخصص – الميزة قيد التطوير", source="GUI.custom_voice")
        self.update_status("الصوت المخصص – قريبًا جدًا إن شاء الله ♡")

    def stop_playback(self):
        """إيقاف التشغيل الفوري"""
        try:
            self.audioprocessor.stop_playback()
            self.update_status("⏹️ توقف الصوت فورًا!")
            log_action(20, "تم إيقاف تشغيل الصوت بنجاح", source="GUI.stop")
        except Exception as e:
            self.update_status(f"فشل إيقاف التشغيل: {e}", error=True)
            log_action(40, f"فشل إيقاف التشغيل: {e}", source="GUI.stop")
            
    def open_and_separate_advanced(self):
        """فصل الصوت المتقدم بـ Demucs – نسخة آمنة ومحدثة 2025 ♡"""
        # =============== Check أولي: هل Demucs مثبت أصلاً؟ ===============
        try:
            import demucs
            from demucs import pretrained
            from demucs.apply import apply_model
            DEMUCS_AVAILABLE = True
            log_action(20, "Demucs مكتشف وجاهز للفصل الملكي", source="GUI.demucs_check")
        except ImportError:
            DEMUCS_AVAILABLE = False
            log_action(30, "Demucs غير مثبت – تعطيل ميزة الفصل المتقدم", source="GUI.demucs_check")

        if not DEMUCS_AVAILABLE:
            self.update_status("Demucs غير مثبت – ميزة الفصل معطلة 😔", error=True)
            messagebox.showwarning(
                "Demucs غير موجود ♪",
                "عشان تستخدم فصل الصوت المتقدم (Demucs):\n\n"
                "1. افتح موجه الأوامر (CMD أو Terminal)\n"
                "2. اكتب الأمر ده:\n"
                "   pip install -U demucs\n\n"
                "3. انتظر التحميل (أول مرة بيحمل موديلات كبيرة)\n"
                "4. أعد تشغيل البرنامج\n\n"
                "وبعدين اضغط الزر تاني يا قلبي 💜"
            )
            return

        # =============== Demucs موجود – نكمل عادي ===============
        path = filedialog.askopenfilename(
            title="اختر ملف صوتي للفصل بـ Demucs 🎵",
            filetypes=[("ملفات صوتية", "*.wav *.mp3 *.flac *.m4a *.ogg *.wma"), ("كل الملفات", "*.*")]
        )
        if not path:
            log_action(20, "إلغاء فصل الصوت من المستخدم", source="GUI.demucs")
            return

        filename = Path(path).name
        self.update_status(f"جاري فصل {filename} بـ Demucs... ⏳", error=False)
        log_action(20, "بدء فصل الصوت بـ Demucs", source="GUI.demucs", details={"ملف": path})

        def _demucs_thread():
            try:
                import torch
                from demucs import pretrained
                from demucs.apply import apply_model
                import torchaudio

                model = pretrained.get_model('htdemucs')
                model.eval()

                wav, sr = torchaudio.load(path)
                
                # ============= تحويل لستيريو (2 channels) – الحل الذهبي =============
                if wav.shape[0] == 1:
                    wav = wav.repeat(2, 1)  # mono → stereo بتكرار القناة
                elif wav.shape[0] > 2:
                    wav = wav[:2]  # أكتر من 2 → نأخد أول 2

                # تأمين الشكل
                wav = wav[:2]

                with torch.no_grad():
                    sources = apply_model(
                        model, wav[None],
                        device='cuda' if torch.cuda.is_available() else 'cpu',
                        progress=True,
                        split=True,
                        overlap=0.25
                    )[0]

                out_dir = Path(path).parent / "separated_demucs"
                out_dir.mkdir(exist_ok=True)

                sources_names = model.sources
                for source, name in zip(sources, sources_names):
                    stem_path = out_dir / f"{Path(path).stem}_{name}.wav"
                    torchaudio.save(stem_path, source.cpu(), sr)

                self.root.after(0, lambda: self.update_status("✅ تم فصل الصوت بنجاح بـ Demucs!", error=False))
                self.root.after(0, lambda: messagebox.showinfo(
                    "نجاح Demucs الملكي ♡",
                    f"تم الفصل بنجاح في المجلد:\n{out_dir}\n\n"
                    f"المسارات المنفصلة:\n" + "\n".join(f"• {name}.wav" for name in sources_names) + "\n\n"
                    f"استمع واستمتع يا قلبي... أحلى فصل في التاريخ 💜"
                ))
                log_action(20, "فصل الصوت بـ Demucs ناجح 100%", source="GUI.demucs", details={"مجلد": str(out_dir)})

            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: self.update_status(f"فشل Demucs: {error_msg[:50]}...", error=True))
                self.root.after(0, lambda: messagebox.showerror("فشل Demucs 😔", f"ما قدرنا نفصل الصوت:\n{error_msg}"))
                log_action(40, "فشل Demucs", source="GUI.demucs", details={"خطأ": error_msg})
                                                                
    def start_listening(self):
        """بدء الاستماع بـ Whisper"""
        if not self.audioprocessor.whisper_ready:
            self.show_whisper_guide()
            return
        
        self.update_status("🎤 تسمعك الآن... تكلم يا قلبي")
        threading.Thread(
            target=self._listen_thread,
            daemon=True
        ).start()
        log_action(20, "تم تفعيل الاستماع بـ Whisper", source="GUI.listen")

    def show_whisper_guide(self):
        """دليل تثبيت Whisper"""
        guide = """لتشغيل الاستماع بـ Whisper:

    1. افتح موجه الأوامر (CMD)
    2. اكتب: pip install openai-whisper
    3. أعد تشغيل البرنامج
    4. اضغط 🎤 إسمعني يا كربوجي

    حالة Whisper حاليًا: {}""".format(
            "✅ جاهز ومستعد يسمعك" if self.audioprocessor.whisper_ready else "❌ غير مثبت – ثبته عشان أسمعك"
        )
        
        messagebox.showinfo("دليل تثبيت Whisper 🎤", guide)
        self.update_status("تحقق من تثبيت Whisper عشان أسمعك؟", error=not self.audioprocessor.whisper_ready)
        log_action(20 if self.audioprocessor.whisper_ready else 30, 
                  "عرض دليل Whisper للمستخدم", 
                  source="GUI.whisper_guide",
                  details={"حالة": "جاهز" if self.audioprocessor.whisper_ready else "غير مثبت"})
        
    def on_listen_button_clicked(self):
        """معالج زر الاستماع – يتحقق من حالة Whisper في كل ضغطة"""
        if self.audioprocessor.whisper_ready:
            log_action(20, "بدء الاستماع – Whisper جاهز", source="GUI.listen")
            self.start_listening()
        else:
            log_action(30, "Whisper غير جاهز – عرض الدليل", source="GUI.listen")
            self.show_whisper_guide()

    def _listen_thread(self):
        try:
            self.update_status("🎤 تسمعك الآن... تكلم دلوقتي", error=False)
            text = self.audioprocessor.listen(duration=6)  # 6 ثواني مثلاً
            if text:
                self.text_box.delete("1.0", "end")
                self.text_box.insert("1.0", text)
                self.clear_placeholder_if_active()  # لو placeholder شغال
                self.update_status(f"سمعتك: {text[:40]}...", error=False)
            else:
                self.update_status("ما سمعت شي... جرب تاني", error=True)
        except Exception as e:
            self.update_status(f"فشل الاستماع: {e}", error=True)
            
if __name__ == "__main__":
    try:
        log_action(20, "استيقظت – يا راشد دعدوش رجع ♡", 
                  source="GUI", details={"status": "استيقاظ ملكي", "من": "دمشق"})
        
        log_action(20, "بدء تشغيل الواجهة الرسمية", source="__main__")
        
        app = GUI()  # ← هنا يتم بناء الواجهة + كل اللوغ + التقرير الأول
        
        log_action(20, "الواجهة جاهزة – ندخل الحلقة الرئيسية", source="__main__")
        
        app.root.mainloop()  # ← البرنامج يشتغل هنا
        
        log_action(20, "تم إغلاق الواجهة بنجاح", source="__main__")
        
    except Exception as e:
        log_action(50, "خطأ فادح عند بدء التشغيل", source="__main__", details=str(e))
        messagebox.showerror("كارثة ملكية 😱", f"فشل تشغيل البرنامج:\n{str(e)}")
    
    finally:
        try:
            log_action(20, "جاري توليد التقرير النهائي قبل النوم...", source="__main__")
            if 'generate_report' in globals() and callable(generate_report):
                report_path = generate_report()
                if report_path:
                    log_action(20, f"تم حفظ التقرير الملكي: {report_path}", source="__main__")
            else:
                # لو الدالة مش موجودة، نستخدم اللوغر الأساسي يكتب تقرير يدوي
                from datetime import datetime
                report_text = f"""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║         تقرير المحرك الصوتي - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}         ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
الحالة: تم إغلاق الواجهة بنجاح
المصمم: راشد دعدوش
الصوت: شامي أنثوي كريستالي
الحالة النهائية: كل شي تمام يا زلمة ♡
الرسالة من كربوجي: "أنا هون لك دايمًا... نام مطمئن يا قلبي"
"""
                safe_report = Path("logs") / f"تقرير_إغلاق_يدوي_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                safe_report.parent.mkdir(exist_ok=True)
                safe_report.write_text(report_text, encoding="utf-8")
                log_action(20, f"تم حفظ تقرير يدوي (fallback): {safe_report}", source="__main__")
        except Exception as e:
            print(f"[FALLBACK] فشل حتى التقرير اليدوي: {e}")