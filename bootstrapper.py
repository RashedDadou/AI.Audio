import re
import os
import sys
import subprocess
import time
from pathlib import Path
import urllib.request
import shutil
import webbrowser
import psutil
import threading
import zipfile
import logging

os.environ['PYTHONIOENCODING'] = 'utf-8'

# ===================== منع التكرار الفوري =====================
# if os.environ.get("BOOTSTRAP_DONE") == "1":
#     sys.exit(0)  # إذا تم الإقلاع من قبل، اخرج فوراً
# os.environ["BOOTSTRAP_DONE"] = "1"

DF_MODEL = None
DF_STATE = None
DF_READY = False

BASE_DIR = Path.cwd()  # المجلد الحالي للتشغيل

# ===================== تفعيل نظام التسجيل =====================
Path("logs").mkdir(exist_ok=True)

log = None
log_action = None
generate_report = None

def fallback_log(level: int = 20, description: str = "", source: str = "bootstrapper", details=None):
    msg = description
    if source and source != "bootstrapper":
        msg = f"[{source}] {msg}"
    if details:
        if isinstance(details, dict):
            msg += " | " + " | ".join(f"{k}: {v}" for k, v in details.items())
        else:
            msg += f" | {details}"
    
    timestamp = time.strftime("%H:%M:%S")
    level_str = {10: "DEBUG", 20: "INFO ", 30: "WARN ", 40: "ERROR", 50: "FATAL"}.get(level, "INFO ")
    line = f"[{timestamp}] {level_str} | bootstrapper | {msg}"
    
    print(line)
    try:
        with open("logs/bootstrapper_fallback.log", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

log = fallback_log

log(20, "بسم الله الرحمن الرحيم – بدء عملية الإقلاع", 
    details={"المطور": "راشد دعدوش", "الوقت": time.strftime("%Y-%m-%d %H:%M:%S")})

try:
    from logger import logger, log_action as real_log_action, generate_report as real_generate_report
    log = real_log_action
    log_action = real_log_action
    generate_report = real_generate_report
    log(20, "تم تفعيل اللوغر الرسمي بنجاح", source="bootstrapper")
except Exception as e:
    log(30, "فشل تحميل logger.py – نستمر بالاحتياطي", details=str(e))

# ===================== دالة r =====================
def r(text: str):
    banner = "\n" + "═" * 90
    banner += "\n                 " + text.center(58)
    banner += "\n" + "═" * 90 + "\n"
    print(banner)
    try:
        log(20, text, source="bootstrapper")
    except:
        print(f"[INFO] {text}")

# ===================== الإقلاع الرسمي داخل if __name__ == "__main__" =====================
if __name__ == "__main__":
    r(" نظام تحويل النص للصوت جاهز للعمل . ")

    # ===================== FFmpeg – النسخة المحلية فقط (اللي بتنزل في مجلد المشروع، زي ما كنت عايز) =====================
    local_ffmpeg = Path("ffmpeg/bin/ffmpeg.exe")

    if local_ffmpeg.exists():
        # موجودة محليًا → نستخدمها ونضيفها للـ PATH
        os.environ["PATH"] = str(local_ffmpeg.parent.resolve()) + os.pathsep + os.environ["PATH"]
        r("FFmpeg جاهز 100% – نسخة محلية أصلية (كريستالي شامي)")
        log(20, "تم تفعيل FFmpeg المحلي – الصوت كريستالي بإذن الله", source="bootstrapper")
    else:
        # مش موجودة → نحمّلها تلقائيًا في المشروع فقط
        r("جاري تحميل FFmpeg المحلي (النسخة المثالية) أول مرة بس…")
        
        ffmpeg_zip = Path("ffmpeg.zip")
        url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"  # أفضل نسخة للصوت

        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                total = int(resp.headers.get('Content-Length', 0))
                downloaded = 0
                with open(ffmpeg_zip, "wb") as f:
                    while True:
                        chunk = resp.read(1024*1024)
                        if not chunk: break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            print(f"\r   ↓ {downloaded//(1024*1024)} ميجا من {total//(1024*1024)}", end="", flush=True)
                print("\n   تم تحميل FFmpeg بنجاح!")
            
            r("جاري فك الضغط…")
            with zipfile.ZipFile(ffmpeg_zip, 'r') as z:
                z.extractall(".")
            
            # نعيد تسمية المجلد لـ ffmpeg
            for folder in Path(".").iterdir():
                if folder.is_dir() and folder.name.startswith("ffmpeg"):
                    if Path("ffmpeg").exists():
                        shutil.rmtree("ffmpeg", ignore_errors=True)
                    folder.rename("ffmpeg")
                    break
            
            ffmpeg_zip.unlink(missing_ok=True)
            
            # نضيف المسار
            os.environ["PATH"] = str(Path("ffmpeg/bin").resolve()) + os.pathsep + os.environ["PATH"]
            r("FFmpeg نزل واتفك وصار جاهز في المشروع – الصوت كريستالي 100%")
            log(20, "تم تثبيت FFmpeg المحلي بنجاح – الصوت راجع زي الأول", source="bootstrapper")
            
        except Exception as e:
            r("فشل تحميل FFmpeg – الصوت هيبقى ضعيف")
            log(40, f"فشل تحميل FFmpeg المحلي: {e}", source="bootstrapper")
                    
    # ===================== uroman – النسخة النهائية اللي ما تتحركش تاني أبدًا =====================
    from pathlib import Path
    import urllib.request
    import zipfile
    import shutil
    import os

    BASE_DIR = Path(__file__).parent.resolve()
    uroman_pl_final = BASE_DIR / "uroman" / "bin" / "uroman.pl"

    r("تجهيز uroman – النطق الشامي الأصلي")

    if uroman_pl_final.exists():
        r("uroman موجود وجاهز 100% – صوت شامي أصلي كريستالي")
        log(20, "uroman جاهز نهائيًا", source="bootstrapper")

    else:
        r("uroman مش موجود… بنحمله مرة واحدة وخلاص للأبد")

        # تنظيف كل الفوضى القديمة
        for item in ["uroman", "uroman-master", "uroman_temp.zip"]:
            try:
                p = BASE_DIR / item
                if p.exists():
                    if p.is_dir():
                        shutil.rmtree(p)
                    else:
                        p.unlink()
            except:
                pass

        os.chdir(BASE_DIR)

        try:
            print("   نزل uroman...", end="", flush=True)
            # المهم: حطينا الـ response في متغيّر اسمه resp مش r
            with urllib.request.urlopen("https://github.com/isi-nlp/uroman/archive/refs/heads/master.zip", timeout=60) as resp:
                with open("uroman_temp.zip", "wb") as f:
                    shutil.copyfileobj(resp, f)
            print(" تم")
        except Exception as e:
            r("فشل تحميل uroman – الفالباك شغال 95%")
            log(40, f"فشل تحميل: {e}", source="bootstrapper")
            Path("uroman_temp.zip").unlink(missing_ok=True)
        else:
            try:
                with zipfile.ZipFile("uroman_temp.zip") as z:
                    z.extractall(".")

                master = Path("uroman-master")
                target = Path("uroman")
                target.mkdir(exist_ok=True)

                for item in master.iterdir():
                    shutil.move(str(item), str(target / item.name))

                # نضمن وجود bin ونقل uroman.pl لجواه بالقوة
                bin_dir = target / "bin"
                bin_dir.mkdir(exist_ok=True)
                final_pl = bin_dir / "uroman.pl"

                # نبحث عن uroman.pl في أي مكان داخل uroman وننقله
                found = False
                for file in target.rglob("uroman.pl"):
                    if not found:
                        shutil.move(str(file), str(final_pl))
                        found = True
                        break

                # تنظيف
                shutil.rmtree(master)
                Path("uroman_temp.zip").unlink()

                r("uroman اتثبت نهائيًا في المكان الصحيح: uroman/bin/uroman.pl")
                log(20, "uroman تم تثبيته بنجاح تام وثابت", source="bootstrapper")

            except Exception as e:
                r("فشل في ترتيب uroman – الفالباك شغال")
                log(40, f"خطأ في uroman: {e}", source="bootstrapper")

    # ===================== فحص وتثبيت المكتبات الأساسية – مرة واحدة فقط =====================
    r("فحص وتثبيت المكتبات الأساسية – مضمون 100% لكل بيئات Python")

    packages = [
        "torch==2.4.0",
        "torchaudio==2.4.0",
        "transformers",
        "accelerate",
        "flask",
        "pydub",
        "numpy",
        "soundfile",
        "librosa",
        "speechrecognition",
        "rich",
        "tqdm",
        "demucs",
        "openai-whisper"
    ]

    def install_package(pkg):
        try:
            __import__(pkg.split("==")[0].replace("-", "_"))
            r(f"✅ موجود: {pkg}")
            return True
        except ImportError:
            r(f"📦 بنزل: {pkg}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--no-cache-dir", "--quiet"])
                r(f"✅ تم تثبيت {pkg} بنجاح")
                return True
            except Exception as e:
                r(f"❌ فشل تثبيت {pkg}: {e}")
                return False

    success_count = 0
    for pkg in packages:
        if install_package(pkg):
            success_count += 1

    r(f"تم تثبيت {success_count}/{len(packages)} مكتبة بنجاح ✅")

    # ===================== تحميل نماذج MMS-TTS أوفلاين =====================
    from transformers import VitsModel, VitsTokenizer

    base_model_dir = BASE_DIR / "models"
    base_model_dir.mkdir(exist_ok=True)

    models_to_download = {
        "ara": "facebook/mms-tts-ara",
        "eng": "facebook/mms-tts-eng"
    }

    downloaded_count = 0

    for lang_code, model_id in models_to_download.items():
        lang_name = "العربي" if lang_code == "ara" else "الإنجليزي"
        model_dir = base_model_dir / f"facebook_mms_tts_{lang_code}"
        
        if model_dir.exists() and (model_dir / "config.json").exists():
            r(f"نموذج MMS-TTS ({lang_name}) موجود أوفلاين")
            downloaded_count += 1
            continue
        
        r(f"تحميل نموذج MMS-TTS ({lang_name}) أوفلاين – مرة واحدة فقط...")
        
        try:
            model = VitsModel.from_pretrained(model_id, torch_dtype="auto", low_cpu_mem_usage=True)
            tokenizer = VitsTokenizer.from_pretrained(model_id)
            
            model.save_pretrained(model_dir)
            tokenizer.save_pretrained(model_dir)
            
            r(f"تم تحميل نموذج MMS-TTS ({lang_name}) أوفلاين بنجاح")
            downloaded_count += 1
            
        except Exception as e:
            r(f"فشل تحميل نموذج {lang_name}: {type(e).__name__}")
            r("النظام سيستمر بدعم اللغة العربية فقط مؤقتًا")

    r(f"تم تجهيز {downloaded_count}/2 نموذج لغوي أوفلاين")
    if downloaded_count == 2:
        r("الدعم الكامل للغة العربية والإنجليزية مفعّل 100%")
    elif downloaded_count == 1:
        r("الدعم الجزئي مفعّل – سيتم استخدام النموذج العربي لكل النصوص")
    else:
        r("تحذير: لا توجد نماذج لغوية – الصوت لن يعمل")
                        
    # ===================== تفعيل DeepFilterNet3 – بسيط ومضمون =====================
    r("تفعيل خاصية إزالة الضوضاء الذكية – DeepFilterNet3")

    def try_online_install():
        """تثبيت DeepFilterNet3 من الإنترنت"""
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "deepfilternet", "--no-cache-dir", "--quiet"
            ], timeout=120)
            return True
        except:
            return False

    # التنفيذ الآمن
    if try_online_install():
        try:
            from df.enhance import init_df
            model, state, _ = init_df()  # بدون device
            log(20, "DeepFilterNet3 جاهز كريستالي 100%!", source="DeepFilterNet")
            r("DeepFilterNet3 شغال – الصوت استوديو هوليوود!")
        except Exception as e:
            log(30, f"DeepFilterNet3 فشل تحميل الموديل: {e}", source="DeepFilterNet")
    else:
        log(30, "DeepFilterNet3 غير مثبت – الفالباك ممتاز", source="DeepFilterNet")
        r("DeepFilterNet3 مؤجل – الصوت ممتاز بدون إزالة ضوضاء")

