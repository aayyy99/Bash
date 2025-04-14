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
        return extract_playable_links_from_content(response.text)
    except requests.exceptions.RequestException as e:
        print(f"无法获取链接内容: {link}, 错误: {e}")
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

    with open('playable_links.txt', 'w', encoding='utf-8') as f:
        for playable_link in all_playable_links:
            f.write(playable_link + '\n')

if __name__ == "__main__":
    main()
