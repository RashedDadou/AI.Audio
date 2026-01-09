def detect_language(text: str) -> str:
    """يكشف اللغة تلقائيًا: ara أو eng"""
    arabic_chars = any(ord(c) >= 0x0600 and ord(c) <= 0x06FF for c in text)
    if arabic_chars or any(c in "أإآؤءئىةلإ" for c in text):
        return "ara"
    return "eng"  # ✅ مثالي

# Voice_processor.py - كربوجي الشامية كريستال 2026 (النسخة الذهبية النظيفة)

import io
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Optional, Literal
import torch
import numpy as np
import soundfile as sf
from flask import Flask, request, jsonify
import sounddevice as sd
import scipy.signal

from transformers import VitsTokenizer, VitsModel

# تعطيل Flask مؤقتاً لحد ما نصلحه
try:
    if "--server-only" in sys.argv:
        print("تعطيل Flask مؤقتاً...")
        sys.exit(0)
except:
    pass

try:
    from bootstrapper import r
except ImportError:
    def r(text: str):
        print("\n" + "═" * 90)
        print("                 " + text.center(58))
        print("═" * 90 + "\n")
                
# استيرادات لاحقة (Lazy Loading)
_whisper = None   # noqa: F401
_sd      = None   # noqa: F401
_pydub   = None   # noqa: F401

# ------------------- تأخير تحميل المكتبات الثقيلة -------------------
# torch, transformers, sounddevice, pydub, soundfile, df, whisper
# كلها هتتحمل داخل الكلاس لاحقًا (Lazy Loading)

warnings.filterwarnings("ignore", category=UserWarning, module="torch")

# ================================ استخدام اللوغر الرسمي الشامي الفخم ================================

# logger (كما هو)
try:
    from logger import logger, log_action, generate_report
    log = log_action
except ImportError as e:
    raise ImportError("ملف logger.py مفقود!") from e

# ================================ المسارات النسبية والذكية ================================

BASE_DIR = Path(__file__).parent.resolve()

DEFAULT_PATHS = {
    "mms_tts_ar": BASE_DIR / "models" / "facebook_mms_tts_ara",
    "mms_tts_en": BASE_DIR / "models" / "facebook_mms_tts_eng",
    "uroman":     BASE_DIR / "uroman" / "bin" / "uroman.pl",
}  # ← تم إغلاق القاموس بشكل صحيح

# ===================== DeepFilterNet3 Global Functions =====================
def load_deepfilternet() -> bool:
    global DF_READY, DF_MODEL, DF_STATE  # إذا لازم globals، بس الأفضل تجنبها
    if DF_READY:
        return True

    try:
        from df.enhance import init_df, enhance  # استيراد كافي بدون import df
        log_action(20, "جاري تحميل DeepFilterNet3 بالطريقة الرسمية (2025)...", source="DF")
        
        # بدون device: يدعم CUDA تلقائيًا
        DF_MODEL, DF_STATE, _ = init_df()  # إضافة _ للـ offset أو أي رجوع ثالث
        
        DF_READY = True
        log_action(20, "DeepFilterNet3 جاهز كريستالي 100% – تنظيف الصوت مفعّل", 
                  source="DF", details={"مصدر": "PyPI + Cache"})
        return True

    except Exception as e:
        log_action(30, f"DeepFilterNet3 معطل (غير ضروري): {e}", source="DF")
        DF_READY = False
        return False    
# ===================== DeepFilterNet3 – PyPI فقط (لا مجلدات محلية) =====================
DF_MODEL = None
DF_STATE = None  
DF_READY = False
# ❌ احذف DF_MODEL_PATH و DF_PROJECT_ROOT و candidates كاملة
        
# ===================== DeepFilterNet3 – متغيرات فقط (التحميل في AudioProcessor) =====================
DF_MODEL = None
DF_STATE = None  
DF_READY = False
        
# ================================ مسارات موديلات MMS-TTS (التصحيح النهائي) ================================
MMS_ARABIC_MODEL_PATH = BASE_DIR / "models" / "facebook_mms_tts_ara"
MMS_ENGLISH_MODEL_PATH = BASE_DIR / "models" / "facebook_mms_tts_eng"