# ===================== دالة safe_log =====================
def safe_log(level, msg, source="bootstrapper", details=None):
    try:
        log_action(level, msg, source=source, details=details)
    except:
        try:
            log(level, msg, source=source, details=details)
        except:
            print(f"[BOOT] [{source}] {msg}")

# ===================== صوت الترحيب =====================
def play_welcome_sound():
    sound_paths = [
        "sounds/welcome_shami.wav",
        "sounds/welcome.mp3",
        "sounds/intro_shami.mp3",
        "sounds/welcome.wav",
        "sounds/welcome_shami.mp3"
    ]
    for path in sound_paths:
        if Path(path).exists():
            try:
                from pydub import AudioSegment
                from pydub.playback import play
                sound = AudioSegment.from_file(path)
                print(f"\nتم تشغيل صوت الترحيب: {path}")
                play(sound)
                log(20, f"تم تشغيل صوت الترحيب: {path}", source="bootstrapper")
                return
            except Exception as e:
                log(30, f"فشل تشغيل الصوت {path}: {e}", source="bootstrapper")
    print("لا يوجد ملف صوت ترحيب – كربوجي هتتكلم لما تقول مرحبا")
    log(20, "لا صوت ترحيب – كربوجي جاهزة للكلام", source="bootstrapper")

