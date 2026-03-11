# -*- coding: utf-8 -*-
"""
雪球专栏文章爬虫 - 优化版
"""
import time
import random
import csv
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= 配置区域 =================
# 目标专栏URL (比如 https://xueqiu.com/8790885129/column )
COLUMN_URL = 'https://xueqiu.com/8790885129/column'  # 请替换为实际的专栏URL
CSV_FILENAME = 'xueqiu_column_articles.csv'

# 从哪个页开始抓取（默认为 1）
START_PAGE = 1

# 最大运行时间（秒），0表示无限制
MAX_RUNTIME = 3600  # 1小时

# 最大文章数量，0表示无限制
MAX_ARTICLES = 100

# ===========================================

def init_driver():
    try:
        chrome_options = Options()
        # 移除 'headless' 模式，因为我们需要扫码登录，且需要模拟真实环境
        chrome_options.add_argument('--disable-gpu')
        # 添加一个伪装的 User-Agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')

        # 规避 Selenium 被检测的风险
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # 使用Selenium Manager自动管理ChromeDriver（无需手动下载）
        driver = webdriver.Chrome(options=chrome_options)

        # 消除 webdriver 痕迹
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
                })
            """
        })
        print("[SUCCESS] Browser driver initialized successfully")
        return driver
    except Exception as e:
        print(f"[INFO] Auto-managed driver failed: {str(e)}")
        print("[INFO] Attempting to use local driver...")
        try:
            # 如果自动管理失败，尝试使用本地驱动
            service = Service('./chromedriver.exe')
            driver = webdriver.Chrome(service=service, options=chrome_options)

            # 消除 webdriver 痕迹
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                    })
                """
            })
            print("[SUCCESS] Local driver initialized successfully")
            return driver
        except Exception as e2:
            print(f"[INFO] Local driver failed: {str(e2)}")
            print("[INFO] Trying to install compatible ChromeDriver automatically...")
            try:
                # 尝试使用webdriver-manager自动下载兼容的驱动
                from webdriver_manager.chrome import ChromeDriverManager

                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)

                # 消除 webdriver 痕迹
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                        })
                    """
                })
                print("[SUCCESS] Automatically managed driver initialized successfully")
                return driver
            except ImportError:
                print("[ERROR] webdriver-manager is not installed. Please run: pip install webdriver-manager")
                print("[ERROR] Please ensure you have Chrome installed and compatible ChromeDriver available.")
                return None
            except Exception as e3:
                print(f"[ERROR] All driver initialization methods failed: {str(e3)}")
                print("[ERROR] Please ensure you have Chrome installed and compatible ChromeDriver available.")
                return None

def save_to_csv(data_list):
    """增量保存数据到CSV，防止程序崩溃数据丢失"""
    file_exists = os.path.isfile(CSV_FILENAME)
    with open(CSV_FILENAME, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["article_id", "title", "time", "content", "view_count", "like_count", "comment_count"])
        if not file_exists:
            writer.writeheader() # 如果文件不存在，写入表头
        writer.writerows(data_list)

def smooth_scroll(driver):
    """模拟真人平滑向下滚动，而不是瞬间跳转"""
    current_height = driver.execute_script("return window.pageYOffset")
    # 随机滚动距离，模拟鼠标滚轮
    scroll_distance = random.randint(300, 700)
    target = current_height + scroll_distance

    driver.execute_script(f"window.scrollTo(0, {target});")
    # 随机停顿，模拟阅读时间
    time.sleep(random.uniform(1.5, 4.5))

def expand_all(driver):
    """在抓取前点击页面上所有可能的"展开"按钮以显示全文。"""
    try:
        # 常见含 '展开' 的文本，也尝试英文 'expand' / 'read more'
        xpaths = [
            "//a[contains(text(),'展开') or contains(text(),'展开全文') or contains(text(),'展开更多')]",
            "//button[contains(text(),'展开') or contains(text(),'展开全文') or contains(text(),'展开更多')]",
            "//a[contains(text(),'展开') or contains(text(),'Expand') or contains(text(),'Read more') ]",
            "//button[contains(text(),'Expand') or contains(text(),'Read more') ]",
            "//span[contains(text(),'阅读全文') or contains(text(),'查看全文')]",
        ]

        # 收集所有要点击的元素（去重）
        to_click = []
        for xp in xpaths:
            try:
                elems = driver.find_elements(By.XPATH, xp)
            except Exception:
                elems = []
            for e in elems:
                try:
                    if e and e.is_displayed():
                        to_click.append(e)
                except Exception:
                    continue

        # 点击每个展开元素
        for e in to_click:
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", e)
                time.sleep(0.2)
                try:
                    e.click()
                except Exception:
                    # fallback: 使用 JS 触发点击
                    driver.execute_script("arguments[0].click();", e)
                time.sleep(0.3 + random.random() * 0.5)
            except Exception:
                continue
    except Exception as ex:
        print(f"[WARNING] Error expanding content: {str(ex)}")

def extract_article_content(driver, article_link):
    """提取专栏文章的详细内容"""
    original_window = driver.current_window_handle

    try:
        # 在新标签页中打开文章链接
        driver.execute_script("window.open(arguments[0]);", article_link)

        # 等待新窗口出现
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)

        # 切换到新窗口
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                driver.switch_to.window(window_handle)
                break

        # 等待页面加载
        time.sleep(3)

        # 尝试展开全文内容
        expand_all(driver)
        time.sleep(2)

        # 提取文章标题
        title = ""
        title_selectors = [
            "h1.article__title",
            "h1.XUEQIU_GLOBAL_HEADER_TITLE",
            ".article__bd h1",
            "article header h1",
            "#ArticleTitle",
            "h1[itemprop='headline']"
        ]
        for selector in title_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                title = element.text.strip()
                if title:
                    break
            except Exception:
                continue

        # 提取文章内容
        content = ""
        content_selectors = [
            ".article__bd",
            ".article__content",
            ".detail",
            "article .content",
            ".RichText",
            "#ueditor-box",
            ".timeline-item__content"
        ]
        for selector in content_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                content = element.text.strip()
                if content:
                    break
            except Exception:
                continue

        # 提取时间
        post_time = ""
        time_selectors = [
            ".article__author .time",
            ".article__meta .time",
            ".time",
            ".publish-time",
            "[datetime]"
        ]
        for selector in time_selectors:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                post_time = element.text.strip()
                if post_time:
                    break
            except Exception:
                continue

        # 尝试获取统计数据
        view_count = like_count = comment_count = 0

        # 关闭当前标签页
        driver.close()

        # 切换回原始窗口
        driver.switch_to.window(original_window)

        return {
            "title": title,
            "content": content,
            "time": post_time,
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count
        }

    except Exception as e:
        print(f"[WARNING] Error extracting article details: {str(e)}")
        # 确保切换回原始窗口
        try:
            driver.switch_to.window(original_window)
        except:
            pass
        return None

def main():
    start_time = time.time()
    driver = init_driver()
    if driver is None:
        print("[ERROR] Could not initialize driver, exiting.")
        return

    processed_ids = set() # 记录已经抓取过的文章ID，用于去重

    try:
        # 1. 打开首页并手动登录
        driver.get("https://xueqiu.com")
        print("[INFO] Please scan QR code to login in the opened browser...")
        print("   -> After successful login, press Enter in console to continue...")

        # 添加超时机制，避免无限等待
        login_start_time = time.time()
        while time.time() - login_start_time < 300:  # 最多等待5分钟
            input_result = input_with_timeout("Press Enter after logging in (or 'q' to quit): ", 300)
            if input_result.lower() == 'q':
                print("[INFO] User chose to quit.")
                return
            elif input_result == '':
                break
        else:
            print("[TIMEOUT] Login timeout. Proceeding anyway...")

        # 2. 跳转专栏页面
        driver.get(COLUMN_URL)
        time.sleep(3) # 等待基础页面加载

        # 如果指定从某页开始，优先尝试通过页面底部的分页输入框跳页
        try:
            if MAX_RUNTIME > 0 and (time.time() - start_time) > MAX_RUNTIME:
                print(f"[TIMEOUT] Runtime exceeded {MAX_RUNTIME} seconds. Exiting...")
                return

            if 'START_PAGE' in globals() and START_PAGE and int(START_PAGE) > 1:
                target_page = str(int(START_PAGE))
                # 尝试滚动到底部以显示分页控件
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1 + random.random() * 2)

                pag_input = None
                try:
                    pag_input = driver.find_element(By.CSS_SELECTOR, ".pagination input[type='text']")
                except Exception:
                    # 多尝试几种常见选择器
                    try:
                        pag_input = driver.find_element(By.XPATH, "//div[contains(@class,'pagination')]//input[@type='text']")
                    except Exception:
                        pag_input = None

                if pag_input:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true);", pag_input)
                        time.sleep(0.3)
                        pag_input.clear()
                        pag_input.send_keys(target_page)
                        pag_input.send_keys(Keys.ENTER)
                        print(f"[INFO] Jumped to page: {target_page}")
                        time.sleep(3 + random.random() * 2)
                    except Exception as e:
                        print(f"[ERROR] Failed to jump to page with input: {str(e)}")
                        pag_input = None

                if not pag_input:
                    # 回退方案：通过 URL 参数跳转
                    try:
                        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
                        parsed = urlparse(COLUMN_URL)
                        qs = parse_qs(parsed.query)
                        qs['page'] = [target_page]
                        new_query = urlencode(qs, doseq=True)
                        start_url = urlunparse(parsed._replace(query=new_query))
                        print(f"[INFO] Jumping to page via URL: {start_url}")
                        driver.get(start_url)
                        time.sleep(3 + random.random() * 2)
                    except Exception as e:
                        print(f"[ERROR] Failed to jump to page via URL: {str(e)}")
        except Exception as e:
            print(f"[WARNING] Error processing START_PAGE: {str(e)}")

        print(f"[INFO] Starting to scrape column articles...")

        last_height = 0
        unchanged_count = 0

        while True:
            # 检查时间限制和数量限制
            if MAX_RUNTIME > 0 and (time.time() - start_time) > MAX_RUNTIME:
                print(f"[TIMEOUT] Runtime exceeded {MAX_RUNTIME} seconds. Exiting...")
                break

            if MAX_ARTICLES > 0 and len(processed_ids) >= MAX_ARTICLES:
                print(f"[LIMIT] Collected {len(processed_ids)} articles (max {MAX_ARTICLES}). Exiting...")
                break

            # === 抓取当前视口内的文章项 ===
            # 专栏文章列表可能有不同的CSS类
            article_items = driver.find_elements(By.CSS_SELECTOR, "div.article-item, div.column-item, article.item, div.list-item")

            # 如果没找到这些类名，尝试通用的文章类名
            if not article_items:
                article_items = driver.find_elements(By.CSS_SELECTOR, ".article, .column-article, .feed-item, div[data-type='article'], div[data-type='column']")

            # 先尝试展开页面上所有被折叠的内容
            expand_all(driver)
            # 重新抓取文章元素以确保展开的内容被包含
            article_items = driver.find_elements(By.CSS_SELECTOR, "div.article-item, div.column-item, article.item, div.list-item")
            if not article_items:
                article_items = driver.find_elements(By.CSS_SELECTOR, ".article, .column-article, .feed-item, div[data-type='article'], div[data-type='column']")

            new_data = []

            for item in article_items:
                # 检查限制条件
                if MAX_RUNTIME > 0 and (time.time() - start_time) > MAX_RUNTIME:
                    break
                if MAX_ARTICLES > 0 and len(processed_ids) >= MAX_ARTICLES:
                    break

                try:
                    # 获取文章ID，尝试多个属性，最后降级为内容哈希
                    article_id = item.get_attribute("data-id") or item.get_attribute("id") or item.get_attribute("data-article-id")
                    if not article_id:
                        # 尝试从链接获取ID
                        try:
                            link_elem = item.find_element(By.TAG_NAME, "a")
                            href = link_elem.get_attribute("href")
                            if href:
                                import re
                                id_match = re.search(r'/(\d+)/?', href.split('/')[-1])
                                if id_match:
                                    article_id = id_match.group(1)
                        except:
                            pass

                    if not article_id:
                        article_id = str(hash(item.text[:200]))

                    if article_id in processed_ids:
                        continue

                    # 获取文章链接
                    article_link = None
                    try:
                        link_elem = item.find_element(By.TAG_NAME, "a")
                        href = link_elem.get_attribute("href")
                        if href and href.startswith('/'):
                            article_link = f"https://xueqiu.com{href}"
                        elif href and href.startswith('http'):
                            article_link = href
                    except:
                        # 尝试其他方式获取链接
                        try:
                            link_elem = item.find_element(By.CSS_SELECTOR, "a[href]")
                            href = link_elem.get_attribute("href")
                            if href and href.startswith('/'):
                                article_link = f"https://xueqiu.com{href}"
                            elif href and href.startswith('http'):
                                article_link = href
                        except:
                            pass

                    if not article_link:
                        print("[WARNING] Article link not found, skipping")
                        continue

                    # 提取标题（如果在列表页就能获取的话）
                    title = ""
                    title_selectors = [
                        ".article-title", ".column-title", ".title", "h3", "h2", "a[title]", ".content-title"
                    ]
                    for sel in title_selectors:
                        try:
                            el = item.find_element(By.CSS_SELECTOR, sel)
                            title = el.text.strip()
                            if title:
                                break
                        except Exception:
                            continue

                    # 解析发表时间（如果在列表页就能获取的话）
                    post_time = ""
                    time_selectors = [".date-and-source", ".time", ".date", ".tweet-time", ".pub-time", ".article-time"]
                    for sel in time_selectors:
                        try:
                            el = item.find_element(By.CSS_SELECTOR, sel)
                            post_time = el.text.strip()
                            if post_time:
                                break
                        except Exception:
                            continue

                    # 提取摘要内容
                    content_text = ""
                    content_selectors = [".summary", ".desc", ".abstract", ".content-brief", ".excerpt", ".content-preview"]
                    for sel in content_selectors:
                        try:
                            el = item.find_element(By.CSS_SELECTOR, sel)
                            content_text = el.text.strip()
                            if content_text:
                                break
                        except Exception:
                            continue

                    if not content_text:
                        # 降级方案：使用 item 的可见文本的一部分
                        content_text = item.text.strip()[:500]

                    # 尝试提取统计数据
                    view_count = like_count = comment_count = 0

                    # 构造基本文章数据
                    article_data = {
                        "article_id": article_id,
                        "title": title,
                        "time": post_time,
                        "content": content_text,
                        "view_count": view_count,
                        "like_count": like_count,
                        "comment_count": comment_count
                    }

                    # 如果能获取到链接，进一步获取详细内容
                    if article_link:
                        print(f"[INFO] Extracting article details: {title if title else 'No title'} (ID: {article_id})")
                        detailed_data = extract_article_content(driver, article_link)
                        if detailed_data:
                            # 更新文章数据，使用详细内容覆盖摘要内容
                            article_data.update({
                                "title": detailed_data["title"] or article_data["title"],
                                "content": detailed_data["content"] or article_data["content"],
                                "time": detailed_data["time"] or article_data["time"],
                                "view_count": detailed_data["view_count"],
                                "like_count": detailed_data["like_count"],
                                "comment_count": detailed_data["comment_count"]
                            })

                    new_data.append(article_data)
                    processed_ids.add(article_id)

                except Exception as e:
                    print(f"[WARNING] Error parsing item: {str(e)}")
                    continue

            # === 保存本轮数据 ===
            if new_data:
                save_to_csv(new_data)
                print(f"[SUCCESS] Saved {len(new_data)} new articles (Total: {len(processed_ids)})")

            # === 更可靠的滚动策略：滚到底并等待新条目加载 ===
            prev_count = len(article_items)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2.0, 4.0))

            # 等待若干次以便新内容加载（检查文章数量是否增长）
            attempts = 0
            while attempts < 6:
                if MAX_RUNTIME > 0 and (time.time() - start_time) > MAX_RUNTIME:
                    print(f"[TIMEOUT] Runtime exceeded {MAX_RUNTIME} seconds. Exiting...")
                    return
                article_items_now = driver.find_elements(By.CSS_SELECTOR, "div.article-item, div.column-item, article.item, div.list-item")
                if not article_items_now:
                    article_items_now = driver.find_elements(By.CSS_SELECTOR, ".article, .column-article, .feed-item, div[data-type='article'], div[data-type='column']")

                if len(article_items_now) > prev_count:
                    break
                time.sleep(1.0 + random.random())
                attempts += 1

            # 判断是否真的到底或无法加载更多
            new_height = driver.execute_script("return document.body.scrollHeight")
            current_scroll = driver.execute_script("return window.pageYOffset + window.innerHeight")

            if new_height == last_height and current_scroll >= new_height:
                # 立即尝试翻页（优先点击"下一页/加载更多"），如失败再累积尝试次数
                print("[INFO] Reached bottom, attempting to paginate...")
                try:
                    next_btn = None
                    xpaths = [
                        "//a[contains(text(),'下一页') or contains(text(),'加载更多') or contains(text(),'更多') or contains(text(),'Next') or contains(text(),'下一页>') ]",
                        "//button[contains(text(),'加载更多') or contains(text(),'更多') or contains(text(),'下一页') or contains(text(),'Next') ]",
                        "//a[@rel='next']",
                        "//a[contains(@class,'next') or contains(@class,'page-next') or contains(@class,'load-more')]",
                        "//li[contains(@class,'next')]//a"
                    ]
                    for xp in xpaths:
                        try:
                            elems = driver.find_elements(By.XPATH, xp)
                        except Exception:
                            elems = []
                        if elems:
                            for e in elems:
                                try:
                                    if e.is_displayed():
                                        next_btn = e
                                        break
                                except Exception:
                                    continue
                        if next_btn:
                            break

                    if next_btn:
                        try:
                            driver.execute_script("arguments[0].scrollIntoView(true);", next_btn)
                            time.sleep(0.5)
                            try:
                                next_btn.click()
                            except Exception:
                                driver.execute_script("arguments[0].click();", next_btn)
                            print("[INFO] Clicked pagination button, waiting to load...")
                            time.sleep(3 + random.random() * 2)
                            # 点击成功，重置计数并继续抓取
                            unchanged_count = 0
                            last_height = driver.execute_script("return document.body.scrollHeight")
                            continue
                        except Exception as e:
                            print(f"[ERROR] Failed to click pagination: {str(e)}")

                    # 未找到或点击失败 -> 尝试通过修改 URL 的 page 参数翻页
                    try:
                        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
                        cur = driver.current_url
                        parsed = urlparse(cur)
                        qs = parse_qs(parsed.query)
                        if 'page' in qs:
                            try:
                                cur_page = int(qs.get('page', ['1'])[0])
                            except Exception:
                                cur_page = 1
                            qs['page'] = [str(cur_page + 1)]
                            new_query = urlencode(qs, doseq=True)
                            new_url = urlunparse(parsed._replace(query=new_query))
                        else:
                            # 简单追加 page=2 或 page=N
                            sep = '&' if parsed.query else '?'
                            new_url = cur + sep + 'page=2'

                        print(f"[INFO] Attempting to go to next page via URL: {new_url}")
                        driver.get(new_url)
                        time.sleep(3 + random.random() * 2)
                        unchanged_count = 0
                        last_height = driver.execute_script("return document.body.scrollHeight")
                        continue
                    except Exception as e:
                        print(f"[ERROR] Failed to paginate via URL: {str(e)}")

                except Exception as e:
                    print(f"[ERROR] Pagination attempt failed: {str(e)}")

                # 如果所有翻页手段都失败，则累积到底重试计数，达到阈值再结束
                unchanged_count += 1
                print(f"[INFO] Appears to have reached bottom? (Attempt #{unchanged_count}/3)")
                if unchanged_count >= 3:
                    print("[INFO] Scraping ended: appears to have reached the bottom or can't continue.")
                    break
            else:
                unchanged_count = 0
                last_height = new_height

    except Exception as e:
        print(f"[ERROR] An exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"[INFO] Task completed, data saved to {CSV_FILENAME}")
        driver.quit()

def input_with_timeout(prompt, timeout=300):
    """带超时的输入函数"""
    print(prompt, end='', flush=True)

    import select
    import sys

    # 对于Windows系统，使用keyboard库或简单实现
    try:
        import msvcrt
        start_time = time.time()
        input_str = ""
        while time.time() - start_time < timeout:
            if msvcrt.kbhit():
                char = msvcrt.getch().decode('utf-8')
                if char == '\r' or char == '\n':  # Enter key
                    break
                elif char == '\x08':  # Backspace key
                    if len(input_str) > 0:
                        input_str = input_str[:-1]
                        print('\b \b', end='', flush=True)
                else:
                    input_str += char
                    print(char, end='', flush=True)
        print()  # New line
        return input_str
    except ImportError:
        # 简化版本：返回空字符串
        print("\n[INFO] Running in simplified mode. Press Enter in the browser window to continue.")
        time.sleep(5)  # 等待用户在浏览器中操作
        return ""

if __name__ == "__main__":
    main()