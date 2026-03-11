# 雪球专栏文章爬虫工具

这是一个用于批量提取雪球专栏文章标题和URL的Python工具，支持多页自动翻页。

## 功能特点

- 自动处理雪球登录验证
- 支持多页自动翻页（最多指定页数）
- 提取文章标题、URL、摘要和文章ID
- 智能翻页：优先点击页面底部的“下一页”按钮，失败时回退到URL参数翻页
- 增量保存数据到CSV文件
- 防检测机制，降低被封风险

## 安装依赖

```bash
pip install selenium webdriver-manager
```

## 使用方法

### 基础使用

直接运行脚本，默认抓取专栏 `https://xueqiu.com/8790885129/column` 的前13页内容：

```bash
python xueqiu_column_skill.py
```

### 自定义参数

通过调用 `scrape_xueqiu_column` 函数来自定义参数：

```python
from xueqiu_column_skill import scrape_xueqiu_column

# 自定义参数
scrape_xueqiu_column(
    base_url='https://xueqiu.com/用户ID/column',  # 专栏地址
    csv_filename='custom_output.csv',             # 输出文件名
    total_pages=10,                               # 抓取总页数
    start_page=1                                  # 起始页码
)
```

## 参数说明

- `base_url`: 专栏主页URL
- `csv_filename`: 输出CSV文件路径
- `total_pages`: 要抓取的总页数
- `start_page`: 开始抓取的页码（默认为1）

## 输出格式

CSV文件包含以下列：

- `article_id`: 文章ID
- `title`: 文章标题
- `url`: 文章URL
- `summary`: 文章摘要
- `page_num`: 页码

## 注意事项

1. 首次运行时需要手动登录雪球账号（提供45秒等待时间）
2. 请遵守雪球的使用条款，不要过度频繁请求
3. 工具会在每页之间添加适当的延迟，以模拟人工操作
4. 如遇反爬机制，请适当调整等待时间

## 常见问题

Q: 运行时没有反应怎么办？
A: 确保已经安装Chrome浏览器，并且允许脚本打开浏览器窗口进行登录。

Q: 只抓取到第一页的内容？
A: 脚本会尝试点击页面底部的"下一页"按钮进行翻页，如果页面布局发生变化，可能需要调整选择器。