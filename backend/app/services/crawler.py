import requests
from bs4 import BeautifulSoup

def fetch_latest_cases() -> list:
    """
    从数据源抓取最新案例，返回包含 title, content, source_url 的字典列表。
    """
    # 示例URL，请替换为实际目标URL
    url = "https://www.http://police.qingdao.gov.cn"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        case_list = []

        # 示例选择器，请根据实际网页结构修改
        articles = soup.select('.article-list .item')
        for article in articles:
            title = article.select_one('.title a').get_text(strip=True)
            content = article.select_one('.summary').get_text(strip=True)
            case_url = article.select_one('.title a')['href']
            case_list.append({
                "title": title,
                "content": content,
                "source_url": case_url,
            })
        return case_list
    except requests.RequestException as e:
        print(f"爬取失败: {e}")
        return []