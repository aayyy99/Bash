import requests
import re
import logging
import os

# 配置日志记录
logging.basicConfig(filename='extract_iptv_errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def extract_and_deduplicate_iptv(source_file, results_file):
    """
    从 source_file 中的链接提取 IPTV 播放地址和频道名称，去重后写入 results_file。
    改进了频道名称提取，增加了对 M3U 文件头的处理，并提供了基于播放地址的去重选项。
    """
    try:
        source_file_path = os.path.join(os.path.dirname(__file__), source_file)
        results_file_path = os.path.join(os.path.dirname(__file__), results_file)
        with open(source_file_path, 'r', encoding='utf-8') as infile:
            urls = [line.strip() for line in infile]

        iptv_data = []  # 使用列表存储所有条目
        processed_urls = set() # 用于记录已处理的源 URL

        for source_url in urls:
            if not source_url or source_url in processed_urls:
                continue
            processed_urls.add(source_url)
            try:
                response = requests.get(source_url, timeout=10)  # 增加超时时间
                response.raise_for_status()  # 检查 HTTP 请求是否成功
                content = response.text

                if source_url.endswith('.m3u'):
                    # 解析 M3U 文件
                    for line in content.splitlines():
                        if line.startswith('#EXTM3U'):
                            continue  # 跳过 M3U 文件头
                        elif line.startswith('#EXTINF:'):
                            # 更鲁棒的正则表达式，允许频道名称中包含括号等字符
                            match = re.search(r',([\s\S]*)$', line)
                            channel_name = match.group(1).strip() if match else "未知频道"
                        elif line.startswith('http'):
                            iptv_data.append((channel_name, line.strip()))
                            channel_name = "" # 重置频道名称
                elif source_url.endswith('.txt'):
                    # 解析 TXT 文件
                    for line in content.splitlines():
                        if line.startswith('http'):
                            iptv_data.append(("", line.strip()))

            except requests.exceptions.RequestException as e:
                logging.error(f"下载 {source_url} 时出错：{e}")
            except Exception as e:
                logging.error(f"处理 {source_url} 时发生错误：{e}")

        # 基于播放地址去重
        unique_iptv_data = {}
        for channel, url in iptv_data:
            if url not in unique_iptv_data:
                unique_iptv_data[url] = channel
            elif not unique_iptv_data[url]:
                unique_iptv_data[url] = channel # 如果之前没有频道名称，则记录

        with open(results_file_path, 'w', encoding='utf-8') as outfile:
            for url, channel in unique_iptv_data.items():
                outfile.write(f"{channel},{url}\n")

        print(f"IPTV 播放地址和频道名称已提取并去重（基于播放地址），结果保存在 {results_file} 中。")

    except FileNotFoundError:
        print(f"错误：文件 {source_file} 未找到。")
    except Exception as e:
        print(f"发生错误：{e}")

# 调用函数进行处理
source_file = 'source.txt'
results_file = 'results.txt'
extract_and_deduplicate_iptv(source_file, results_file)
