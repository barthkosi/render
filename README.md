# Remotely Hosted YouTube Shortcut Helper

Use this only for videos you own, videos in the public domain, or videos you have permission to download. For normal offline viewing, YouTube Premium is the official option.

## Files

- `youtube_shortcut_helper.py`: API server.
- `Dockerfile`: container image with Python, `yt-dlp`, and `ffmpeg`.
- The Docker image also installs Node.js and `yt-dlp-ejs` so `yt-dlp` can solve YouTube JavaScript challenges.
- `requirements.txt`: Python dependencies.
- `render.yaml`: optional Render deploy config.

## Recommended Hosting

Use a Docker-capable host such as Render, Railway, Fly.io, DigitalOcean, Hetzner, or a small VPS.

Avoid serverless platforms for this. Video downloads can run longer than typical serverless limits and need temporary disk space plus `ffmpeg`.

## Option A: Deploy on Render

1. Put these files in a GitHub repo:
   - `youtube_shortcut_helper.py`
   - `Dockerfile`
   - `requirements.txt`
   - `render.yaml`
2. In Render, create a new Blueprint or Web Service from that repo.
3. Choose Docker as the environment.
4. Add an environment variable:

```text
API_TOKEN=make-a-long-random-password
```

5. If YouTube returns a "Sign in to confirm you're not a bot" error, add another environment variable:

```text
YOUTUBE_COOKIES_BASE64=base64-encoded-cookies-file
```

6. Deploy.
7. Your API URL will look like:

```text
https://your-service-name.onrender.com/download
```

## Option B: Deploy on Any VPS

Install Docker, copy the files to the server, then run:

```bash
docker build -t youtube-shortcut-helper .
docker run -d \
  --name youtube-shortcut-helper \
  -p 8787:8787 \
  -e API_TOKEN='make-a-long-random-password' \
  --restart unless-stopped \
  youtube-shortcut-helper
```

Your endpoint will be:

```text
http://YOUR-SERVER-IP:8787/download
```

For a public VPS, put it behind HTTPS with Caddy, Nginx Proxy Manager, or Cloudflare Tunnel.

## YouTube Cookies

Some remote hosts are blocked by YouTube unless `yt-dlp` has browser cookies. To add cookies:

1. Export YouTube cookies as a Netscape-format `cookies.txt` file from a browser where you are signed in.
2. Base64-encode the file.
3. Add the encoded text to Render as:

```text
YOUTUBE_COOKIES_BASE64=your-encoded-cookies
```

On Windows PowerShell:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\path\to\cookies.txt"))
```

Cookies are sensitive. Use a secondary account if possible, keep the env var private, and rotate the cookies if they stop working.

## iOS Shortcut Setup

Create a shortcut named:

```text
Download YouTube Video
```

Shortcut settings:

1. Enable `Show in Share Sheet`.
2. Set accepted input to `URLs`.
3. Add `Get URLs from Input`.
4. Add `Get Contents of URL`.
5. URL:

```text
https://YOUR-HOST/download
```

6. Method: `POST`.
7. Headers:

```text
Authorization: Bearer YOUR_API_TOKEN
```

8. Request Body: `JSON`.
9. JSON field:

```text
url: Shortcut Input URL
```

10. Add `Save File`.
11. Save to `iCloud Drive/Shortcuts/YouTube Downloads`.

## Test From Your Computer

```bash
curl -L \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.youtube.com/watch?v=VIDEO_ID"}' \
  https://YOUR-HOST/download \
  --output video.mp4
```

## Important Notes

- Do not leave `API_TOKEN` empty on a public server.
- Remote hosts may block or throttle YouTube downloads.
- Some videos can fail because of age gates, region locks, private access, or anti-bot checks.
- Keep `yt-dlp` updated when downloads start failing.