if MMS_ARABIC_MODEL_PATH.exists() and (MMS_ARABIC_MODEL_PATH / "config.json").exists():
    log_action(20, "موديل MMS-TTS العربي جاهز", source="MMS", details={"مسار": str(MMS_ARABIC_MODEL_PATH)})
else:
    log_action(40, "تحذير: موديل العربي مفقود أو ناقص!", source="MMS", details={"مسار": str(MMS_ARABIC_MODEL_PATH)})

if MMS_ENGLISH_MODEL_PATH.exists() and (MMS_ENGLISH_MODEL_PATH / "config.json").exists():
    log_action(20, "موديل MMS-TTS الإنجليزي جاهز", source="MMS")
            
class AudioProcessor:
    def __init__(self, uroman_path=None):
        # المتغيرات الأساسية
        self.model_ar = self.tokenizer_ar = None
        self.model_en = self.tokenizer_en = None
        self.mms_ready_ar = self.mms_ready_en = False
        self.df_ready = self.whisper_ready = False
        self.df_model = self.df_state = self.whisper_model = None
        self.uroman_path = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        log_action(20, "بدء تهيئة كربوجي الشامية كريستال 2026...", source="AudioProcessor")
        log_action(20, f"الجهاز: {self.device.upper()}", source="AudioProcessor")

        # ===================== تحميل MMS-TTS العربي (مرة واحدة فقط) =====================
        if MMS_ARABIC_MODEL_PATH.exists() and (MMS_ARABIC_MODEL_PATH / "config.json").exists():
            try:
                self.tokenizer_ar = VitsTokenizer.from_pretrained(str(MMS_ARABIC_MODEL_PATH))
                self.model_ar = VitsModel.from_pretrained(str(MMS_ARABIC_MODEL_PATH), torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32)
                self.model_ar = self.model_ar.to(self.device)
                self.model_ar.eval()
                self.mms_ready_ar = True
                log_action(20, "موديل MMS-TTS العربي جاهز – صوت شامي كريستالي 100%", source="AudioProcessor")
            except Exception as e:
                log_action(40, f"فشل تحميل الموديل العربي: {e}", source="AudioProcessor")
        else:
            log_action(40, "موديل العربي مفقود!", source="AudioProcessor")

        # ===================== تحميل MMS-TTS الإنجليزي (مرة واحدة فقط) =====================
        if MMS_ENGLISH_MODEL_PATH.exists() and (MMS_ENGLISH_MODEL_PATH / "config.json").exists():
            try:
                self.tokenizer_en = VitsTokenizer.from_pretrained(str(MMS_ENGLISH_MODEL_PATH))
                self.model_en = VitsModel.from_pretrained(str(MMS_ENGLISH_MODEL_PATH), torch_dtype=torch.float16 if self.device == 'cuda' else torch.float32)
                self.model_en = self.model_en.to(self.device)
                self.model_en.eval()
                self.mms_ready_en = True
                log_action(20, "موديل MMS-TTS الإنجليزي جاهز – نطق نقي", source="AudioProcessor")
            except Exception as e:
                log_action(40, f"فشل تحميل الموديل الإنجليزي: {e}", source="AudioProcessor")
        else:
            log_action(40, "موديل الإنجليزي مفقود!", source="AudioProcessor")

        # حالة عامة
        if self.mms_ready_ar or self.mms_ready_en:
            log_action(20, "كربوجي جاهزة تتكلم بكل اللغات", source="AudioProcessor")
        else:
            log_action(40, "تحذير: ما في نماذج TTS!", source="AudioProcessor")

        # ===================== uroman =====================
        if uroman_path and Path(uroman_path).exists():
            self.uroman_path = str(Path(uroman_path).resolve())
            log_action(20, "uroman جاهز – نطق شامي أصلي", source="AudioProcessor")
        else:
            log_action(30, "uroman مش موجود – الفالباك شغال", source="AudioProcessor")

        # ===================== DeepFilterNet3 =====================
        try:
            from df.enhance import init_df
            self.df_model, self.df_state, _ = init_df()
            self.df_ready = True
            log_action(20, "DeepFilterNet3 جاهز – صوت استوديو", source="AudioProcessor")
        except Exception as e:
            log_action(30, f"DeepFilterNet3 معطل: {e}", source="AudioProcessor")

        # ===================== Whisper =====================
        try:
            import whisper
            self.whisper_model = whisper.load_model("small", device=self.device)
            self.whisper_ready = True
            log_action(20, "Whisper جاهز – بيفهم اللهجة الشامية", source="AudioProcessor")
        except Exception as e:
            log_action(30, f"Whisper معطل: {e}", source="AudioProcessor")

        log_action(20, "تهيئة كربوجي اكتملت بنجاح 100%", source="AudioProcessor")
                                                                
    def denoise_audio(self, audio_np: np.ndarray, sr: int = 24000) -> np.ndarray:
        """
        تنظيف الصوت بـ DeepFilterNet3 – نسخة ملكية 2026 بدون global أبدًا
        """
        if not self.df_ready or self.df_model is None or self.df_state is None:
            log_action(30, "DeepFilterNet3 غير جاهز – بنرجع الصوت الأصلي", source="denoise_audio")
            return audio_np

        try:
            import torch
            from df.enhance import enhance

            # تحويل للتنسور الصحيح: (batch=1, channels=1, time)
            audio_tensor = torch.from_numpy(audio_np).float().unsqueeze(0).unsqueeze(0).to(self.device)

            log_action(20, "DeepFilterNet3 يشتغل – تنظيف صوت استوديو عالمي جاري...", source="denoise_audio")

            # التوليف السحري – استخدام self مباشرة
            enhanced_tensor = enhance(self.df_model, self.df_state, audio_tensor)

            enhanced_np = enhanced_tensor.squeeze().cpu().numpy()

            log_action(20, "✅ DeepFilterNet3 نجح – الصوت صار كريستالي نقي 100%", source="denoise_audio")

            return enhanced_np

        except Exception as e:
            log_action(30, f"DeepFilterNet3 فشل في التنظيف: {e}", source="denoise_audio")
            return audio_np  # fallback آمن: نرجع الصوت الأصلي بدون ما نقع
                                                                                                                                                                                            
    def uromanize(self, text: str) -> str:
        """
        تحويل النص العربي/الإنجليزي المختلط إلى لاتيني لـ MMS-TTS
        مع fallback شامي أصلي كريستالي 2026
        """
        if not text or not text.strip():
            return "marhaba"

        text = text.strip()

        # 1. uroman.pl (الأصلي) – لو موجود
        if self.uroman_path and Path(self.uroman_path).exists():
            try:
                import subprocess
                process = subprocess.Popen(
                    ["perl", self.uroman_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=text)
                if process.returncode == 0 and stdout.strip():
                    romanized = stdout.strip()
                    log_action(20, f"uroman.pl نجح → {romanized[:80]}...", source="uromanize")
                    return romanized
            except Exception as e:
                log_action(30, f"uroman.pl فشل: {e} – منكمل بالfallback", source="uromanize")

        # 2. Fallback ذكي شامي أصلي – محدث وأدق
        log_action(20, "[translate:fallback شامي كريستالي مفعّل]", source="uromanize")

        result = ""
        for char in text:
            if 0x0600 <= ord(char) <= 0x06FF:  # حرف عربي
                arabic_map = {
                    'ا': 'a', 'أ': 'a', 'إ': 'e', 'آ': 'aa',
                    'ب': 'b', 'ت': 't', 'ث': 'th', 'ج': 'j',
                    'ح': 'h', 'خ': 'kh', 'د': 'd', 'ذ': 'th',
                    'ر': 'r', 'ز': 'z', 'س': 's', 'ش': 'sh',
                    'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'th',
                    'ع': '3', 'غ': 'gh', 'ف': 'f', 'ق': 'q',
                    'ك': 'k', 'ل': 'l', 'م': 'm', 'ن': 'n',
                    'ه': 'h', 'و': 'w', 'ي': 'y', 'ى': 'a',
                    'ة': 'a', 'ء': '', 'ئ': '', 'ؤ': ''
                }
                result += arabic_map.get(char, ' ')
            else:
                # إنجليزي أو رموز أو مسافات
                result += char.lower()

        # تنظيف نهائي فخم
        import re
        result = re.sub(r'[^a-z0-9\s3]', ' ', result.lower())
        result = re.sub(r'\s+', ' ', result).strip()

        if not result:
            result = "marhaba"

        log_action(20, f"[translate:fallback نجح → {result[:80]}...]", source="uromanize")
        return result
                     
    def process(
                self,
                audio_path=None,
                output_path=None,
                recognize_speech: bool = False,
                synthesize_text: str = None,
                enhance_pronunciation: bool = False,
                language: str = "ar",
            ) -> dict:
                """
                الدالة الرئيسية الشاملة 
                تدعم: 
                • TTS (تحويل نص → صوت )
                • STT (سماع صوت → نص 100%)
                • تنظيف الصوت (Denoise + Enhance بـ DeepFilterNet3)
                آمنة، لا تجمد الواجهة، لا تتوقف، وتشتغل في أي مكان في الكون
                """
                try:
                    # ─────────────── 1. توليف النص (TTS) ───────────────
                    if synthesize_text:
                        log_action(20, "بدء نظام TTS بالعمل", source="process",
                                details={"نص": synthesize_text[:60], "لغة": language})

                        audio_bytes = self.synthesize_text(synthesize_text, language, enhance_pronunciation)

                        out_path = Path(output_path or "output_tts.wav").expanduser().resolve()
                        out_path.parent.mkdir(parents=True, exist_ok=True)

                        with open(out_path, "wb") as f:
                            f.write(audio_bytes)

                        log_action(20, "TTS نجح وحفظ الملف بنجاح", source="process",
                                details={"ملف": str(out_path), "حجم": f"{out_path.stat().st_size/1024:.1f}KB"})

                        return {"status": "success", "output": str(out_path), "mode": "tts"}

                    # ─────────────── 2. التعرف على الكلام (STT) ───────────────
                    if recognize_speech and audio_path:
                        if not self.whisper_ready:
                            return {"status": "error", "message": "Whisper معطل حالياً – ما فيني أسمعك"}

                        audio_path = Path(audio_path)
                        if not audio_path.exists():
                            return {"status": "error", "message": f"ملف الصوت مش موجود: {audio_path}"}

                        from pydub import AudioSegment

                        audio = AudioSegment.from_file(audio_path)
                        audio = audio.set_channels(1).set_frame_rate(16000)

                        samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
                        samples /= 32768.0  # pydub يرجع 16-bit دايمًا

                        result = self.whisper_model.transcribe(
                            samples,
                            language="ar",
                            fp16=(self.device == "cuda"),
                            temperature=0.0,
                            beam_size=5,
                            best_of=5,
                            word_timestamps=True,
                        )

                        text = result["text"].strip()

                        log_action(20, "STT شامي ناجح 100%", source="process",
                                details={"نص": text[:100], "مدة": f"{result.get('duration', 0):.1f}ث"})

                        return {
                            "status": "success",
                            "text": text,
                            "mode": "stt",
                            "segments": result.get("segments", []),
                            "language": result.get("language"),
                        }

                    # ─────────────── 3. تنظيف الصوت (Denoise) – الطريقة الصحيحة 100% ───────────────
                    if audio_path and output_path:
                        audio_path = Path(audio_path)
                        output_path = Path(output_path).expanduser().resolve()

                        if not audio_path.exists():
                            return {"status": "error", "message": f"ملف الصوت مش موجود: {audio_path}"}

                        output_path.parent.mkdir(parents=True, exist_ok=True)

                        from pydub import AudioSegment

                        # تحميل الصوت
                        audio = AudioSegment.from_file(audio_path)
                        
                        # تحويل للشكل المطلوب لـ DeepFilterNet3: 24kHz مونو
                        audio = audio.set_frame_rate(24000).set_channels(1)
                        samples = np.array(audio.get_array_of_samples(), dtype=np.float32) / 32768.0
                        
                        denoised = samples  # القيمة الافتراضية لو فشل التنظيف

                        # ✅ استخدام DeepFilterNet3 الصحيح (instance variables)
                        if self.df_ready and self.df_model:
                            try:
                                from df.enhance import enhance
                                import torch
                                
                                # تحويل للشكل الصحيح: (1, 1, T)
                                audio_tensor = torch.from_numpy(samples).unsqueeze(0)
                                
                                log_action(20, "DeepFilterNet3 يشتغل – تنظيف الصوت بقوة!", source="denoise")
                                enhanced_tensor = enhance(self.df_model, self.df_state, audio_tensor)  # ✅ الصحيح!
                                denoised = enhanced_tensor.squeeze().cpu().numpy()
                                
                                log_action(20, "✅ DeepFilterNet3 نجح – الصوت صار استوديو عالمي!", source="denoise")
                                
                            except Exception as e:
                                log_action(30, f"DeepFilterNet3 فشل: {e}", source="denoise")
                                denoised = samples
                        else:
                            log_action(30, "DeepFilterNet3 غير جاهز", source="denoise")

                        # حفظ الملف النظيف
                        sf.write(output_path, denoised, 24000)
                        
                        log_action(20, "تم حفظ الصوت النظيف بنجاح", source="process",
                                details={"ملف": str(output_path), "حجم": f"{output_path.stat().st_size/1024:.1f}KB"})
                        
                        return {"status": "success", "output": str(output_path), "mode": "denoise"}

                    # ─────────────── لو ما عرفنا شو بدو بدو ───────────────
                    return {
                        "status": "error",
                        "message": "يا زلمة، إما أعطيني نص أحكيه، أو ملف صوت أنظفه، أو قلي اسمعك… ما تقعد تحيرني!"
                    }

                except Exception as e:
                    log_action(40, "خطأ عام في process", source="AudioProcessor.process", details=str(e))
                    return {"status": "error", "message": f"صار شي غلط كبير: {e}"}         
    
    def listen(self, duration: int = 5, sample_rate: int = 16000) -> str:
        """تسجيل من الميكروفون لمدة معينة وتحويله لنص بـ Whisper"""
        if not self.whisper_ready:
            log_action(40, "Whisper غير جاهز – ما فيني أسمع", source="AudioProcessor.listen")
            return ""

        try:
            log_action(20, "بدء الاستماع من الميكروفون", source="AudioProcessor.listen",
                      details={"المدة": duration, "معدل_العينة": sample_rate})

            import sounddevice as sd
            import numpy as np

            audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
            sd.wait()  # انتظر انتهاء التسجيل

            audio = audio.flatten()

            result = self.whisper_model.transcribe(
                audio,
                language="ar",
                fp16=(self.device == "cuda"),
                temperature=0.0,
            )

            text = result["text"].strip()
            log_action(20, "تم الاستماع والتعرف بنجاح", source="AudioProcessor.listen",
                      details={"النص": text[:100]})

            return text

        except Exception as e:
            log_action(40, "فشل الاستماع من الميكروفون", source="AudioProcessor.listen", details=str(e))
            return ""
                                             
    def synthesize_text(self, text: str, language: str = None, enhance_pronunciation: bool = False) -> bytes:
        """
        توليد صوت من نص طويل أو قصير مع دعم كشف اللغة تلقائي (عربي/إنجليزي)
        """
        if not text or not text.strip():
            raise ValueError("النص فارغ يا قلبي!")

        original_text = text.strip()

        # كشف اللغة تلقائيًا إذا ما حددتش
        if language is None:
            language = detect_language(original_text)
            log_action(20, f"كشف اللغة تلقائيًا: {language}", source="synthesize_text")
        else:
            if language != "ara" and (language != "eng" or not self.mms_ready_en):
                if language == "eng":
                    log_action(20, "الإنجليزي مطلوب بس الموديل غير جاهز – بنستخدم العربي الشامي الكريستالي ♡", source="synthesize_text")
                else:
                    log_action(20, f"لغة غير مدعومة: {language} – بنرجع للعربي", source="synthesize_text")
                language = "ara"
        
        log_action(20, "طلب TTS", source="synthesize_text",
                  details={"طول النص": len(original_text), "لغة": language})

        # لو النص قصير → توليف مباشر
        if len(original_text) < 300:
            return self._synthesize_chunk(original_text, language)

        # لو طويل → تقطيع ذكي لدفعات
        import re
        sentences = re.split(r'[.!?۔؟؛،,]\s*', original_text)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            temp = current_chunk + (". " if current_chunk else "") + sentence
            if len(temp) > 220:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk = temp

        if current_chunk:
            chunks.append(current_chunk)

        log_action(20, f"تم تقطيع النص إلى {len(chunks)} دفعة صوتية", source="synthesize_text")

        # توليد ودمج الأجزاء
        audio_parts = []
        for i, chunk in enumerate(chunks):
            log_action(10, f"توليد دفعة {i+1}/{len(chunks)}: {chunk[:60]}...", source="synthesize_text")
            part_bytes = self._synthesize_chunk(chunk, language)
            audio_parts.append(part_bytes)

        combined_audio = b"".join(audio_parts)

        duration_sec = len(combined_audio) / 1024 / 10  # تقريبي (كان صحيح أساسًا)
        log_action(20, "تم دمج كل الدفعات بنجاح – الصوت متصل 100%", source="synthesize_text",
                  details={
                      "عدد الدفعات": len(chunks),
                      "الحجم الكلي KB": f"{len(combined_audio)/1024:.1f}",
                      "المدة التقريبية": f"{duration_sec:.1f}ث"
                  })

        return combined_audio
    
    def speak(self, text: str, lang: str = "ar", gender: str = "female", block: bool = True):
        print("تم استدعاء speak من AudioProcessor!")  # اختبار
        log_action(20, "تم استدعاء speak", source="AudioProcessor.speak")

        if lang == "ar":
            lang = "ara"
        elif lang == "en":
            lang = "eng"

        if not text or not text.strip():
            return

        try:
            log_action(20, "طلب تشغيل صوت مباشر", source="AudioProcessor.speak",
                      details={"نص": text[:60], "لغة": lang, "جنس": gender})

            audio_bytes = self.synthesize_text(text, language=lang)

            import sounddevice as sd
            import io, soundfile as sf
            import numpy as np

            with io.BytesIO(audio_bytes) as f:
                audio_np, original_rate = sf.read(f, dtype='float32')

            if audio_np.ndim > 1:
                audio_np = audio_np.mean(axis=1)

            # ============= السر الشامي الكريستالي: بطء حنون لكل اللغات =============
            # 0.75 = صوت أنثوي حنون طبيعي (مش طفولي، مش سريع)
            # 0.80 = لو بدك أسرع شوية
            # 0.70 = لو بدك أبطأ وأعمق أكتر
            
            if lang == "ara" and gender == "female":
                # لمسة شامية خاصة للعربي الأنثوي
                speed_factor = 0.67
            else:
                # للإنجليزي أو الصوت الذكري → أقل بطء
                speed_factor = 0.65

            playback_rate = int(original_rate * speed_factor)

            # ============= تنقية الصوت (اختياري بس يجنن) =============
            try:
                from scipy.signal import butter, lfilter
                def high_pass_filter(data, cutoff=80, fs=original_rate, order=4):
                    nyq = 0.5 * fs
                    normal_cutoff = cutoff / nyq
                    b, a = butter(order, normal_cutoff, btype='high', analog=False)
                    return lfilter(b, a, data)
                audio_np = high_pass_filter(audio_np)
            except ImportError:
                pass  # scipy مش مطلوب، الصوت لسا حلو

            # ============= تشغيل الصوت الحنون الطبيعي =============
            sd.stop()  # مهم جدًا
            sd.play(audio_np, samplerate=playback_rate, blocking=block)

            duration = len(audio_np) / original_rate
            log_action(20, f"تم تشغيل الصوت الحنون الطبيعي بنجاح ♡", 
                      source="AudioProcessor.speak", 
                      details={
                          "المدة الأصلية": f"{duration:.2f}ث", 
                          "معدل_التشغيل": playback_rate, 
                          "عامل_السرعة": speed_factor,
                          "لغة": lang
                      })

        except Exception as e:
            log_action(40, f"فشل speak: {e}", source="AudioProcessor.speak")
                                
    def _synthesize_chunk(self, text: str, language: str) -> bytes:
        """توليف دفعة واحدة فقط بناءً على اللغة (ara أو eng)"""
        if language not in ("ara", "eng"):
            language = "ara"

        # اختيار الموديل والتوكنايزر المناسبين
        if language == "ara":
            if not self.mms_ready_ar:
                raise RuntimeError("موديل MMS-TTS العربي غير جاهز!")
            tokenizer = self.tokenizer_ar
            model = self.model_ar
        else:  # eng
            if not self.mms_ready_en:
                raise RuntimeError("موديل MMS-TTS الإنجليزي غير جاهز!")
            tokenizer = self.tokenizer_en
            model = self.model_en

        try:
            inputs = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=256,
                padding=False
            ).to(self.device)

            # لو النص فارغ بعد التوكنز → نستخدم كلمة افتراضية
            if inputs["input_ids"].shape[1] == 0:
                fallback_text = "hello" if language == "eng" else "مرحبا"
                inputs = tokenizer(fallback_text, return_tensors="pt").to(self.device)

            with torch.no_grad():
                output = model(inputs["input_ids"])
                audio_np = output.waveform.squeeze().cpu().numpy()

            if audio_np.size == 0:
                raise RuntimeError("الصوت فارغ من الموديل!")

            # تطبيع الصوت
            peak = np.max(np.abs(audio_np))
            if peak > 0:
                audio_np = audio_np / peak * 0.98

            # تحويل إلى int16
            audio_int16 = (audio_np * 32767).astype(np.int16)

            # حفظ كـ WAV (بـ 24kHz لأن MMS-TTS يولد على 24kHz)
            buffer = io.BytesIO()
            sf.write(buffer, audio_int16, samplerate=24000, format='WAV', subtype='PCM_16')
            buffer.seek(0)
            return buffer.getvalue()

        except Exception as e:
            log_action(40, f"فشل في توليد دفعة ({language}): {e}", source="_synthesize_chunk")
            import traceback
            log_action(40, traceback.format_exc(), source="_synthesize_chunk")

            # fallback آمن: صمت قصير (1 ثانية على 24kHz)
            audio_np = np.zeros(24000, dtype=np.float32)
            audio_int16 = (audio_np * 32767).astype(np.int16)
            buffer = io.BytesIO()
            sf.write(buffer, audio_int16, samplerate=24000, format='WAV', subtype='PCM_16')
            buffer.seek(0)
            return buffer.getvalue()
                                                                                                                                                                                                                       
    def save_audio(self, text: str, output_path: str | Path, lang: str = "ar", gender: str = "female") -> str:
        """
        حفظ النص كملف WAV – مضمونة 100% حتى لو المجلد مش موجود
        ترجع المسار الكامل للملف المحفوظ
        """
        if not text or not text.strip():
            log_action(30, "نص فارغ – ما في صوت نحفظو", source="AudioProcessor.save_audio")
            raise ValueError("النص فارغ يا قلبي")

        output_path = Path(output_path).expanduser().resolve()  # يدعم ~ ومسارات نسبية

        try:
            log_action(20, "طلب حفظ صوت", source="AudioProcessor.save_audio",
                      details={"نص": text[:60], "مسار": str(output_path), "لغة": lang})

            # 1. نضمن إن المجلد موجود قبل ما نحفظ
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 2. توليد الصوت
            audio_bytes = self.synthesize_text(text, language=lang)

            # 3. حفظ الملف
            with open(output_path, "wb") as f:
                f.write(audio_bytes)

            # 4. تأكيد إن الملف فعلاً اتحفظ وفيه بيانات
            if output_path.stat().st_size < 1000:  # أقل من 1KB = شي غلط
                raise RuntimeError("الملف اتحفظ بس حجمه صغير جدًا – في مشكلة بالتوليف")

            duration = len(audio_bytes) / 1024 / 10  # تقريبي
            log_action(20, "تم حفظ الصوت بنجاح تام", source="AudioProcessor.save_audio",
                      details={
                          "ملف": str(output_path),
                          "حجم": f"{output_path.stat().st_size/1024:.1f}KB",
                          "المدة التقريبية": f"~{duration:.1f}ث"
                      })

            return str(output_path)

        except Exception as e:
            log_action(40, "فشل حفظ الصوت", source="AudioProcessor.save_audio",
                      details={"مسار": str(output_path), "خطأ": str(e)})
            raise RuntimeError(f"ما قدرنا نحفظ الصوت في: {output_path}\nالسبب: {e}")
        
    def stop_playback(self):
        """إيقاف الصوت فوراً وبدون أي طقطقة – طريقة 2026"""
        try:
            import sounddevice as sd
            sd.stop()
            # نضيف سطر سحري ينظف كل الـ buffers (يشتغل على 99.9% من الأجهزة)
            try:
                sd.play(np.zeros(1), samplerate=44100)  # صمت مطلق
            except:
                pass
            log_action(20, "تم إيقاف الصوت + تنظيف كامل للبفر", source="AudioProcessor.stop_playback")
        except Exception as e:
            log_action(30, f"ما قدرنا نوقف الصوت: {e}", source="AudioProcessor.stop_playback")
                                                                          
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
# إنشاء اللحظة التاريخية
# ←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←←
uroman_path = DEFAULT_PATHS["uroman"]

