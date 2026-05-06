from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import yt_dlp

app = FastAPI(title="Batch Adult Downloader - Direct MP4")

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
        # 🔥 OPTIMASI BARU UNTUK xnxx
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'format_sort': ['res', 'ext:mp4', 'size', 'proto:https'],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            try:
                info = ydl.extract_info(url.strip(), download=False)
                if not info:
                    continue

                # 🔥 FILTER AGRESIF: Hanya ambil direct MP4 (bukan .m3u8)
                formats = [
                    f for f in info.get('formats', [])
                    if f.get('url')
                    and f.get('ext') == 'mp4'                    # hanya mp4
                    and '.m3u8' not in f.get('url', '')          # skip semua HLS
                    and f.get('height') is not None
                ]

                # Sort dari resolusi tertinggi
                formats = sorted(formats, 
                               key=lambda x: (x.get('height') or 0, x.get('filesize') or 0), 
                               reverse=True)

                best = formats[0] if formats else None

                if best:
                    results.append({
                        "title": info.get('title', 'Video'),
                        "thumbnail": info.get('thumbnail'),
                        "duration": info.get('duration'),
                        "best_format": {
                            "url": best.get('url'),
                            "quality": f"{best.get('height')}p",
                            "ext": "mp4",
                            "filesize": best.get('filesize') or best.get('filesize_approx')
                        }
                    })
                else:
                    # Kalau tidak ada MP4 direct, kasih pesan
                    results.append({
                        "title": info.get('title', 'Video'),
                        "error": "Tidak ada format MP4 direct (hanya HLS)"
                    })
            except:
                continue

    return {"videos": results}
