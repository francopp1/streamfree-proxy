import os
from flask import Flask, Response, redirect
from playwright.sync_api import sync_playwright
import requests

app = Flask(__name__)

def get_m3u8_stream(embed_url):
    m3u8_url = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        def handle_request(request):
            nonlocal m3u8_url
            if ".m3u8" in request.url and not m3u8_url:
                m3u8_url = request.url

        page.on("request", handle_request)
        try:
            page.goto(embed_url, timeout=15000)
            page.wait_for_timeout(3000)
        except Exception:
            pass
        
        browser.close()
    return m3u8_url

@app.route('/stream/<path:embed_id>')
def stream(embed_id):
    target_url = f"https://streamfree.top/embed/{embed_id}"
    real_stream = get_m3u8_stream(target_url)
    if real_stream:
        return redirect(real_stream)
    return "Stream non trovato", 404

@app.route('/playlist.m3u')
def playlist():
    api_url = "https://streamfree.top/api/v1/streams"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        res = requests.get(api_url, headers=headers).json()
        streams = res.get("streams", [])
    except:
        streams = []

    host = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:5000")
    lines = ["#EXTM3U\n"]
    for s in streams:
        name = s.get("name", "Evento Sportivo")
        embed_url = s.get("embed_url", "")
        embed_id = embed_url.split("/")[-1] if embed_url else ""
        if embed_id:
            lines.append(f'#EXTINF:-1, {name}')
            lines.append(f'{host}/stream/{embed_id}\n')
            
    return Response("\n".join(lines), mimetype='text/plain')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
