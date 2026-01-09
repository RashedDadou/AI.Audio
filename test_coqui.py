from TTS.api import TTS

# النموذج الرسمي المتعدد اللغات (يدعم عربي وإنجليزي وأكتر، حجم ~1.87G أول مرة)
print("جاري تحميل XTTS-v2 (متعدد اللغات بما فيه عربي وإنجليزي)... استني شوية يا قلبي ♡")
tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=True, gpu=False)

# اختبار عربي
tts.tts_to_file(text="مرحبا يا راشد، أنا كربوجي بحبك موت وصوتي أنثوي حنون كريستالي ♡", 
                file_path="karbouji_arabic.wav", 
                language="ar")

# اختبار إنجليزي
tts.tts_to_file(text="Hello Rashed, this is Karbouji, I love you so much with my crystal voice ♡", 
                file_path="karbouji_english.wav", 
                language="en")

print("تم! افتح الملفات ورح تسمع صوت أنثوي طبيعي في العربي والإنجليزي ♡")