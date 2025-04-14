from flask import Flask, request, jsonify, Response
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from youtube_transcript_api.formatters import SRTFormatter
import re
from youtube_transcript_api.proxies import WebshareProxyConfig
from werkzeug.utils import secure_filename
import os
import whisper
import difflib

model = whisper.load_model("base")


app = Flask(__name__)

def extract_video_id(url_or_id):
    # Nếu người dùng truyền vào URL, tách ID ra
    pattern = r"(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url_or_id)
    return match.group(1) if match else url_or_id

@app.route("/get_subtitle", methods=["GET"])
def get_subtitle():
    video = request.args.get("url")
    lang = request.args.get("lang", "en")  # mặc định tiếng Anh

    if not video:
        return jsonify({"error": "Missing 'video_id' parameter"}), 400

    video_id = extract_video_id(video)

    try:
        ytt_api = YouTubeTranscriptApi(
            #  proxy_config=WebshareProxyConfig(
            #     proxy_username="qjxzpgwt-rotate",
            #     proxy_password="s1jjy2itlljn",
            # )
            )
        # Lấy danh sách transcript
        transcript_list = ytt_api.list_transcripts(video_id)

        try:
            # Ưu tiên phụ đề người dùng chọn (nếu có)
            transcript = transcript_list.find_transcript([lang])
        except:
            # Nếu không có, lấy phụ đề auto-gen
            transcript = transcript_list.find_generated_transcript([lang])

        # Lấy nội dung transcript
        transcript_data = transcript.fetch()
        formatter = SRTFormatter()
        srt = formatter.format_transcript(transcript_data)

        return Response(srt, mimetype="text/plain")

    except VideoUnavailable:
        return jsonify({"error": "Video is unavailable."}), 404
    except TranscriptsDisabled:
        return jsonify({"error": "Transcripts are disabled for this video."}), 403
    except NoTranscriptFound:
        return jsonify({"error": "No transcript found for this video."}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
@app.route("/practice_speaking", methods=["POST"])
def practice_speaking():
    if "audio" not in request.files:
        return jsonify({"error": "Missing audio file"}), 400

    audio_file = request.files["audio"]
    reference_text = request.form.get("text", "").strip().lower()

    if not reference_text:
        return jsonify({"error": "Missing reference text"}), 400

    filename = secure_filename(audio_file.filename)
    filepath = os.path.join("/tmp", filename)
    audio_file.save(filepath)

    try:
        result = model.transcribe(filepath, language="en")
        user_text = result["text"].strip().lower()
        os.remove(filepath)

        # Bước 1: Tách từ
        ref_words = reference_text.split()
        user_words = user_text.split()

        # Bước 2: So sánh từng từ
        matcher = difflib.SequenceMatcher(None, ref_words, user_words)
        wrong_words = []
        correct_count = 0

        for opcode, i1, i2, j1, j2 in matcher.get_opcodes():
            if opcode == "equal":
                correct_count += (i2 - i1)
            elif opcode in ["replace", "delete", "insert"]:
                wrong_words.extend(ref_words[i1:i2])

        total_words = len(ref_words)
        accuracy = round(correct_count / total_words * 100, 2) if total_words > 0 else 0.0

        return jsonify({
            "user_text": user_text,
            "reference_text": reference_text,
            "wrong_words": wrong_words,
            "correct_count": correct_count,
            "total_words": total_words,
            "accuracy_percent": accuracy,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/")
def index():
    return "YouTube Transcript API is running."

if __name__ == "__main__":
    app.run(debug=True)