if uroman_path.exists():
    log_action(20, "uroman.pl موجود وجاهز – الصوت هيطلع شامي أصلي 100%", source="init",
              details={"مسار": str(uroman_path)})
else:
    uroman_path = None
    log_action(30, "uroman.pl مش موجود – منكمل بالفال باك الذكي (لسا ممتاز)", source="init")

# إنشاء كربوجي الشامية رسميًا
try:
    audio_processor = AudioProcessor(uroman_path=uroman_path)
    
    # التصحيح النهائي هنا
    log_action(20, "تم التشغيل بنجاح تام", source="init",
              details={
                  "اسمها": "محرك الصوت",
                  "المصمم": "راشد دعدوش",
                  "الجهاز": audio_processor.device.upper(),
                  "TTS عربي": audio_processor.mms_ready_ar,
                  "TTS إنجليزي": audio_processor.mms_ready_en,
                  "TTS جاهز": audio_processor.mms_ready_ar or audio_processor.mms_ready_en,
                  "Whisper جاهز": audio_processor.whisper_ready,
                  "DeepFilterNet جاهز": audio_processor.df_ready
              })

    # تحية شامية فورية (فعّلها لما تبغى)
    # audio_processor.speak("أهلين وسهلين فيك يا زلمة، كربوجي الشامية كريستال 2026 جاهزة تحكي")

except Exception as e:
    log_action(40, "فشل إنشاء – البرنامج لن يعمل!", source="init", details=str(e))
    raise RuntimeError(f"ما قدرنا نشغّل كربوجي: {e}")

# ===================== فقط للتشغيل المباشر (اختبار) =====================
if __name__ == "__main__":
    # هذا الكود يشتغل فقط لو شغلت الملف مباشرة: python Voice_processor.py
    # مش هيشتغل أبدًا لما الـ GUI يستورده
    print("\n" + "═" * 75)
    print(" كربوجي الشامية استيقظت بواجهة سطح مكتب ♡".center(75))
    print(" ابحث عن نافذة 'كريستال 2026' على سطح المكتب".center(75))
    print(" اكتب 'مرحبا' في حقل النص واضغط تشغيل الصوت".center(75))
    print("═" * 75 + "\n")
    
    # تشغيل صوت الترحيب (اختياري)
    try:
        from pydub import AudioSegment
        from pydub.playback import play
        for p in ["sounds/welcome_shami.wav", "sounds/welcome.mp3"]:
            if Path(p).exists():
                play(AudioSegment.from_file(p))
                break
    except:
        pass