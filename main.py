from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import yt_dlp

app = FastAPI(title="Batch Adult Downloader - Fixed Stuck Download")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/extract")
async def extract(request: Request):
    data = await request.json()
    urls = data.get("urls", [])

    if not urls:
        return JSONResponse({"error": "Masukkan minimal 1 link"}, status_code=400)

    results = []
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'format_sort': ['res', 'ext:mp4', 'size', 'vcodec:avc'],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            try:
                info = ydl.extract_info(url.strip(), download=False)
                if not info:
                    continue

                formats = [
                    f for f in info.get('formats', [])
                    if f.get('url') and f.get('ext') in ('mp4', 'm4a')
                ]
                formats = sorted(formats, key=lambda x: (
                    x.get('height') or 0,
                    x.get('filesize') or x.get('filesize_approx') or 0
                ), reverse=True)

                best = formats[0] if formats else None

                if best:
                    results.append({
                        "title": info.get('title', 'Video').replace('/', '-').replace('\\', '-'),
                        "thumbnail": info.get('thumbnail'),
                        "referer": "https://www.txnhh.com/",
                        "direct_url": best.get('url'),           # ← ini yang baru
                        "quality": f"{best.get('height') or 'HD'}p"
                    })
            except:
                continue

    return {"videos": results}

# PERBAIKAN UTAMA: sekarang langsung redirect ke CDN (tidak proxy lagi)
@app.get("/download")
async def download_video(url: str = Query(...), title: str = Query("video")):
    filename = f"{title}.mp4".replace('"', '').replace("'", "").replace("/", "-")
    # Redirect langsung ke video URL asli (browser yang download)
    return RedirectResponse(url=url, status_code=302)
