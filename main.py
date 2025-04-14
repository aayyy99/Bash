import requests
import re

def extract_playable_links_and_names(content):
    """从内容中提取播放链接和频道名称"""
    results = []
    # 提取 M3U8 播放链接和频道名称
    m3u8_matches = re.findall(r'#EXTINF:-1,(.*?)\n(https?://.*?\.m3u8?)', content)
    for name, link in m3u8_matches:
        results.append((link, name.strip()))
    # 提取其他常见播放链接和频道名称 (假设频道名称在链接前一行)
    other_matches = re.findall(r'(.*?)\n(https?://.*?\.(mp4|flv|ts))', content)
    for name, link, _ in other_matches:
        results.append((link, name.strip()))
    return results

def process_link(link):
    """处理单个链接，提取播放链接和频道名称"""
    try:
        response = requests.get(link, timeout=5)
        response.raise_for_status()
        content = response.text

        if ".m3u" in link or ".txt" in link:
            # 递归处理 M3U 和 TXT 文件
            inner_links = re.findall(r'(https?://.*?(m3u|txt|m3u8|mp4|flv|ts))', content)
            all_inner_results = []
            for inner_link in inner_links:
                all_inner_results.extend(process_link(inner_link[0]))
            return all_inner_results

        else:
            # 处理其他格式
            return extract_playable_links_and_names(content)

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

    all_results = []
    for link in links:
        results = process_link(link)
        if results:
            all_results.extend(results)

    unique_results = list(set(all_results)) # 去重

    with open('results.txt', 'w', encoding='utf-8') as f:
        for link, name in unique_results:
            f.write(f"频道名称: {name}, 播放链接: {link}\n")

if __name__ == "__main__":
    main()
