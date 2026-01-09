# logger.py - نظام التسجيل الشامل لكربوجي الشامية 2026
import logging
from datetime import datetime
from pathlib import Path

# ----------------------- أول حاجة: نعرّف logger -----------------------
logger = logging.getLogger("KarboujiShamia")
logger.setLevel(logging.DEBUG)
logger.propagate = False

# إعداد المجلد والملفات
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / "karbouji_full.log"
report_dir = LOG_DIR

# تنسيق غني
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)-8s | %(module)s.%(funcName)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 1. ملف كامل
fh = logging.FileHandler(log_file, encoding='utf-8')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)

# 2. ملف الأخطاء فقط
eh = logging.FileHandler(LOG_DIR / "errors_only.log", encoding='utf-8')
eh.setLevel(logging.ERROR)
eh.setFormatter(formatter)
logger.addHandler(eh)

# 3. الكونسول (Rich للجمال)
try:
    from rich.logging import RichHandler
    ch = RichHandler(rich_tracebacks=True, markup=True)
    ch.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(ch)
except:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s'))
    logger.addHandler(ch)

# دالة احتياطية لو الاستيراد فشل
if 'log_action' not in globals():
    def log_action(level, msg, source="logger", details=None):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {logging.getLevelName(level)} | {source} | {msg}" + (f" → {details}" if details else ""))

# الدالة الرئيسية (اللي بتشتغل دايمًا)
def log_action(level: int, description: str, source: str = None, details: dict | str = None):
    msg = description
    if source:
        msg = f"[{source}] {msg}"
    if details:
        if isinstance(details, dict):
            details_str = " | ".join(f"{k}: {v}" for k, v in details.items())
        else:
            details_str = str(details)
        msg += f" → {details_str}"
    logger.log(level, msg)

# دالة توليد التقرير الملخص
def generate_report():
    """تُستدعى عند إغلاق البرنامج أو يدويًا"""
    try:
        full_log = LOG_DIR / "karbouji_full.log"
        if not full_log.exists() or full_log.stat().st_size == 0:
            log_action(30, "لا يوجد سجل لتوليد تقرير", source="generate_report")
            return None

        lines = full_log.read_text(encoding='utf-8').splitlines()
        
        total = len(lines)
        
        # تصحيح دقيق للعد
        errors = sum(1 for l in lines if any(level in l for level in ["ERROR", "FATAL", "CRITICAL"]))
        warnings = sum(1 for l in lines if "WARN" in l)  # يشمل WARNING و WARN
        infos = sum(1 for l in lines if "INFO" in l or "DEBUG" in l)
        success = total - errors - warnings  # أو ممكن نحسب infos + success لو عايز

        report = f"""
╔══════════════════════════════════════════════════════════╗
║          تقرير كربوجي الشامية كريستال 2026           ║
║      {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}      ║
╚══════════════════════════════════════════════════════════╝

إجمالي السجلات: {total}
✓ ناجحة/معلومات: {success + infos}
⚠ تحذيرات: {warnings}
✗ أخطاء خطيرة: {errors}

آخر 15 حدث (للتفاصيل الأعمق):
"""
        last_15 = lines[-15:] if len(lines) >= 15 else lines
        for line in last_15:
            report += f"\n  {line}"

        report += f"\n\nالملف الكامل: {full_log.resolve()}\nكربوجي: دايمًا معك يا قلبي ♡"

        report_file = report_dir / f"تقرير_كربوجي_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_file.write_text(report, encoding='utf-8')

        log_action(20, "تم توليد تقرير ملخص بنجاح تام ♡", 
                  source="generate_report", details={"ملف": str(report_file), "أخطاء": errors})

        return str(report_file)

    except Exception as e:
        print(f"[ERROR] فشل في توليد التقرير: {e}")
        log_action(40, "فشل generate_report", details=str(e))
        return None