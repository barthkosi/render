import base64
import importlib.metadata
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, HttpUrl
from starlette.background import BackgroundTask
from yt_dlp import YoutubeDL


app = FastAPI(title="YouTube Shortcut Helper")
API_TOKEN = os.getenv("API_TOKEN")
YOUTUBE_COOKIES_BASE64 = os.getenv("YOUTUBE_COOKIES_BASE64")


class DownloadRequest(BaseModel):
    url: Annotated[HttpUrl, "YouTube video URL"]


@app.get("/health")
def health():
    return {"ok": True}


class DebugLogger:
    def __init__(self):
        self.messages = []

    def debug(self, msg):
        self.messages.append(f"[DEBUG] {msg}")

    def info(self, msg):
        self.messages.append(f"[INFO] {msg}")

    def warning(self, msg):
        self.messages.append(f"[WARNING] {msg}")

    def error(self, msg):
        self.messages.append(f"[ERROR] {msg}")


@app.get("/debug")
def debug_info(
    url: str = "https://www.youtube.com/watch?v=NVGuFdX5guE",
    token: str | None = None,
    authorization: Annotated[str | None, Header()] = None,
):
    if API_TOKEN:
        authorized = False
        if authorization == f"Bearer {API_TOKEN}":
            authorized = True
        elif token == API_TOKEN:
            authorized = True

        if not authorized:
            raise HTTPException(status_code=401, detail="Unauthorized")

    # 1. yt-dlp version
    try:
        import yt_dlp
        yt_dlp_version = yt_dlp.version.__version__
    except Exception as e:
        yt_dlp_version = f"Error: {str(e)}"

    # 2. yt-dlp-ejs version
    try:
        yt_dlp_ejs_version = importlib.metadata.version("yt-dlp-ejs")
    except importlib.metadata.PackageNotFoundError:
        yt_dlp_ejs_version = "Not installed"
    except Exception as e:
        yt_dlp_ejs_version = f"Error: {str(e)}"

    # 3. Node version
    try:
        res = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
        node_version = res.stdout.strip() if res.returncode == 0 else f"Exit code {res.returncode}: {res.stderr}"
    except Exception as e:
        node_version = f"Error: {str(e)}"

    # 4. yt-dlp verbose output for url
    logger = DebugLogger()
    ydl_opts = {
        "logger": logger,
        "verbose": True,
        "noplaylist": True,
    }

    status = "Pending"
    try:
        if YOUTUBE_COOKIES_BASE64:
            with TemporaryDirectory() as temp_dir:
                cookies_path = Path(temp_dir) / "cookies.txt"
                cookies_path.write_bytes(base64.b64decode(YOUTUBE_COOKIES_BASE64))
                ydl_opts["cookiefile"] = str(cookies_path)
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=False)
        else:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=False)
        status = "Success"
    except Exception as e:
        status = f"Error: {str(e)}"

    return {
        "yt_dlp_version": yt_dlp_version,
        "yt_dlp_ejs_version": yt_dlp_ejs_version,
        "node_version": node_version,
        "extraction_status": status,
        "logs": logger.messages,
    }


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

    base_options = {
        "outtmpl": output_template,
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
        base_options["cookiefile"] = str(cookies_path)

    try:
        filename = _download_with_fallbacks(url, temp_path, base_options)
    except Exception as exc:
        temp_dir.cleanup()
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    media_type = "video/mp4" if filename.suffix.lower() == ".mp4" else "application/octet-stream"
    response = FileResponse(
        path=filename,
        filename=filename.name,
        media_type=media_type,
        background=BackgroundTask(temp_dir.cleanup),
    )
    return response


def _download_with_fallbacks(url: str, temp_path: Path, base_options: dict) -> Path:
    attempts = [
        {
            **base_options,
            "format": "best[ext=mp4]/bestvideo*+bestaudio/best",
            "format_sort": ["res:720", "ext:mp4:m4a"],
            "merge_output_format": "mp4",
        },
        {
            **base_options,
            "format": "best",
        },
        base_options,
    ]

    last_error = None
    for options in attempts:
        try:
            with YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = Path(ydl.prepare_filename(info))
                mp4_filename = filename.with_suffix(".mp4")
                if mp4_filename.exists():
                    return mp4_filename
                if filename.exists():
                    return filename
                matches = [path for path in temp_path.glob("*") if path.name != "cookies.txt"]
                if matches:
                    return max(matches, key=lambda path: path.stat().st_size)
                raise RuntimeError("Download finished but no output file was found.")
        except Exception as exc:
            last_error = exc

    raise last_error or RuntimeError("Download failed.")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8787)
