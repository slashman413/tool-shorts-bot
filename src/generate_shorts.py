#!/usr/bin/env python3
"""
tool-shorts-bot — 每日精選 3 個工具介紹 Shorts
從 slashmantools.us 挑選工具，用女聲 TTS + 同步字幕生成 YouTube Shorts
"""
import os, sys, json, re, random, textwrap, subprocess, requests
from pathlib import Path
from datetime import datetime
from typing import Optional

BASE_DIR = Path(__file__).parent.parent
TMP_DIR = BASE_DIR / "tmp"
OUTPUT_DIR = BASE_DIR / "output"
TOOLS_URL = "https://slashmantools.us/tools/"

# ── 工具資料（手動維護，保持精準） ──
TOOLS = [
    {"name": "AI Bio Generator", "url": "https://slashman413.github.io/bio-generator/",
     "tagline": "免費 AI 個人簡介產生器，支援 Instagram、LinkedIn、Twitter 跟 TikTok"},
    {"name": "LLM VRAM Calculator", "url": "https://slashmantools.us/llm-calc/",
     "tagline": "估算跑本地 LLM 需要的 VRAM 跟 RAM，支援 7B 到 405B 模型"},
    {"name": "Token Cost Calculator", "url": "https://slashmantools.us/token-cost-calculator/",
     "tagline": "計算 GPT、Claude、Gemini 的 token 用量跟費用"},
    {"name": "AI Image Size Calculator", "url": "https://slashmantools.us/ai-image-size-calculator/",
     "tagline": "Midjourney、SD 跟 SDXL 的最佳解析度跟比例計算"},
    {"name": "AI Prompt Library", "url": "https://slashmantools.us/ai-prompt-library/",
     "tagline": "超過 100 組可直接複製貼上的 AI 提示詞模板"},
    {"name": "Pomodoro Focus Timer", "url": "https://slashmantools.us/pomodoro-focus-timer/",
     "tagline": "內建白噪音、粉紅噪音、棕色噪音跟雨聲的專注計時器"},
    {"name": "JSON & Regex Dev Tools", "url": "https://slashmantools.us/json-regex-devtools/",
     "tagline": "線上格式化驗證 JSON，測試正規表達式，免安裝"},
    {"name": "Developer Tools", "url": "https://slashmantools.us/dev-tools/",
     "tagline": "Base64 編解碼、URL 編碼、JWT 解碼、UUID 產生器"},
    {"name": "Password Generator", "url": "https://slashmantools.us/password-generator/",
     "tagline": "產生強固的隨機密碼，所有資料都在本地生成不傳送"},
    {"name": "Word & Character Counter", "url": "https://slashmantools.us/word-counter/",
     "tagline": "計算字數、字元、行數、段落的免費線上工具"},
    {"name": "QR Code Generator", "url": "https://slashmantools.us/qr-code-generator/",
     "tagline": "輸入網址或文字，立刻產生 QR Code 並下載 PNG"},
    {"name": "Unit Converter", "url": "https://slashmantools.us/unit-converter/",
     "tagline": "轉換長度、重量、溫度、速度跟資料大小的單位換算"},
    {"name": "Image Compressor & Resizer", "url": "https://slashmantools.us/image-compressor/",
     "tagline": "瀏覽器內直接壓縮跟縮放 JPG、PNG、WebP，不上傳伺服器"},
    {"name": "Color Tools", "url": "https://slashmantools.us/color-tools/",
     "tagline": "選色器、HEX-RGB 互轉、調色盤跟 CSS 漸層產生器"},
    {"name": "Compound Interest Calculator", "url": "https://slashmantools.us/compound-calculator/",
     "tagline": "模擬定期定額投資 ETF 跟退休金的複利計算機"},
    {"name": "Everyday Calculators", "url": "https://slashmantools.us/calculators/",
     "tagline": "BMI、百分比、貸款、年齡跟小費的日常計算工具"},
    {"name": "PDF Tools", "url": "https://slashmantools.us/pdf-tools/",
     "tagline": "圖片轉 PDF 跟 PDF 合併，全部在瀏覽器完成不上傳"},
    {"name": "Macro Economy Dashboard", "url": "https://slashmantools.us/macro-dashboard/dashboard.html",
     "tagline": "每日更新的總體經濟指標儀表板，掌握大盤趨勢"},
    {"name": "Taiwan ETF Analysis", "url": "https://slashmantools.us/tw-etf-dashboard/dashboard.html",
     "tagline": "0050、0056、00878 等熱門 ETF 的每日深度分析"},
    {"name": "Surge Stock DNA Screener", "url": "https://slashmantools.us/twse-surge-stocks-dna/",
     "tagline": "台股飆股篩選器，搭配 20 年回測歷史資料"},
    {"name": "Taiwan Stock Backtester", "url": "https://slashmantools.us/twse-backtests/",
     "tagline": "用真實歷史資料驗證你的台股交易策略"},
    {"name": "Global Events 3D Globe", "url": "https://slashmantools.us/global-events-tracker/",
     "tagline": "在 3D 地球儀上追蹤全球 60 多個重大新聞事件"},
]

