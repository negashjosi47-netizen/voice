"""
Amharic voice prototype backend.

  /tts   -> natural MALE Amharic voice (Microsoft am-ET-AmehaNeural) via edge-tts
  /chat  -> real AI replies via the Anthropic API (optional; needs ANTHROPIC_API_KEY)

Run (PC, Termux, or any small server):
  pip install flask edge-tts anthropic
  export ANTHROPIC_API_KEY=sk-ant-...        # only needed for /chat
  python server.py

Then in the prototype's ☰ menu:
  TTS endpoint  -> http://<server-ip>:8787/tts
  Mode          -> ቀጥታ AI,   endpoint -> http://<server-ip>:8787/chat

Note: an https page cannot call an http server. Open the HTML as a local file
in Chrome, or put the server behind https (e.g. a Cloudflare tunnel).
"""
import asyncio, os
from flask import Flask, request, Response, jsonify
import edge_tts

app = Flask(__name__)
VOICE = "am-ET-AmehaNeural"          # male Amharic
MODEL = os.environ.get("MODEL", "claude-sonnet-5-5")


@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    r.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return r


@app.route("/tts", methods=["POST", "OPTIONS"])
def tts():
    if request.method == "OPTIONS":
        return ("", 204)
    data = request.get_json(force=True)
    text = (data.get("text") or "").strip()
    if not text:
        return ("empty", 400)

    async def synth():
        buf = b""
        comm = edge_tts.Communicate(text, data.get("voice") or VOICE, rate="-3%", pitch="-2Hz")
        async for ch in comm.stream():
            if ch["type"] == "audio":
                buf += ch["data"]
        return buf

    audio = asyncio.run(synth())
    return Response(audio, mimetype="audio/mpeg")


@app.route("/chat", methods=["POST", "OPTIONS"])
def chat():
    if request.method == "OPTIONS":
        return ("", 204)
    import anthropic
    data = request.get_json(force=True)
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    msg = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=data.get("system", ""),
        messages=data.get("messages", []),
    )
    return jsonify(reply="".join(b.text for b in msg.content if b.type == "text"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8787)
