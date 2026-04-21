"""爬取中央纪委「警钟」栏目案例，导入暗黑职场素材库。

策略：先用 web_fetch 风格的 HTTP 请求抓列表页，再逐个抓详情页正文。
对于被验证码拦截的页面，标记为 FAILED 留待手动处理。

用法:
    source .venv/bin/activate
    python scripts/crawl_jingzhong.py [--max-pages N] [--dry-run] [--output FILE]
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

# 确保项目根目录在 sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from runtime.materials import add_material

BASE_URL = "https://www.ccdi.gov.cn/jzn/"
SESSIONS = requests.Session()
SESSIONS.headers.update({
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
})


def fetch_html(url: str) -> BeautifulSoup | None:
    """获取页面 HTML，返回 BeautifulSoup。失败返回 None。"""
    try:
        resp = SESSIONS.get(url, timeout=30)
        resp.encoding = resp.apparent_encoding or "utf-8"
        if resp.status_code != 200:
            return None
        # 检查是否被验证码拦截
        if "captchaPage" in resp.text or "验证" in resp.text[:500]:
            return None
        return BeautifulSoup(resp.text, "lxml")
    except Exception:
        return None


def parse_list_page(soup: BeautifulSoup) -> list[dict]:
    """从列表页解析出案例标题、链接、日期。"""
    articles = []
    
    # 尝试多种列表结构选择器
    items = (
        soup.select("ul.list_wh li") 
        or soup.select("ul.list li") 
        or soup.select("div.list li")
        or soup.select(".news_list li")
        or soup.select("ul.wh_sh li")
    )
    
    if not items:
        # 兜底：查找所有包含链接的 li
        items = [li for li in soup.select("li") if li.find("a")]
    
    for li in items:
        a_tag = li.find("a")
        if not a_tag:
            continue
        title = a_tag.get_text(strip=True)
        href = a_tag.get("href", "")
        if not title or not href:
            continue
        if href.startswith("javascript") or href == "#":
            continue
        
        full_url = urljoin(BASE_URL, href)
        
        # 提取日期
        date_text = ""
        date_span = li.find("span") or li.find("em")
        if date_span:
            date_match = re.search(r"(\d{4}[-/]\d{2}[-/]\d{2})", date_span.get_text())
            if date_match:
                date_text = date_match.group(1)
        if not date_text:
            date_match = re.search(r"(\d{4}[-/]\d{2}[-/]\d{2})", li.get_text())
            if date_match:
                date_text = date_match.group(1)
        
        articles.append({
            "title": title,
            "url": full_url,
            "date": date_text,
        })
    
    return articles


def parse_article(soup: BeautifulSoup) -> dict:
    """从文章详情页提取正文。"""
    result = {
        "title": "",
        "content": "",
        "date": "",
    }
    
    # 标题 - 尝试多种选择器
    for sel in ["h1", ".article-title", ".tit", ".detail-title", ".bt"]:
        tag = soup.select_one(sel)
        if tag and tag.get_text(strip=True):
            result["title"] = tag.get_text(strip=True)
            break
    
    # 正文 - 尝试多种选择器
    content_selectors = [
        ".article-content", ".detail-content", "#content", 
        ".content", ".TRS_Editor", "div.text", ".txt", ".zw"
    ]
    for sel in content_selectors:
        tag = soup.select_one(sel)
        if tag:
            # 清理
            for s in tag.find_all(["script", "style"]):
                s.decompose()
            text = tag.get_text(separator="\n", strip=True)
            if len(text) > 100:
                result["content"] = text
                break
    
    # 如果上述选择器都没有命中，尝试找最长的文本块
    if not result["content"]:
        all_divs = soup.find_all("div")
        longest = ""
        for div in all_divs:
            for s in div.find_all(["script", "style", "nav", "header", "footer"]):
                s.decompose()
            text = div.get_text(separator="\n", strip=True)
            if len(text) > len(longest):
                longest = text
        if len(longest) > 200:
            result["content"] = longest
    
    # 日期
    for sel in [".article-date", ".detail-date", ".pubtime", "span.date", ".time"]:
        tag = soup.select_one(sel)
        if tag:
            result["date"] = tag.get_text(strip=True)
            break
    
    return result


def is_text_article(url: str) -> bool:
    """判断是否为图文案例（非视频）。"""
    if "v.ccdi.gov.cn" in url:
        return False
    if "ccdi.gov.cn" not in url:
        return False
    return True


def crawl_and_import(
    max_pages: int = 9,
    dry_run: bool = False,
    output: str | None = None,
) -> list[dict]:
    """主流程：抓取 → 解析 → 导入。"""
    all_articles = []
    results = []
    
    print("=" * 60)
    print("🔍 开始爬取中央纪委「警钟」栏目案例")
    print("=" * 60)
    
    # ── Phase 1: 收集所有列表页的案例链接 ──
    for page_num in range(1, max_pages + 1):
        if page_num == 1:
            page_url = urljoin(BASE_URL, "index.html")
        else:
            page_url = urljoin(BASE_URL, f"index_{page_num}.html")
        
        print(f"\n📄 列表页 {page_num}/{max_pages}: {page_url}")
        
        soup = fetch_html(page_url)
        if not soup:
            print(f"  ❌ 抓取失败（可能被验证码拦截）")
            continue
        
        articles = parse_list_page(soup)
        print(f"  ✅ 发现 {len(articles)} 条案例")
        all_articles.extend(articles)
        time.sleep(0.5)
    
    print(f"\n📊 共收集到 {len(all_articles)} 条案例链接")
    
    # ── Phase 2: 逐个抓取正文 ──
    text_count = 0
    skip_count = 0
    fail_count = 0
    
    for i, info in enumerate(all_articles, 1):
        title = info["title"]
        url = info["url"]
        
        # 跳过视频
        if not is_text_article(url):
            print(f"\n  ⏭️ [{i}/{len(all_articles)}] 视频案例: {title}")
            results.append({"title": title, "status": "skipped_video", "url": url})
            skip_count += 1
            continue
        
        print(f"\n  📖 [{i}/{len(all_articles)}] {title}")
        
        soup = fetch_html(url)
        if not soup:
            print(f"    ❌ 详情页抓取失败")
            results.append({"title": title, "status": "fetch_failed", "url": url})
            fail_count += 1
            time.sleep(1)
            continue
        
        detail = parse_article(soup)
        if not detail["title"]:
            detail["title"] = title
        if not detail["date"]:
            detail["date"] = info.get("date", "")
        
        content = detail["content"]
        if not content or len(content.strip()) < 100:
            print(f"    ⚠️ 内容不足({len(content)}字符)")
            results.append({
                "title": detail["title"], 
                "status": "content_too_short", 
                "length": len(content),
                "url": url,
            })
            fail_count += 1
            time.sleep(1)
            continue
        
        print(f"    ✅ {len(content)} 字符")
        
        if not dry_run:
            try:
                material_id = add_material(
                    title=detail["title"],
                    source="中央纪委国家监委网站-警钟",
                    category="贪腐案例",
                    content=content,
                    file_type="CRAWL",
                    original_filename=None,
                    tags=["警钟", "贪腐", "案例"],
                    metadata={
                        "url": url,
                        "date": detail["date"],
                    },
                )
                print(f"    💾 已导入素材库 (id={material_id})")
                results.append({
                    "title": detail["title"],
                    "status": "imported",
                    "material_id": material_id,
                    "length": len(content),
                    "url": url,
                })
                text_count += 1
            except Exception as e:
                print(f"    ❌ 导入失败: {e}")
                results.append({
                    "title": detail["title"],
                    "status": "import_failed",
                    "error": str(e),
                    "url": url,
                })
                fail_count += 1
        else:
            print(f"    🔍 [dry-run]")
            results.append({
                "title": detail["title"],
                "status": "dry_run",
                "length": len(content),
                "url": url,
            })
            text_count += 1
        
        time.sleep(1)
    
    # ── 汇总 ──
    print("\n" + "=" * 60)
    print("📊 抓取汇总")
    print("=" * 60)
    print(f"  ✅ 成功: {text_count}")
    print(f"  ⏭️ 跳过(视频): {skip_count}")
    print(f"  ❌ 失败: {fail_count}")
    print(f"  📊 总计: {len(results)}")
    
    # 保存结果
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n📁 结果已保存到: {out_path}")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="爬取中央纪委「警钟」栏目案例")
    parser.add_argument("--max-pages", type=int, default=9, help="最多抓取几页（默认9）")
    parser.add_argument("--dry-run", action="store_true", help="只抓取不写入数据库")
    parser.add_argument("--output", type=str, default=None, help="保存结果JSON文件路径")
    args = parser.parse_args()
    
    crawl_and_import(
        max_pages=args.max_pages,
        dry_run=args.dry_run,
        output=args.output,
    )
