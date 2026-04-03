"""
从微信公众号后台下载已发布文章，保存为 Markdown。
使用方式：python3 scripts/fetch_wechat_articles.py
流程：打开浏览器 → 扫码登录 → 自动抓取文章 → 保存到 inbox/bootstrap/
"""

import json
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from markdownify import markdownify as md

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "inbox" / "bootstrap"
USER_DATA_DIR = BASE_DIR / ".cache" / "playwright_profile"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)


def wait_for_login(page):
    """等待用户扫码登录，检测URL跳转到后台首页"""
    print("\n🔑 请在浏览器中扫码登录公众号后台...")
    print("   登录成功后脚本将自动继续\n")
    # 等待 URL 变为后台首页（最多等 120 秒）
    page.wait_for_url("**/cgi-bin/home**", timeout=120_000)
    print("✅ 登录成功！\n")


def get_token(page):
    """从当前 URL 中提取 token 参数"""
    url = page.url
    match = re.search(r'token=(\d+)', url)
    if match:
        return match.group(1)
    # 也尝试从 cookie 中获取
    return None


def fetch_article_list(page, token):
    """通过后台 API 获取所有已发布文章列表"""
    articles = []
    begin = 0
    count = 5  # 每次请求的数量

    while True:
        api_url = (
            f"https://mp.weixin.qq.com/cgi-bin/appmsg"
            f"?action=list_ex&begin={begin}&count={count}"
            f"&fakeid=&type=9&query=&token={token}&lang=zh_CN"
            f"&f=json&ajax=1"
        )
        resp = page.evaluate(
            """async (url) => {
                const r = await fetch(url, {credentials: 'include'});
                return await r.json();
            }""",
            api_url,
        )

        if resp.get("base_resp", {}).get("ret") != 0:
            print(f"⚠️  API 返回错误: {resp.get('base_resp', {})}")
            break

        app_msg_list = resp.get("app_msg_list", [])
        if not app_msg_list:
            break

        for item in app_msg_list:
            articles.append({
                "title": item.get("title", "untitled"),
                "link": item.get("link", ""),
                "create_time": item.get("create_time", 0),
                "aid": item.get("aid", ""),
                "digest": item.get("digest", ""),
            })

        total = resp.get("app_msg_cnt", 0)
        begin += count
        print(f"   已获取 {len(articles)}/{total} 篇文章列表...")

        if begin >= total:
            break

        # 避免请求过快被限流
        time.sleep(1)

    # 按发布时间升序排列（从早到晚）
    articles.sort(key=lambda x: x["create_time"])
    return articles


def extract_article_content(page, url):
    """打开文章链接，提取正文 HTML 并转换为 Markdown"""
    page.goto(url, wait_until="domcontentloaded", timeout=30_000)

    # 等待文章内容加载
    try:
        page.wait_for_selector("#js_content", timeout=15_000)
    except Exception:
        # 可能遇到验证页面，等待用户手动处理
        print("   ⏳ 页面可能需要验证，请在浏览器中完成操作...")
        page.wait_for_selector("#js_content", timeout=60_000)

    # 提取发布时间
    publish_time = ""
    try:
        time_el = page.query_selector("#publish_time")
        if time_el:
            publish_time = time_el.inner_text().strip()
    except Exception:
        pass

    # 提取作者
    author = ""
    try:
        author_el = page.query_selector("#js_name") or page.query_selector(".rich_media_meta_nickname")
        if author_el:
            author = author_el.inner_text().strip()
    except Exception:
        pass

    # 提取正文 HTML
    content_html = page.eval_on_selector("#js_content", "el => el.innerHTML")

    # 转换为 Markdown
    content_md = md(content_html, heading_style="ATX", strip=["img", "script", "style"])

    # 清理多余空行
    content_md = re.sub(r'\n{3,}', '\n\n', content_md).strip()

    return {
        "content": content_md,
        "publish_time": publish_time,
        "author": author,
    }


def sanitize_filename(title):
    """将标题转为安全的文件名"""
    # 移除或替换不安全字符
    safe = re.sub(r'[<>:"/\\|?*]', '', title)
    safe = safe.strip().replace(' ', '_')
    # 截断过长的文件名
    if len(safe) > 80:
        safe = safe[:80]
    return safe


def main():
    with sync_playwright() as p:
        # 使用持久化上下文（保留登录状态）
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(USER_DATA_DIR),
            headless=False,
            channel="chromium",
            viewport={"width": 1280, "height": 800},
            locale="zh-CN",
        )

        page = browser.pages[0] if browser.pages else browser.new_page()

        # 导航到公众号后台
        page.goto("https://mp.weixin.qq.com/", timeout=30_000)

        # 检查是否已登录
        time.sleep(2)
        current_url = page.url
        if "cgi-bin/home" not in current_url:
            wait_for_login(page)

        token = get_token(page)
        if not token:
            print("❌ 无法获取 token，请确保已成功登录")
            browser.close()
            return

        print(f"🔑 Token: {token[:6]}...\n")

        # 获取文章列表
        print("📋 正在获取文章列表...")
        articles = fetch_article_list(page, token)
        print(f"\n📚 共找到 {len(articles)} 篇文章\n")

        if not articles:
            print("未找到文章，退出。")
            browser.close()
            return

        # 显示文章列表
        for i, art in enumerate(articles):
            ts = time.strftime("%Y-%m-%d", time.localtime(art["create_time"]))
            print(f"  {i+1}. [{ts}] {art['title']}")

        print(f"\n📥 开始下载文章内容...\n")

        # 打开新标签页用于抓取文章内容
        content_page = browser.new_page()
        saved_count = 0

        for i, art in enumerate(articles):
            title = art["title"]
            ts = time.strftime("%Y%m%d", time.localtime(art["create_time"]))
            ts_display = time.strftime("%Y-%m-%d", time.localtime(art["create_time"]))

            filename = f"{sanitize_filename(title)}-{ts}.md"
            filepath = OUTPUT_DIR / filename

            # 跳过已下载的
            if filepath.exists():
                print(f"  ⏭️  [{i+1}/{len(articles)}] 已存在，跳过: {filename}")
                continue

            print(f"  📄 [{i+1}/{len(articles)}] 下载: {title}")

            try:
                result = extract_article_content(content_page, art["link"])

                # 写入 Markdown 文件
                md_content = f"# {title}\n\n"
                md_content += f"> **发布时间**：{result['publish_time'] or ts_display}\n"
                if result["author"]:
                    md_content += f"> **公众号**：{result['author']}\n"
                md_content += f"> **原文链接**：{art['link']}\n\n"
                md_content += f"---\n\n{result['content']}\n"

                filepath.write_text(md_content, encoding="utf-8")
                saved_count += 1
                print(f"       ✅ 已保存: {filename}")

            except Exception as e:
                print(f"       ❌ 下载失败: {e}")

            # 避免请求过快
            time.sleep(2)

        content_page.close()
        print(f"\n🎉 完成！共下载 {saved_count} 篇文章到 inbox/bootstrap/")
        print("   你可以关闭浏览器窗口了。\n")

        browser.close()


if __name__ == "__main__":
    main()
