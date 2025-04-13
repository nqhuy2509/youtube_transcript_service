from flask import Flask, request, jsonify, Response
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from youtube_transcript_api.formatters import SRTFormatter
import re
from youtube_transcript_api.proxies import WebshareProxyConfig

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
             proxy_config=WebshareProxyConfig(
                proxy_username="brd-customer-hl_a63b1cbf-zone-youtube_transcript",
                proxy_password="1z46rhgu908a",
            )
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

@app.route("/")
def index():
    return "YouTube Transcript API is running."

if __name__ == "__main__":
    app.run(debug=True)