# 開場白模板
INTROS = [
    "你今天需要什麼工具呢？來看看這三個超實用的網站！",
    "三個你一定要知道的免費線上工具，先收藏起來！",
    "每天都要用的工具，這三個真的幫我省超多時間！",
    "免費又好用的工具來了～趕快筆記起來！",
    "工程師跟創作者必備的三個工具，你看過幾個？",
]

# 結尾模板
OUTROS = [
    "以上就是今天的工具推薦，喜歡的話幫我按讚分享喔！想要自動生成這樣的 Shorts 嗎？點下方說明欄連結試試 ShortsGen Pro！",
    "每天為你介紹三個好用的工具，我們明天見！順便說一下，這支 Shorts 就是用 ShortsGen Pro 自動生成的喔～",
    "想看更多免費工具，記得訂閱我的頻道！也歡迎試試 ShortsGen Pro，自動幫你產出這種 Shorts！",
    "你有用過這些工具嗎？留言告訴我你的心得！如果也想自動化產出 Shorts，可以試試 ShortsGen Pro！",
]


def pick_tools(count: int = 3) -> list[dict]:
    """隨機挑選 N 個工具"""
    return random.sample(TOOLS, min(count, len(TOOLS)))


def build_script(tools: list[dict]) -> str:
    """產生 Shorts 腳本（含開場 + 各工具介紹 + 結尾）"""
    intro = random.choice(INTROS)
    lines = [intro]
    for i, tool in enumerate(tools, 1):
        text = f"第{i}個，{tool['name']}，{tool['tagline']}"
        lines.append(text)
    lines.append(random.choice(OUTROS))
    return "\n\n".join(lines)