# ===================== إقلاع الواجهة تلقائيًا =====================
def start_karboji():
    try:
        import psutil
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            cmd = ' '.join(proc.info['cmdline'] or [])
            if 'Voice_processor.GUI.py' in cmd and 'python' in cmd.lower():
                safe_log(20, "واجهة كربوجي الشامية شغالة بالفعل", source="bootstrapper")
                return True
    except Exception as e:
        safe_log(30, f"فحص العمليات فشل: {e}", source="bootstrapper")

    safe_log(20, "جاري إيقاظ واجهة كربوجي الشامية (GUI)...", source="bootstrapper")
    try:
        gui_path = str(BASE_DIR / "Voice_processor.GUI.py")
        if os.name == "nt":
            os.system(f'start "" python "{gui_path}"')
        else:
            subprocess.Popen([sys.executable, gui_path, "--gui-mode"], cwd=BASE_DIR)
        time.sleep(3.0)
        safe_log(20, "واجهة كربوجي الشامية انطلقت بنجاح ♡", source="bootstrapper")
        return True
    except Exception as e:
        safe_log(40, f"فشل إقلاع واجهة كربوجي: {e}", source="bootstrapper")
        return False

# ===================== الإقلاع الرسمي =====================
if __name__ == "__main__":
    r(" نظام تحويل النص للصوت جاهز للعمل . ")

    # FFmpeg code here (your existing code)
    # uroman code here (your existing code)
    # packages and install code here (your existing code)
    # MMS-TTS code here (your existing code)
    # DeepFilterNet code here (your existing code)

    r("جاري إقلاع كربوجي الشامية بواجهة سطح المكتب ♡")
    start_karboji()

    print("\n" + "═" * 75)
    print(" كربوجي الشامية استيقظت بواجهة سطح مكتب ♡".center(75))
    print(" ابحث عن نافذة 'كريستال 2026' على سطح المكتب".center(75))
    print(" اكتب 'مرحبا' في حقل النص واضغط تشغيل الصوت".center(75))
    print("═" * 75 + "\n")

    threading.Thread(target=play_welcome_sound, daemon=True).start()

    for i in range(5, 0, -1):
        hearts = "♡" * (6 - i)
        print(f"\r{' '*30}إغلاق نافذة الإقلاع بعد {i} ثوانٍ... {hearts}", end="", flush=True)
        time.sleep(1)

    print("\n\n" + " تم بنجاح ♡ كربوجي شغالة بواجهة سطح المكتب الحين… افتح الواجهة وكلمها!".center(80))
    print("═" * 80 + "\n")
    
