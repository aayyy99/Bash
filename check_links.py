import requests
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
        with open('source.txt', 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("错误：找不到 source.txt 文件。")
        return

    results = []
    for link in links:
        success, data = check_link(link)
        channel_name = extract_channel_name(link)
        results.append(f"链接: {link}, 频道名称: {channel_name}, 状态: {'成功' if success else '失败'}")

    with open('results.txt', 'w', encoding='utf-8') as f: #修改了文件名和写入方式。
        for result in results:
            f.write(result + '\n')

if __name__ == "__main__":
    main()
