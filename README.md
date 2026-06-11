# Remotely Hosted Universal Video Downloader Shortcut Helper

A self-hosted FastAPI helper designed to run on a VPS or Render. It serves as a secure, remote API backend for an iOS Shortcut to download videos from almost anywhere (**YouTube, TikTok, Instagram, Twitter/X, Vimeo, Facebook, and generic websites**) using the power of `yt-dlp` and `ffmpeg`.

---

## Features

- **Universal Support**: Download videos from any platform supported by `yt-dlp`.
- **VPS-Ready**: Easy deployment using Docker or Docker Compose.
- **Cookieless Operation**: Uses `yt-dlp-ejs` and Node.js in the container to solve JavaScript anti-bot challenges automatically. Running on a VPS with a clean IP usually avoids blocks entirely, meaning you don't have to manage cookies.
- **Optional Multi-Site Cookies**: If you do need cookies (e.g. for age-restricted videos or private links), you can pass a single base64-encoded Netscape-format cookie file containing cookies for multiple domains.
- **Token Authorization**: Secures your endpoint with an API token.

---

## Files in the Repo

- `downloader.py`: The FastAPI server code.
- `Dockerfile`: Multi-stage environment installing Python 3.12, Node.js, `ffmpeg`, and dependencies.
- `docker-compose.yml`: Simplified runner orchestration for VPS setups.
- `requirements.txt`: Python package requirements.
- `render.yaml`: Blueprint configuration for Render.com.

---

## Option A: Deploy on a VPS (Recommended)

iOS Shortcuts require your API endpoint to use **HTTPS**. The easiest setup is to run this container on your VPS and reverse-proxy it behind a secure SSL layer using **Caddy**.

### 1. Run via Docker Compose

1. Clone or copy these files into a directory on your VPS.
2. Edit `docker-compose.yml` to set your desired `API_TOKEN`.
3. Launch the container in the background:
   ```bash
   docker compose up -d --build
   ```

Alternatively, run with a single Docker command:
```bash
docker build -t video-downloader .
docker run -d \
  --name video-downloader \
  -p 8787:8787 \
  -e API_TOKEN="your-secure-random-token-here" \
  --restart unless-stopped \
  video-downloader
```

### 2. Set Up HTTPS with Caddy

Install Caddy on your server, point your domain/subdomain to your VPS IP, and add this to your `/etc/caddy/Caddyfile`:

```caddy
downloader.yourdomain.com {
    reverse_proxy localhost:8787
}
```

Restart Caddy:
```bash
sudo systemctl restart caddy
```
Caddy will automatically acquire and renew a free Let's Encrypt SSL certificate. Your endpoint is now:
`https://downloader.yourdomain.com/download`

---

## Option B: Deploy on Render

1. Create a private GitHub repository with the files.
2. Connect the repository to Render and create a new **Web Service** (using Docker).
3. Set the following environment variable:
   - `API_TOKEN` = `your-secure-random-token`
4. If you encounter bot challenges, you can optionally set:
   - `COOKIES_BASE64` = `your-base64-encoded-netscape-cookies`
5. Deploy the service.

---

## Cookie-Free & VPS IP Reputation

By default, the application **does not require cookies** to function.
- Cloud providers (like Render or AWS) share IP ranges that are heavily flagged by video platforms.
- Hosting on a **VPS** grants you a dedicated, clean IP address. Combined with the pre-installed JavaScript-challenge solver (`yt-dlp-ejs`), you will typically be able to download videos completely cookieless.
- If a platform like YouTube ever flags your VPS IP and shows a *"Sign in to confirm you're not a bot"* error, you can export your cookies (in Netscape format) from a signed-in browser session, base64-encode the file, and supply it via the `COOKIES_BASE64` environment variable.

To encode a `cookies.txt` file into base64:
- **Linux/macOS**:
  ```bash
  base64 -w 0 cookies.txt > encoded.txt
  ```
- **Windows PowerShell**:
  ```powershell
  [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\cookies.txt"))
  ```

---

## iOS Shortcut Setup

Create a new Shortcut on your iPhone/iPad to handle sharing and downloading:

1. **Shortcut Configuration**:
   - Rename the Shortcut to: `Download Video`
   - In Shortcut Settings, turn on **Show in Share Sheet**.
   - Set "Shortcut receives" to only accept **URLs**.

2. **Actions**:
   - Add **Get URLs from Input**.
   - Add **Get Contents of URL**:
     - **URL**: `https://downloader.yourdomain.com/download` (or your Render URL)
     - **Method**: `POST`
     - **Headers**:
       - `Authorization`: `Bearer your-api-token-here`
     - **Request Body**: `JSON`
     - **JSON Field**:
       - `url`: `Shortcut Input URL`
   - Add **Save File**:
     - Save the response file to `iCloud Drive/Shortcuts/Downloads` (or any folder of your choice).

---

## Testing the API Locally

You can test the server locally before deploying it to your VPS.

1. **Start the API server**:
   ```bash
   python downloader.py
   ```
2. **Download a YouTube video**:
   ```bash
   curl -L \
     -H "Authorization: Bearer your-api-token-here" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://www.youtube.com/watch?v=NVGuFdX5guE"}' \
     http://localhost:8787/download \
     --output youtube_video.mp4
   ```
3. **Download a Vimeo or other platform video**:
   ```bash
   curl -L \
     -H "Authorization: Bearer your-api-token-here" \
     -H "Content-Type: application/json" \
     -d '{"url":"https://vimeo.com/76979871"}' \
     http://localhost:8787/download \
     --output vimeo_video.mp4
   ```
