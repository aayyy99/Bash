import requests
import re

def extract_and_deduplicate_iptv(source_file, results_file):
    """
    从 source_file 中的链接提取 IPTV 播放地址和频道名称，去重后写入 results_file。
    """
    try:
        with open(source_file, 'r', encoding='utf-8') as infile:
            urls = [line.strip() for line in infile]

        iptv_data = set()  # 使用集合进行去重

        for url in urls:
            try:
                response = requests.get(url)
                response.raise_for_status()  # 检查 HTTP 请求是否成功
                content = response.text

                if url.endswith('.m3u'):
                    # 解析 M3U 文件
                    for line in content.splitlines():
                        if line.startswith('#EXTINF:'):
                            channel_name = re.search(r',(.+)', line).group(1)
                        elif line.startswith('http'):
                            iptv_data.add((channel_name, line))
                elif url.endswith('.txt'):
                    # 解析 TXT 文件
                    for line in content.splitlines():
                        if line.startswith('http'):
                            iptv_data.add(("", line))

            except requests.exceptions.RequestException as e:
                print(f"下载 {url} 时出错：{e}")
            except Exception as e:
                print(f"处理 {url} 时发生错误：{e}")

        with open(results_file, 'w', encoding='utf-8') as outfile:
            for channel_name, url in iptv_data:
                outfile.write(f"{channel_name},{url}\n")

        print(f"IPTV 播放地址和频道名称已提取并去重，结果保存在 {results_file} 中。")

    except FileNotFoundError:
        print(f"错误：文件 {source_file} 未找到。")
    except Exception as e:
        print(f"发生错误：{e}")

# 调用函数进行处理
source_file = 'source.txt'
results_file = 'results.txt'
extract_and_deduplicate_iptv(source_file, results_file)
