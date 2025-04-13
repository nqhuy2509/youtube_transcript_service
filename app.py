import os
import subprocess
import uuid
from flask import Flask, request, jsonify, Response
import webvtt

app = Flask(__name__)

def vtt_to_srt(vtt_file_path):
    srt_output = ""
    for i, caption in enumerate(webvtt.read(vtt_file_path)):
        srt_output += f"{i+1}\n"
        srt_output += f"{caption.start.replace('.', ',')} --> {caption.end.replace('.', ',')}\n"
        srt_output += f"{caption.text}\n\n"
    return srt_output

def download_subtitle(video_url, lang="en"):
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)

    unique_id = str(uuid.uuid4())
    output_template = os.path.join(temp_dir, unique_id)

    def run_yt_dlp(auto=False):
        command = [
            "yt-dlp",
            "--cookies", "cookies.txt",
            "--skip-download",
            "--sub-lang", lang,
            "--sub-format", "vtt",
            "-o", output_template,
            video_url
        ]

        if auto:
            command.append("--write-auto-sub")
        else:
            command.append("--write-sub")

        return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    
    result = run_yt_dlp(auto=False)
    vtt_path = f"{output_template}.{lang}.vtt"

    # Nếu không tìm thấy, thử phụ đề auto
    if not os.path.exists(vtt_path):
        result = run_yt_dlp(auto=True)
        if not os.path.exists(vtt_path):
            return None, "Không tìm thấy phụ đề thường hoặc auto trong ngôn ngữ đã chọn."

    try:
        srt_output = ""
        for i, caption in enumerate(webvtt.read(vtt_path)):
            srt_output += f"{i+1}\n"
            srt_output += f"{caption.start.replace('.', ',')} --> {caption.end.replace('.', ',')}\n"
            srt_output += f"{caption.text}\n\n"

        os.remove(vtt_path)
        os.rmdir(temp_dir)

        return srt_output, None

    except subprocess.CalledProcessError as e:
        return None, f"yt-dlp error: {e.stderr.decode()}"
    except Exception as e:
        return None, str(e)

@app.route("/get_subtitle", methods=["GET"])
def get_subtitle():
    url = request.args.get("video_url")
    lang = request.args.get("lang", "en")

    if not url:
        return jsonify({"error": "Missing 'video_url' parameter"}), 400

    content, error = download_subtitle(url, lang)

    if error:
        return jsonify({"error": error}), 500

    return Response(content, mimetype="text/plain")

@app.route("/")
def home():
    return "✅ YouTube Subtitle API (via yt-dlp) is running."

if __name__ == "__main__":
    app.run(debug=True)
