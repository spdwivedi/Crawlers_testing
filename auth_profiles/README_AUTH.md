# 🔐 Social Media & Crawler Authentication Profiles

This directory is designated for dropping session cookies, tokens, and browser profiles for authenticated crawling actions across social platforms:

- `insta_cookies.txt`: Netscape formatted cookies or exported Instagram session cookies for `11_yt_dlp_ffmpeg` and `12_instaloader`.
- `instaloader.session`: Serialized Instaloader session file created via `instaloader -l <username>`.
- `fb_cookies.txt`: Netscape formatted cookies for Facebook / Meta scraping with `11_yt_dlp_ffmpeg` and `13_gallery_dl`.
- `cookies.txt`: Generic Netscape cookies file.

> [!SECURITY]
> All files in this folder (except this `README_AUTH.md`) are explicitly excluded from Git in `.gitignore`.
> Never commit real user credentials, passwords, session tokens, or active cookies to version control.
