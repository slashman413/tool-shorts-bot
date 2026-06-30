#!/usr/bin/env python3
"""
tool-shorts-bot — YouTube Uploader
Uploads generated tool introduction Shorts to YouTube.
"""
import os, json, logging, random
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

logger = logging.getLogger(__name__)
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
REFRESH_TOKEN = os.environ.get("GOOGLE_REFRESH_TOKEN", "")


def get_authenticated_service():
    """Get an authenticated YouTube API service using refresh token."""
    token_data = {
        "token": None,
        "refresh_token": REFRESH_TOKEN,
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scopes": SCOPES,
    }
    creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return build("youtube", "v3", credentials=creds)


def upload_video(video_path: str, tools: list[dict], script: str):
    """Upload a video to YouTube as a Short."""
    youtube = get_authenticated_service()

    # Build title and description
    tool_names = [t["name"] for t in tools]
    title = f"🔥 免費線上工具推薦 {', '.join(tool_names[:2])}"
    if len(title) > 80:
        title = title[:77] + "..."

    # Build description
    desc_lines = [
        "✨ 每天三個好用工具，提升你的工作效率！",
        "",
        "📌 本集工具：",
    ]
    for i, t in enumerate(tools, 1):
        desc_lines.append(f"{i}. {t['name']} — {t['tagline']}")
        desc_lines.append(f"   🔗 {t['url']}")
    
    # Randomly pick 1-2 Ko-fi products to promote
    kofi_products = [
        "🎬 自動生成這種 Shorts？👉 ShortsGen Pro → https://ko-fi.com/s/896aa3c229",
        "📊 台股即時訊號掃描 👉 TWSE Premium → https://ko-fi.com/s/b99720d13d",
        "🛒 自動追蹤 Amazon 特價 👉 Deal Finder Pro → https://ko-fi.com/s/5730f8f947",
        "📝 自動生成 SEO 文章 👉 SEO Content Engine → https://ko-fi.com/s/a03f0a8e3b",
    ]
    selected_kofi = random.sample(kofi_products, min(2, len(kofi_products)))
    
    desc_lines += [
        "",
        "🎬 影片來源：Pixabay (Royalty-Free)",
        "🎙️ AI 語音 + 同步字幕",
        "",
        "🔥 更多免費工具 & 自動化服務：",
    ]
    desc_lines.extend(f"• {p}" for p in selected_kofi)
    desc_lines += [
        "",
        "🔧 全部工具：https://slashmantools.us/tools/",
        "",
        "🔔 喜歡的話幫我按讚、分享、訂閱！",
        "",
        "#Shorts #免費工具 #生產力工具 #線上工具 #ShortsGen",
    ]

    body = {
        "snippet": {
            "title": title,
            "description": "\n".join(desc_lines),
            "categoryId": "22",  # People & Blogs
            "tags": ["Shorts", "免費工具", "生產力工具", "線上工具",
                     "工具推薦", "效率工具", "productivity", "free tools",
                     "web tools", "AI工具"],
        },
        "status": {
            "privacyStatus": "public",
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = request.execute()
    video_id = response.get("id")
    print(f"✅ Uploaded! https://youtu.be/{video_id}")
    return video_id
