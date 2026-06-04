import base64
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException
from starlette.background import BackgroundTask
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from yt_dlp import YoutubeDL


app = FastAPI(title="YouTube Shortcut Helper")
API_TOKEN = os.getenv("API_TOKEN")
YOUTUBE_COOKIES_BASE64 = os.getenv("YOUTUBE_COOKIES_BASE64")


class DownloadRequest(BaseModel):
    url: Annotated[HttpUrl, "YouTube video URL"]


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/download")
def download_video(
    request: DownloadRequest,
    authorization: Annotated[str | None, Header()] = None,
):
    if API_TOKEN:
        expected = f"Bearer {API_TOKEN}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Unauthorized")

    url = str(request.url)

    if "youtube.com" not in url and "youtu.be" not in url:
        raise HTTPException(status_code=400, detail="Only YouTube URLs are accepted.")

    temp_dir = TemporaryDirectory()
    temp_path = Path(temp_dir.name)
    output_template = str(Path(temp_dir.name) / "%(title).80s.%(ext)s")

    options = {
        "format": "best[ext=mp4]/bv*+ba/best",
        "format_sort": ["res:720", "ext:mp4:m4a"],
        "outtmpl": output_template,
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    if YOUTUBE_COOKIES_BASE64:
        cookies_path = temp_path / "cookies.txt"
        try:
            cookies_path.write_bytes(base64.b64decode(YOUTUBE_COOKIES_BASE64))
        except Exception as exc:
            temp_dir.cleanup()
            raise HTTPException(
                status_code=500,
                detail="YOUTUBE_COOKIES_BASE64 is not valid base64.",
            ) from exc
        options["cookiefile"] = str(cookies_path)

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = Path(ydl.prepare_filename(info)).with_suffix(".mp4")
            if not filename.exists():
                matches = list(Path(temp_dir.name).glob("*"))
                if not matches:
                    raise RuntimeError("Download finished but no output file was found.")
                filename = matches[0]
    except Exception as exc:
        temp_dir.cleanup()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    response = FileResponse(
        path=filename,
        filename=filename.name,
        media_type="video/mp4",
        background=BackgroundTask(temp_dir.cleanup),
    )
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8787)
