# 数据爬虫系统

## 项目简介
用于爬取雪球网和微博等社交媒体平台的数据爬虫工具集。

## 技术栈
- Python 3.x
- Selenium - 浏览器自动化
- BeautifulSoup - HTML解析
- Requests - HTTP请求

## 项目结构
```
数据爬虫系统/
├── xueqiu_scraper.py       # 雪球网爬虫
├── weibo_scraper.py        # 微博爬虫
└── data/                   # 爬取数据存储
    ├── xueqiu_posts_8790885129.csv
    ├── temp_xueqiu_posts_8790885129.csv
    └── ~~xueqiu_posts_8790885129.csv
```

## 功能特性

### 雪球网爬虫 (xueqiu_scraper.py)
- ✅ 使用 Selenium 模拟浏览器操作
- ✅ 爬取用户帖子数据
- ✅ 支持滚动加载
- ✅ 导出为 CSV 格式
- ✅ 反爬虫策略应对

### 微博爬虫 (weibo_scraper.py)
- ✅ 使用 BeautifulSoup 解析 HTML
- ✅ 爬取微博内容
- ✅ JSON 数据处理
- ✅ 时间戳转换

## 安装依赖
```bash
pip install selenium beautifulsoup4 requests
```

## 使用说明

### 雪球网爬虫
```python
python xueqiu_scraper.py
```
- 需要配置目标用户ID
- 需要安装Chrome浏览器和ChromeDriver
- 数据保存在 data/ 目录

### 微博爬虫
```python
python weibo_scraper.py
```
- 需要配置微博用户ID或关键词
- 可能需要登录凭证

## 注意事项
⚠️ **重要提醒**:
- 请遵守网站的robots.txt协议
- 控制爬取频率，避免给服务器造成压力
- 不要用于商业用途
- 注意数据隐私保护
- 遵守相关法律法规

## 数据格式
爬取的数据以CSV格式存储，包含以下字段：
- 帖子ID
- 发布时间
- 内容文本
- 点赞数
- 评论数
- 转发数

## 开发维护
- 最后更新: 2026年1月5日
