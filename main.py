import requests
import re

def extract_playable_links_from_content(content):
    """从内容中提取播放链接"""
    m3u8_links = re.findall(r'(https?://.*?\.m3u8?)', content)
    other_links = re.findall(r'(https?://.*?\.(mp4|flv|ts))', content)
    return m3u8_links + [link[0] for link in other_links]

def process_link(link):
    """处理单个链接，提取播放链接"""
    try:
        response = requests.get(link, timeout=5)
        response.raise_for_status()
        content = response.text

        if ".m3u" in link or ".txt" in link:
            # 递归处理 M3U 和 TXT 文件
            inner_links = re.findall(r'(https?://.*?(m3u|txt|m3u8|mp4|flv|ts))', content)
            all_inner_links = []
            for inner_link in inner_links:
                all_inner_links.append(inner_link[0])
            inner_playable_links = []
            for inner_link in all_inner_links:
                inner_playable_links.extend(process_link(inner_link))
            return inner_playable_links

        else:
            # 处理其他格式
            return extract_playable_links_from_content(content)

    except requests.exceptions.RequestException as e:
        print(f"无法获取链接内容: {link}, 错误: {e}")
        return []
    except Exception as e:
        print(f"处理链接内容时发生错误: {link}, 错误: {e}")
        return []

def main():
    try:
        with open('source.txt', 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("错误：找不到 source.txt 文件。")
        return

    all_playable_links = []
    for link in links:
        playable_links = process_link(link)
        if playable_links:
            all_playable_links.extend(playable_links)

    with open('results.txt', 'w', encoding='utf-8') as f: #修改了文件名
        for playable_link in all_playable_links:
            f.write(playable_link + '\n')

if __name__ == "__main__":
    main()
