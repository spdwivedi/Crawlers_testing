# 🎬 Media Extraction & Demuxing Report

**Tool:** `11_yt_dlp_ffmpeg`  
**Action:** `scrape_for_insta`  
**Source:** `mock://test_reel_human_mode`  
**Authentication Mode:** `anonymous`  
**Date:** 2026-10-18 15:56:32 UTC

---

## 📌 Video Metadata & Caption
- **Title:** Antigravity Instagram Reel Stream Capture & Audio Demux Test
- **Uploader:** antigravity_social_crawler
- **Caption / Description:**
> Deterministic multi-chunk HLS stream sample for Stage 1.3 verification #coding #antigravity #crawlers

---

## 🎞️ Stream & Track Demuxing
| Stream / Asset | Format / Codec | Resolution / Sample Rate | File Size | Path |
|----------------|---------------|--------------------------|-----------|------|
| **Combined Video** | `h264` + `aac` | 640x360 @ 30.0 fps | 51.7 KB | `cleaned/combined_video.mp4` |
| **Standalone MP3** | `mp3` | 44.1/48 kHz Stereo | 73.0 KB | `cleaned/extracted_audio.mp3` |
| **Whisper-Ready WAV** | PCM 16-bit | 16,000 Hz Mono | 95.1 KB | `cleaned/extracted_audio.wav` |

---

## 📦 Raw Chunks Intercepted
- Total Chunks Captured: **3**
- Muxing Engine: **FFmpeg 7.1 Essentials (`imageio-ffmpeg`)**
- yt-dlp Version: **`2026.08.19`**
