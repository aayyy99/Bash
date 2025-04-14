import requests
import pandas as pd
import re

def check_link(link):
    try:
        response = requests.get(link, timeout=5)
        response.raise_for_status()  # 检查 HTTP 错误
        return True, response.text
    except requests.exceptions.RequestException as e:
        return False, str(e)

def extract_channel_name(link):
    try:
      #此正则表达式会匹配常见的直播源格式中的频道名称。
      match = re.search(r'#(EXTINF:-1,)?(.*)', link)
      if match:
          return match.group(2).strip()
    except Exception as e:
      print(f"提取频道名称时发生错误: {e}")
    return "未知频道"

def main():
    try:
        with open('links.txt', 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("错误：找不到 links.txt 文件。")
        return

    results = []
    for link in links:
        success, data = check_link(link)
        channel_name = extract_channel_name(link)
        results.append({'链接': link, '频道名称': channel_name,'状态': '成功' if success else '失败', '数据': data if success else ''})
        print(f"链接：{link}， 状态：{'成功' if success else '失败'}")

    df = pd.DataFrame(results)
    successful_links = df[df['状态'] == '成功']
    successful_links.to_csv('results.csv', index=False, encoding='utf-8-sig')

if __name__ == "__main__":
    main()
