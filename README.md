# Universal Video Downloader iOS Shortcut Guide (via Cobalt API)

This guide shows you how to set up a completely free, zero-hosting iOS Shortcut to download videos from almost anywhere (**YouTube, TikTok, Instagram, Twitter/X, Vimeo, Reddit, and more**) using the public **Cobalt API** (`https://api.cobalt.tools/api/json`).

---

## Why Use the Cobalt Route?

- **100% Free**: No VPS subscription or cloud hosting fees.
- **Zero Maintenance**: You don't need to update Python packages, Docker containers, or base64 cookies. The Cobalt maintainers handle bot challenges and IP bans on their end.
- **Privacy-focused**: No tracking, ads, or bloated web interfaces.
- **Multi-Platform Support**: Natively downloads from dozens of major video and audio sharing platforms.

---

## Step-by-Step iOS Shortcut Setup

Follow these steps to create your custom downloader shortcut on iPhone or iPad:

### 1. Create the Shortcut
1. Open the **Shortcuts** app on your iOS device.
2. Tap the **+** icon in the top right to create a new shortcut.
3. Rename the shortcut to: **Download Video** (tap the title at the top to rename).
4. Tap the **i** (info) button at the bottom (or in the details menu) and turn on **Show in Share Sheet**.
5. Set the input type to only accept **URLs** (e.g. tap *"Receive Any input from Share Sheet"*, clear all, and select only *URLs*).

---

### 2. Add the Actions
Add the following actions in order:

#### Action 1: Get URLs from Input
- This extracts the video URL shared from Safari, YouTube, TikTok, etc.

#### Action 2: Get Contents of URL (Call Cobalt API)
- Drag in the **Get Contents of URL** action.
- Set the target URL to:
  ```text
  https://api.cobalt.tools/api/json
  ```
- Tap **Show More** / **Advanced** and configure:
  - **Method**: `POST`
  - **Headers**:
    - `Accept`: `application/json`
    - `Content-Type`: `application/json`
  - **Request Body**: `JSON`
  - **JSON Fields (Add these key-value pairs)**:
    - `url` (type Text): select the **URL** variable (output of Action 1).
    - `videoQuality` (type Text): `720` (options: `360`, `480`, `720`, `1080`, `max`).
    - `filenamePattern` (type Text): `pretty` (options: `classic`, `pretty`, `basic`, `nerdy`).

#### Action 3: Get Dictionary from Input
- Choose the **Get Dictionary from Input** action.
- Set its input to the **Contents of URL** (the JSON response from Cobalt).

#### Action 4: Get Value from Dictionary
- Choose the **Get Value for Key in Dictionary** action.
- Set **Key** to: `url`
- Set **Dictionary** to: the **Dictionary** variable from Action 3.
- *Note: This retrieves the direct streaming/download URL returned by Cobalt.*

#### Action 5: Get Contents of URL (Download Video File)
- Add another **Get Contents of URL** action.
- Set its target URL to the **Dictionary Value** (the download URL retrieved in Action 4).
- *This downloads the actual video/media file directly to your phone.*

#### Action 6: Save File
- Add the **Save File** action.
- Set its input to the downloaded file from Action 5.
- Choose your preferred save location (e.g., `Shortcuts/Downloads` or ask where to save each time).

---

## Advanced Options

If you want to customize your downloads, you can add these optional fields to the JSON body in **Action 2**:

| Key | Type | Value | Description |
| :--- | :--- | :--- | :--- |
| `isAudioOnly` | Boolean | `true`/`false` | Downloads only the audio (e.g., MP3/M4A). Useful for music. |
| `audioFormat` | Text | `mp3` | Choose `mp3`, `ogg`, `wav`, or `best` (default). |
| `isFormatSelection` | Boolean | `true` | Attempts to download the exact requested video format/codec. |

For a complete list of settings, view the official [Cobalt API Documentation](https://github.com/imputnet/cobalt/blob/current/docs/api.md).

---

## Looking to Self-Host?

If you ever want to run your own private downloader backend to avoid third-party API dependencies:
1. Navigate to the [self-hosted/](./self-hosted) directory.
2. Follow the instructions to deploy the FastAPI + `yt-dlp` helper on a VPS or Render.
