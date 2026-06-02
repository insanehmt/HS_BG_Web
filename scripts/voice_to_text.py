"""voice_to_text.py
簡單的語音轉文字工具（Windows）
需求：先安裝 pyaudio 與 SpeechRecognition
Usage:
  python voice_to_text.py --lang zh-TW

會錄製一次語音（最多 30 秒），使用 Google Web Speech API 進行辨識（需要網路）。
"""
import argparse
import sys

try:
    import speech_recognition as sr
except Exception as e:
    print("請先安裝 SpeechRecognition 與 PyAudio（或透過 install_voice_env.ps1 安裝）。")
    print(e)
    sys.exit(1)


def record_and_transcribe(lang="zh-TW", timeout=None, phrase_time_limit=30):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("調整環境噪音（1 秒）...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("開始錄音，請開始說話（最多 %s 秒或停頓自動結束）..." % phrase_time_limit)
        audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
    try:
        print("辨識中（使用 Google Web Speech API，需網路）...")
        text = r.recognize_google(audio, language=lang)
        print("辨識結果：\n", text)
        return text
    except sr.UnknownValueError:
        print("無法辨識語音（無法理解）")
    except sr.RequestError as e:
        print(f"語音服務錯誤：{e}")
    except Exception as e:
        print(f"其他錯誤：{e}")
    return ""


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--lang', default='zh-TW', help='語言代碼，預設 zh-TW')
    p.add_argument('--limit', type=int, default=30, help='最多錄製秒數')
    args = p.parse_args()
    record_and_transcribe(lang=args.lang, phrase_time_limit=args.limit)
