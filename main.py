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
    """
    try:
        source_file_path = os.path.join(os.path.dirname(__file__), source_file)
        results_file_path = os.path.join(os.path.dirname(__file__), results_file)
        with open(source_file_path, 'r', encoding='utf-8') as infile:
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
                            # 修改后的正则表达式，提取频道名称
                            match = re.search(r',([\s\S]*?)(?:\s*\(|\s*$)', line)
                            if match:
                                channel_name = match.group(1).strip()
                            else:
                                channel_name = "未知频道"
                        elif line.startswith('http'):
                            iptv_data.add((channel_name, line))
                elif url.endswith('.txt'):
                    # 解析 TXT 文件
                    for line in content.splitlines():
                        if line.startswith('http'):
                            iptv_data.add(("", line))

            except requests.exceptions.RequestException as e:
                logging.error(f"下载 {url} 时出错：{e}")
            except Exception as e:
                logging.error(f"处理 {url} 时发生错误：{e}")

        with open(results_file_path, 'w', encoding='utf-8') as outfile:
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