def run_tts(text: str, voice: str, output_path: Path) -> Path:
    """執行 edge-tts 生成音檔 + SRT 字幕檔"""
    srt_path = output_path.with_suffix(".srt")
    cmd = [
        sys.executable or "python3", "-m", "edge_tts",
        "--voice", voice,
        "--text", text,
        "--write-media", str(output_path),
        "--write-subtitles", str(srt_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return srt_path


def get_video_duration(video_path: Path) -> float:
    """用 ffprobe 取得影片長度"""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    r = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return float(r.stdout.strip())


def get_audio_duration(audio_path: Path) -> float:
    """用 ffprobe 取得音檔長度"""
    return get_video_duration(audio_path)


def fetch_pixabay_video(api_key: str, output_path: Path) -> Path:
    """從 Pixabay 下載 720x1280 直式影片"""
    # 搜尋關鍵字 — 偏科技/城市/辦公室風格
    queries = [
        "nature landscape", "sunset ocean", "city night",
        "mountain lake", "forest river", "beach waves",
        "sky clouds", "stars night", "aurora borealis",
    ]
    query = random.choice(queries)

    url = "https://pixabay.com/api/videos/"
    
    # Try up to 3 different queries to find portrait videos
    for attempt in range(3):
        params = {
            "key": api_key,
            "q": query,
            "orientation": "vertical",
            "per_page": 20,
        }
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if data.get("hits"):
            # 只選直式影片
            portrait_hits = []
            for hit in data["hits"]:
                videos = hit.get("videos", {})
                for fmt in ["medium", "large", "small"]:
                    v = videos.get(fmt)
                    if v and v.get("width") and v.get("height"):
                        w, hgt = v["width"], v["height"]
                        if hgt > w:  # portrait orientation
                            portrait_hits.append((w, hgt, v, hit))
                        break
            
            if portrait_hits:
                portrait_hits.sort(key=lambda x: abs(x[0] - 720) + abs(x[1] - 1280))
                best = portrait_hits[0][2]
                print(f"  📹 Video: {best['width']}x{best['height']} from {best['url']}")
                
                video_url = best["url"]
                r = requests.get(video_url, timeout=30)
                r.raise_for_status()
                output_path.write_bytes(r.content)
                return output_path
        
        # Try a different query
        print(f"  Retry {attempt+1}: no portrait videos for '{query}', trying another...")
        query = random.choice(queries)
    
    raise RuntimeError("No portrait videos found after 3 attempts")


def gen_background_music(output_path: Path, duration: float) -> Path:
    """用 FFmpeg 產生鋼琴背景音樂"""
    # C大調和弦進行: C-G-Am-F (I-V-vi-IV)
    freqs = [262, 392, 440, 349]  # C4, G4, A4, F4
    beat = duration / 4  # Each chord gets equal time
    filter_parts = []
    for i, freq in enumerate(freqs):
        filter_parts.append(
            f"sine=f={freq}:d={beat}:r=44100,volume=0.08[a{i}]"
        )

    # Mix all together
    mix_inputs = "".join(f"[a{i}]" for i in range(len(freqs)))
    filter_chain = (
        ";".join(filter_parts)
        + f";{mix_inputs}amix=inputs={len(freqs)}:duration=first"
        + f",afade=t=in:ss=0:d=1,afade=t=out:st={max(duration-2,0)}:d=2"
    )

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo,atrim=0:{duration}",
        "-filter_complex", filter_chain,
        "-shortest",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return output_path


def process_video(
    video_path: Path,
    audio_path: Path,
    srt_path: Path,
    music_path: Path,
    output_path: Path,
):
    """合成最終影片：loop video to fit audio + 字幕 + 背景音樂 + TTS"""
    vb_duration = get_video_duration(video_path)
    ab_duration = get_audio_duration(audio_path)

    # 計算需要 loop 幾次
    loop_count = int(ab_duration / vb_duration) + 1

    # SRT 字幕至 ASS (FFmpeg 原生支援 SRT)
    # 字幕樣式設定（使用通用字型）
    subtitle_style = (
        "FontName=Noto Sans CJK SC,FontSize=28,PrimaryColour=&H00FFFFFF,"
        "BackColour=&H00000000,Bold=1,Alignment=10,"
        "BorderStyle=1,Outline=1,Shadow=0,MarginV=24"
    )

    tmp_looped = TMP_DIR / "looped_video.mp4"

    # Step 1: Loop & trim video to match audio
    loop_count = int(ab_duration / vb_duration) + 1
    cmd_loop = [
        "ffmpeg", "-y",
        "-stream_loop", str(loop_count - 1),
        "-i", str(video_path),
        "-t", str(ab_duration),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2:color=black",
        "-r", "30",
        str(tmp_looped),
    ]
    subprocess.run(cmd_loop, check=True, capture_output=True, text=True)
    print(f"  🎬 Looped video: {ab_duration:.1f}s")

    # Step 2: Burn subtitles + mix audio + background music
    # Use absolute path with escaped colon for subtitles filter
    srt_path_str = str(srt_path).replace('\\', '/')
    # Escape colon in path for FFmpeg filter syntax (only in subtitles filter context)
    srt_filter_path = srt_path_str.replace(':', '\\:')
    cmd_final = [
        "ffmpeg", "-y",
        "-i", str(tmp_looped),
        "-i", str(audio_path),
        "-i", str(music_path),
        "-filter_complex",
        f"[1:a][2:a]amix=inputs=2:duration=first:weights=1 0.4[aud];"
        f"[0:v]subtitles='{srt_filter_path}':force_style='{subtitle_style}'[v]",
        "-map", "[v]",
        "-map", "[aud]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path),
    ]
    subprocess.run(cmd_final, check=True, capture_output=True, text=True)
    print(f"  ✅ Final video: {output_path}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate tool introduction Shorts")
    parser.add_argument("--voice", default="zh-TW-HsiaoChenNeural",
                        help="Edge TTS voice (default: zh-TW-HsiaoChenNeural)")
    parser.add_argument("--count", type=int, default=3,
                        help="Number of tools to feature (default: 3)")
    parser.add_argument("--api-key", help="Pixabay API key (default: PIXABAY_API_KEY env)")
    parser.add_argument("--upload", action="store_true",
                        help="Upload to YouTube after generation")
    args = parser.parse_args()

    TMP_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    api_key = args.api_key or os.environ.get("PIXABAY_API_KEY")
    if not api_key:
        print("❌ Need PIXABAY_API_KEY")
        sys.exit(1)

    today = datetime.now().strftime("%Y%m%d")
    print(f"🎬 Tool Shorts Generator — {today}")

    # 1. Pick tools
    tools = pick_tools(args.count)
    print(f"📌 Picked: {', '.join(t['name'] for t in tools)}")

    # 2. Build script
    script = build_script(tools)
    print(f"📝 Script:\n{script}\n")

    # 3. Generate TTS audio + SRT
    print("🎙️  Generating TTS...")
    tts_audio = TMP_DIR / f"tts_{today}.mp3"
    srt_file = run_tts(script, args.voice, tts_audio)
    audio_dur = get_audio_duration(tts_audio)
    print(f"   Audio: {audio_dur:.1f}s, SRT: {srt_file}")

    # 4. Fetch Pixabay video
    print("📹  Fetching video...")
    raw_video = TMP_DIR / f"raw_{today}.mp4"
    fetch_pixabay_video(api_key, raw_video)

    # 5. Generate background music
    print("🎵  Generating music...")
    music_audio = TMP_DIR / f"music_{today}.mp3"
    gen_background_music(music_audio, audio_dur)

    # 6. Process final video
    print("🎬  Processing video...")
    final_video = OUTPUT_DIR / f"tool-shorts-{today}.mp4"
    process_video(raw_video, tts_audio, srt_file, music_audio, final_video)

    file_size = final_video.stat().st_size
    print(f"\n✅ Done! Video: {final_video} ({file_size/1024/1024:.1f} MB)")

    # 7. Upload?
    if args.upload:
        print("📤  Uploading to YouTube...")
        try:
            from upload_youtube import upload_video
            upload_video(str(final_video), tools, script)
        except ImportError:
            print("⚠️  upload_youtube.py not found, skipping upload")

    return final_video


if __name__ == "__main__":
    main()
