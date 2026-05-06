from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import yt_dlp

app = FastAPI(title="Universal Adult Downloader")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/extract")
async def extract(request: Request):
    data = await request.json()
    url = data.get("url")

    if not url:
        return JSONResponse({"error": "URL tidak boleh kosong"}, status_code=400)

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:  # Playlist / Channel
                videos = []
                for entry in info['entries']:
                    if not entry: continue
                    formats = sorted([
                        {
                            "format": f.get('format_note') or f.get('format_id') or 'HD',
                            "url": f.get('url'),
                            "ext": f.get('ext'),
                            "quality": f.get('height') or 0,
                            "filesize": f.get('filesize') or f.get('filesize_approx')
                        } for f in entry.get('formats', [])
                        if f.get('url') and f.get('ext') in ['mp4', 'webm']
                    ], key=lambda x: x['quality'], reverse=True)
                    
                    videos.append({
                        "title": entry.get('title', 'No Title'),
                        "url": entry.get('webpage_url'),
                        "thumbnail": entry.get('thumbnail'),
                        "duration": entry.get('duration'),
                        "formats": formats
                    })
                return {"type": "playlist", "title": info.get('title', 'Playlist'), "videos": videos}

            else:  # Single video
                formats = sorted([
                    {
                        "format": f.get('format_note') or f.get('format_id') or 'HD',
                        "url": f.get('url'),
                        "ext": f.get('ext'),
                        "quality": f.get('height') or 0,
                        "filesize": f.get('filesize') or f.get('filesize_approx')
                    } for f in info.get('formats', [])
                    if f.get('url') and f.get('ext') in ['mp4', 'webm']
                ], key=lambda x: x['quality'], reverse=True)

                return {
                    "type": "single",
                    "title": info.get('title', 'Video'),
                    "thumbnail": info.get('thumbnail'),
                    "duration": info.get('duration'),
                    "formats": formats
                }

    except Exception as e:
        return JSONResponse({"error": f"Gagal extract: {str(e)}"}, status_code=500)