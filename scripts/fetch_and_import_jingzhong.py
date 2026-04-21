"""直接用 web_fetch 抓取正文并导入素材库（一次一篇文章，间隔较长避免验证码）。

使用方式：在 Agent 会话中，通过 execute_command 调用此脚本，
每次处理一篇案例。脚本会读取 data/jingzhong_cases.json 中的案例列表，
对尚未导入的案例，用 requests 抓取正文后导入。

如果 requests 被验证码拦截，Agent 可以用 web_fetch 工具手动抓取后，
将内容写入 data/jingzhong_content/{编号}.md，再运行此脚本导入。

用法:
    source .venv/bin/activate
    # 抓取并导入所有（间隔5秒）
    python scripts/fetch_and_import_jingzhong.py --all --delay 5
    
    # 只导入已有 md 文件但尚未入库的
    python scripts/fetch_and_import_jingzhong.py --import-only
    
    # 查看导入状态
    python scripts/fetch_and_import_jingzhong.py --status
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from runtime.materials import add_material, list_materials

CASES_FILE = PROJECT_ROOT / "data" / "jingzhong_cases.json"
CONTENT_DIR = PROJECT_ROOT / "data" / "jingzhong_content"

BASE_URL = "https://www.ccdi.gov.cn/jzn/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


def load_cases() -> list[dict]:
    """加载案例列表。"""
    if not CASES_FILE.exists():
        print(f"❌ 案例文件不存在: {CASES_FILE}")
        return []
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def fetch_article(url: str) -> str | None:
    """用 requests 抓取文章正文，失败返回 None。"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30)
        resp.encoding = resp.apparent_encoding or "utf-8"
        if resp.status_code != 200:
            return None
        if "captchaPage" in resp.text or "验证" in resp.text[:500]:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        for sel in [".article-content", ".detail-content", "#content",
                     ".content", ".TRS_Editor", "div.text", ".txt", ".zw"]:
            tag = soup.select_one(sel)
            if tag:
                for s in tag.find_all(["script", "style"]):
                    s.decompose()
                text = tag.get_text(separator="\n", strip=True)
                if len(text) > 200:
                    return text
        # 兜底：找最长文本
        longest = ""
        for div in soup.find_all("div"):
            for s in div.find_all(["script", "style", "nav", "header", "footer"]):
                s.decompose()
            text = div.get_text(separator="\n", strip=True)
            if len(text) > len(longest):
                longest = text
        return longest if len(longest) > 200 else None
    except Exception:
        return None


def import_from_md(case_num: int, case: dict) -> bool:
    """从已有的 md 文件导入素材库。"""
    md_file = CONTENT_DIR / f"{case_num:02d}.md"
    if not md_file.exists():
        return False
    
    content = md_file.read_text(encoding="utf-8")
    # 清理 markdown 标记
    content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
    content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
    content = re.sub(r'\*(.+?)\*', r'\1', content)
    content = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', content)
    content = re.sub(r'^---+$', '', content, flags=re.MULTILINE)
    content = re.sub(r'\n{3,}', '\n\n', content)
    content = content.strip()
    
    if len(content) < 200:
        return False
    
    add_material(
        title=case["title"],
        source="中央纪委国家监委网站-警钟",
        category="贪腐案例",
        content=content,
        file_type="CRAWL",
        original_filename=None,
        tags=["警钟", "贪腐", "案例", case["person"]],
        metadata={
            "url": case["url"],
            "person": case["person"],
            "position": case["position"],
        },
    )
    return True


def show_status():
    """显示导入状态。"""
    cases = load_cases()
    existing = list_materials(source="中央纪委国家监委网站-警钟")
    existing_titles = {m["title"] for m in existing}
    
    print(f"📋 案例总数: {len(cases)}")
    print(f"✅ 已导入: {len(existing)}")
    print()
    
    for i, case in enumerate(cases, 1):
        status = "✅" if case["title"] in existing_titles else "⬜"
        md_exists = (CONTENT_DIR / f"{i:02d}.md").exists()
        md_flag = " [有md]" if md_exists else ""
        print(f"  {status} [{i:02d}] {case['title']} ({case['person']}){md_flag}")


def run_import(delay: float = 5, import_only: bool = False):
    """批量导入。"""
    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    cases = load_cases()
    existing = list_materials(source="中央纪委国家监委网站-警钟")
    existing_titles = {m["title"] for m in existing}
    
    print(f"📋 案例总数: {len(cases)}")
    print(f"✅ 已导入: {len(existing)}")
    print()
    
    imported = 0
    skipped = 0
    failed = 0
    
    for i, case in enumerate(cases, 1):
        title = case["title"]
        
        if title in existing_titles:
            print(f"  ⏭️ [{i:02d}] 已存在: {title}")
            skipped += 1
            continue
        
        # 先尝试从 md 文件导入
        if import_from_md(i, case):
            print(f"  ✅ [{i:02d}] 从md文件导入: {title}")
            imported += 1
            continue
        
        if import_only:
            print(f"  ⬜ [{i:02d}] 无md文件: {title}")
            skipped += 1
            continue
        
        # 用 requests 抓取
        print(f"  🌐 [{i:02d}] 抓取: {title} ...", end="", flush=True)
        content = fetch_article(case["url"])
        
        if content and len(content) >= 200:
            # 保存 md 文件
            md_file = CONTENT_DIR / f"{i:02d}.md"
            md_file.write_text(content, encoding="utf-8")
            
            # 导入素材库
            add_material(
                title=title,
                source="中央纪委国家监委网站-警钟",
                category="贪腐案例",
                content=content,
                file_type="CRAWL",
                original_filename=None,
                tags=["警钟", "贪腐", "案例", case["person"]],
                metadata={
                    "url": case["url"],
                    "person": case["person"],
                    "position": case["position"],
                },
            )
            print(f" ✅ ({len(content)}字符)")
            imported += 1
        else:
            print(f" ❌ 被验证码拦截")
            failed += 1
            # 写一个空文件标记
            md_file = CONTENT_DIR / f"{i:02d}_FAILED.md"
            md_file.write_text(f"# {title}\n\n抓取失败：被验证码拦截\nURL: {case['url']}\n", encoding="utf-8")
        
        if delay > 0 and i < len(cases):
            time.sleep(delay)
    
    print(f"\n📊 结果: ✅导入{imported} ⏭️跳过{skipped} ❌失败{failed}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="警钟案例导入素材库")
    parser.add_argument("--all", action="store_true", help="抓取并导入所有")
    parser.add_argument("--import-only", action="store_true", help="只导入已有md文件")
    parser.add_argument("--status", action="store_true", help="查看导入状态")
    parser.add_argument("--delay", type=float, default=5, help="请求间隔秒数")
    args = parser.parse_args()
    
    if args.status:
        show_status()
    elif args.import_only:
        run_import(import_only=True)
    elif args.all:
        run_import(delay=args.delay)
    else:
        parser.print_help()
