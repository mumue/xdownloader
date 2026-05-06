from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import yt_dlp
import httpx

app = FastAPI(title="Batch Adult Downloader - 0KB Fixed")

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
        'format_sort': ['res', 'ext:mp4', 'size'],
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
        }
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for url in urls:
            try:
                info = ydl.extract_info(url.strip(), download=False)
                if not info: continue

                formats = [
                    f for f in info.get('formats', [])
                    if f.get('url') and f.get('ext') == 'mp4' and '.m3u8' not in f.get('url', '')
                ]
                formats = sorted(formats, key=lambda x: (x.get('height') or 0, x.get('filesize') or 0), reverse=True)

                best = formats[0] if formats else None
                if best:
                    results.append({
                        "title": info.get('title', 'Video').replace('/', '-').replace('\\', '-'),
                        "thumbnail": info.get('thumbnail'),
                        "referer": info.get('webpage_url', 'https://www.xnxx.com/'),   # 🔥 PENTING
                        "best_format": {
                            "url": best.get('url'),
                            "quality": f"{best.get('height')}p",
                            "ext": "mp4",
                            "filesize": best.get('filesize') or best.get('filesize_approx')
                        }
                    })
            except:
                continue

    return {"videos": results}

# 🔥 PROXY DOWNLOAD VERSI PALING KUAT
@app.get("/download")
async def download_video(url: str = Query(...), title: str = Query("video"), referer: str = Query("https://www.xnxx.com/")):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
        "Accept": "video/mp4,video/*,*/*",
        "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": referer,                          # 🔥 Referer exact dari halaman video
        "Origin": "https://www.xnxx.com",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Dest": "video",
        "Sec-Ch-Ua": '"Chromium";v="134", "Not;A=Brand";v="24", "Google Chrome";v="134"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Range": "bytes=0-"                          # 🔥 Paksa full content
    }

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=180.0) as client:
            async with client.stream("GET", url, headers=headers) as response:
                if response.status_code not in (200, 206):
                    return JSONResponse({"error": f"CDN blocked {response.status_code}"}, status_code=response.status_code)

                filename = f"{title}.mp4".replace('"', '').replace("'", "").replace("/", "-")
                
                return StreamingResponse(
                    response.aiter_bytes(chunk_size=1024*1024),
                    media_type="video/mp4",
                    headers={
                        "Content-Disposition": f'attachment; filename="{filename}"',
                        "Content-Type": "video/mp4"
                    }
                )
    except Exception as e:
        return JSONResponse({"error": f"Proxy error: {str(e)}"}, status_code=500)
