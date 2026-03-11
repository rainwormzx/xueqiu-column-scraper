# -*- coding: utf-8 -*-
"""
雪球专栏文章标题和URL提取器 - 可配置技能版本
"""
import time
import csv
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def init_driver():
    """初始化浏览器驱动"""
    try:
        chrome_options = Options()
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36')

        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        driver = webdriver.Chrome(options=chrome_options)

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
        print(f"[WARNING] Auto-managed driver failed: {str(e)}")
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)

            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                    Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                    })
                """
            })
            print("[SUCCESS] Driver manager initialized successfully")
            return driver
        except Exception as e3:
            print(f"[ERROR] All driver initialization methods failed: {str(e3)}")
            return None


def save_to_csv(data_list, csv_filename):
    """增量保存数据到CSV"""
    file_exists = os.path.isfile(csv_filename)
    with open(csv_filename, mode='a', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=["article_id", "title", "url", "summary", "page_num"])
        if not file_exists:
            writer.writeheader()
        writer.writerows(data_list)


def extract_articles_from_page(driver, page_num):
    """从当前页面提取文章"""
    # 等待页面加载
    time.sleep(3)

    # 滚动页面以加载更多内容
    for i in range(2):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    # 再次滚动到底部
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    # 查找专栏文章
    article_items = driver.find_elements(By.CSS_SELECTOR, "div.column__item")

    print(f"[INFO] Found {len(article_items)} articles on page {page_num}")

    articles_data = []
    processed_urls = set()  # 避免重复

    for item in article_items:
        try:
            # 查找文章链接
            link_elem = None
            try:
                link_elem = item.find_element(By.CSS_SELECTOR, "a[href*='/8790885129/']")
            except:
                try:
                    link_elem = item.find_element(By.TAG_NAME, "a")
                    href = link_elem.get_attribute("href")
                    if '/8790885129/' not in href:
                        continue
                except:
                    continue

            if link_elem:
                article_link = link_elem.get_attribute("href")

                # 避免处理重复的链接
                if article_link in processed_urls:
                    continue
                processed_urls.add(article_link)

                # 从URL中提取文章ID
                id_match = re.search(r'/8790885129/(\d+)', article_link)
                if id_match:
                    article_id = id_match.group(1)
                else:
                    article_id = str(abs(hash(article_link)) % 100000000)

                # 获取标题
                title = link_elem.text.strip()
                if not title:
                    try:
                        title_elem = item.find_element(By.CSS_SELECTOR, "div:first-child, h1, h2, h3")
                        title = title_elem.text.strip()
                    except:
                        title = f"Article {article_id}"

                # 获取摘要
                summary = ""
                try:
                    desc_elem = item.find_element(By.CSS_SELECTOR, ".column__item__desc, .content, .text")
                    summary = desc_elem.text.strip()[:300]
                except:
                    summary = title[:300]

                if not title.strip():
                    title = f"Article {article_id}"

                article_data = {
                    "article_id": article_id,
                    "title": title.replace(',', '，'),
                    "url": article_link,
                    "summary": summary.replace(',', '，'),
                    "page_num": page_num
                }

                articles_data.append(article_data)
                print(f"[FOUND] {title[:50]}..." if len(title) > 50 else f"[FOUND] {title}")

        except Exception as e:
            print(f"[ERROR] Error processing article: {str(e)}")
            continue

    return articles_data


def click_next_page_button(driver):
    """点击下一页按钮"""
    try:
        # 尝试多种可能的下一页按钮选择器
        next_button_selectors = [
            "//a[contains(text(), '下一页') or contains(text(), 'Next') or contains(@aria-label, 'next')]",
            "//button[contains(text(), '下一页') or contains(text(), 'Next')]",
            "//a[@class='next' or contains(@class, 'next') or contains(@class, 'page-next')]",
            "//li[contains(@class, 'next')]//a",
            "//a[contains(@class, 'Pagination-next')]"
        ]

        for selector in next_button_selectors:
            try:
                next_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if next_button.is_displayed() and next_button.is_enabled():
                    print(f"[NAVIGATION] Found next page button, attempting click...")

                    # 滚动到按钮位置
                    driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                    time.sleep(1)

                    # 尝试点击
                    try:
                        next_button.click()
                        print("[NAVIGATION] Successfully clicked next page button")
                        return True
                    except:
                        # 如果直接点击失败，尝试JS点击
                        driver.execute_script("arguments[0].click();", next_button)
                        print("[NAVIGATION] Successfully clicked next page button (via JS)")
                        return True
            except:
                continue

        print("[NAVIGATION] Could not find next page button with any selector")
        return False
    except Exception as e:
        print(f"[NAVIGATION] Error clicking next page button: {str(e)}")
        return False


def scrape_xueqiu_column(base_url, csv_filename, total_pages=13, start_page=1):
    """
    抓取雪球专栏文章的主函数

    Args:
        base_url (str): 专栏主页URL
        csv_filename (str): 输出CSV文件名
        total_pages (int): 总页数
        start_page (int): 起始页码
    """
    driver = init_driver()
    if driver is None:
        print("[ERROR] Could not initialize driver, exiting.")
        return

    total_articles = 0

    try:
        # 登录步骤
        print("[INFO] Opening Xueqiu homepage for login...")
        driver.get("https://xueqiu.com")
        print("[INFO] Please manually login to Xueqiu in the opened browser...")
        print("[INFO] Waiting 45 seconds for login...")

        # 给用户时间登录
        time.sleep(45)

        print(f"[INFO] Starting to extract articles from {total_pages} pages...")
        print(f"[INFO] Will save data to: {csv_filename}")

        # 访问初始页面
        driver.get(base_url)
        current_page = start_page
        processed_pages = 0

        while processed_pages < total_pages:
            print(f"\n{'='*60}")
            print(f"[PROCESSING] PAGE {current_page} (Round {processed_pages+1}/{total_pages})")
            print(f"{'='*60}")

            # 从当前页面提取文章
            page_articles = extract_articles_from_page(driver, current_page)

            if page_articles:
                save_to_csv(page_articles, csv_filename)
                total_articles += len(page_articles)
                print(f"[SAVED] {len(page_articles)} articles from page {current_page} (Total: {total_articles})")
            else:
                print(f"[WARNING] No articles found on page {current_page}")

            processed_pages += 1

            # 如果还没达到目标页数，尝试点击下一页
            if processed_pages < total_pages:
                print(f"[NAVIGATION] Attempting to go to next page...")

                # 尝试点击下一页按钮
                next_page_success = click_next_page_button(driver)

                if next_page_success:
                    # 等待页面加载
                    time.sleep(5)
                    current_page += 1
                    print(f"[SUCCESS] Moved to page {current_page}")
                else:
                    # 如果点击按钮失败，尝试使用URL参数翻页
                    print(f"[FALLBACK] Trying URL-based navigation to page {current_page + 1}")
                    next_url = f"{base_url}?page={current_page + 1}"
                    driver.get(next_url)
                    time.sleep(5)
                    current_page += 1
            else:
                print("[COMPLETED] Reached target number of pages")

        print(f"\n[SUCCESS] COMPLETED: Processed {processed_pages} pages!")
        print(f"[STATS] Total articles extracted: {total_articles}")

    except KeyboardInterrupt:
        print("[INTERRUPT] User interrupted. Stopping gracefully...")
    except Exception as e:
        print(f"[ERROR] An exception occurred: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        print(f"\n[SUMMARY]:")
        print(f"Pages processed: {processed_pages}")
        print(f"Articles extracted: {total_articles}")
        print(f"Data saved to: {csv_filename}")
        print("[CLOSING] Browser...")
        driver.quit()
        print("[DONE] Task completed!")


def main():
    """默认执行函数，使用预设参数"""
    # 默认设置
    BASE_URL = 'https://xueqiu.com/8790885129/column'  # 专栏主页
    CSV_FILENAME = 'xueqiu_column_with_pagination.csv'
    TOTAL_PAGES = 13

    scrape_xueqiu_column(BASE_URL, CSV_FILENAME, TOTAL_PAGES)


if __name__ == "__main__":
    main()