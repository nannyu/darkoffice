"""将 web_fetch 抓取的警钟案例批量导入素材库。

用 web_fetch 工具逐个抓取的正文内容，存为 markdown 临时文件，
然后通过 materials.import_material() 导入素材库。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from runtime.materials import add_material, list_materials

# 案例元数据
CASES = [
    {"title": "靠企吃企 难抵诱惑终自毁", "url": "https://www.ccdi.gov.cn/jzn/202405/t20240522_349569.html", "person": "谢玉敏", "position": "湖南省娄底经济技术开发投资建设集团有限公司原党委书记、董事长"},
    {"title": "算错人生账 醒悟悔已迟", "url": "https://www.ccdi.gov.cn/jzn/202404/t20240410_340107.html", "person": "梁文菊", "position": "江苏省常州经开区戚墅堰街道党工委原书记"},
    {"title": "不遏贪欲祸身 不受监督自毁", "url": "https://www.ccdi.gov.cn/jzn/202403/t20240327_337208.html", "person": "房志秀", "position": "天津市河北区人民政府办公室原四级调研员"},
    {"title": "私利羁绊迷失方向 家风不正越陷越深", "url": "https://www.ccdi.gov.cn/jzn/202403/t20240313_334014.html", "person": "杨兴友", "position": "贵州省供销合作社联合社原党组成员、理事会原副主任"},
    {"title": "贪欲不可纵 伸手必被捉", "url": "https://www.ccdi.gov.cn/jzn/202402/t20240228_330742.html", "person": "何发理", "position": "陕西省人大常委会农业和农村工作委员会原主任"},
    {"title": "贪财取危 追悔莫及", "url": "https://www.ccdi.gov.cn/yaowenn/202401/t20240124_324154.html", "person": "李庆明", "position": "云南省文山州住房和城乡建设局原党组成员、副局长"},
    {"title": "心莫贪 贪念一起坠深渊", "url": "https://www.ccdi.gov.cn/jzn/202401/t20240102_318888.html", "person": "刘采成", "position": "贵州省遵义市中华职业教育社原专职副主任"},
    {"title": "擅权贪利 跌落深渊", "url": "https://www.ccdi.gov.cn/jzn/202311/t20231129_310729.html", "person": "魏斌", "position": "四川省安岳县政协原主席"},
    # 第9篇被验证码拦截，跳过
    {"title": "规划专家破规矩 心为物役陷囹圄", "url": "https://www.ccdi.gov.cn/yaowenn/202311/t20231108_305973.html", "person": "唐小锋", "position": "四川省达州市通川区政协原副主席"},
    {"title": "防线松动 跌入陷阱", "url": "https://www.ccdi.gov.cn/jzn/202311/t20231115_307496.html", "person": "杨海波", "position": "陕西省安康市文化和旅游广电局原党组书记、局长"},
    {"title": "倚官养商 终究成空", "url": "https://www.ccdi.gov.cn/jzn/202311/t20231101_304214.html", "person": "黄开旺", "position": "湖北省大冶市人大常委会原党组成员、副主任"},
    {"title": "心生攀比入歧途 不知收敛坠深渊", "url": "https://www.ccdi.gov.cn/jzn/202310/t20231025_302675.html", "person": "胡秀军", "position": "重庆市巴南区经济和信息化委员会原副主任"},
    {"title": "玩物丧志 由风及腐", "url": "https://www.ccdi.gov.cn/jzn/202310/t20231011_299159.html", "person": "王正强", "position": "贵州科学院科技与经济战略研究中心原主任"},
    {"title": "甘被围猎 苦果自尝", "url": "https://www.ccdi.gov.cn/jzn/202307/t20230711_274653.html", "person": "张静", "position": "重庆环投惠泽水污染治理有限责任公司原董事长"},
    {"title": "爱打招呼无口不开 频踩红线跌落深渊", "url": "https://www.ccdi.gov.cn/jzn/202206/t20220601_196387.html", "person": "翁建荣", "position": "浙江省发展和改革委员会原党组成员、副主任"},
    {"title": "自认国企特殊 享乐放纵迷打球", "url": "https://www.ccdi.gov.cn/jzn/202206/t20220601_196388.html", "person": "王俭", "position": "宁夏回族自治区原经信委党组副书记、副主任"},
    {"title": "从失衡失落到失控", "url": "https://www.ccdi.gov.cn/jzn/202206/t20220601_196386.html", "person": "徐会良", "position": "云南省大理州文化和旅游局原党组书记、局长"},
    {"title": "被贪婪葬送的警监", "url": "https://www.ccdi.gov.cn/jzn/202206/t20220601_196384.html", "person": "丁仁仁", "position": "浙江省公安厅原警务技术二级总监"},
    {"title": "在围猎面前败下阵来", "url": "https://www.ccdi.gov.cn/jzn/202104/t20210407_16631.html", "person": "赵世军", "position": "西藏自治区原工商局党委书记、副局长"},
]

# web_fetch 抓取到的正文内容文件目录
CONTENT_DIR = Path(PROJECT_ROOT) / "data" / "jingzhong_content"


def clean_markdown(text: str) -> str:
    """去除 web_fetch 返回中的 markdown 格式标记，保留纯文本。"""
    # 去除标题标记
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # 去除加粗标记
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    # 去除斜体标记
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    # 去除链接标记
    text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
    # 去除水平线
    text = re.sub(r'^---+$', '', text, flags=re.MULTILINE)
    # 去除多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def import_all():
    """从 markdown 文件批量导入素材库。"""
    # 检查是否已有警钟素材（避免重复导入）
    existing = list_materials(source="中央纪委国家监委网站-警钟")
    existing_titles = {m["title"] for m in existing}
    
    print(f"📋 已有警钟素材: {len(existing)} 条")
    
    imported = 0
    skipped = 0
    
    for i, case in enumerate(CASES, 1):
        title = case["title"]
        if title in existing_titles:
            print(f"  ⏭️ [{i}] 已存在: {title}")
            skipped += 1
            continue
        
        # 查找对应的 markdown 文件
        md_file = CONTENT_DIR / f"{i:02d}.md"
        if not md_file.exists():
            # 也尝试用标题
            md_file = CONTENT_DIR / f"{title}.md"
        
        if not md_file.exists():
            print(f"  ⚠️ [{i}] 无内容文件: {title}")
            skipped += 1
            continue
        
        content = md_file.read_text(encoding="utf-8")
        content = clean_markdown(content)
        
        if len(content) < 200:
            print(f"  ⚠️ [{i}] 内容过短({len(content)}字符): {title}")
            skipped += 1
            continue
        
        material_id = add_material(
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
        print(f"  ✅ [{i}] 导入成功 (id={material_id}): {title} ({len(content)}字符)")
        imported += 1
    
    print(f"\n📊 导入完成: ✅{imported} ⏭️{skipped}")


if __name__ == "__main__":
    import_all()
