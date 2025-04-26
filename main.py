import requests
import re
import logging
import os

# 配置基本日志记录到错误日志文件
logging.basicConfig(filename='extract_iptv_errors.log', level=logging.ERROR,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# 创建一个专门用于详细处理日志的 logger
process_logger = logging.getLogger('process_log')
process_logger.setLevel(logging.INFO)  # 设置日志级别为 INFO，以便记录更多信息

# 创建一个 FileHandler，用于将日志写入特定文件
process_log_file = 'processing.log'
fh = logging.FileHandler(process_log_file, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# 将 FileHandler 添加到 process_logger
process_logger.addHandler(fh)

def extract_and_deduplicate_iptv(source_file, results_file):
    """
    从 source_file 中的链接提取 IPTV 播放地址和频道名称，去重后写入 results_file。
    进一步优化频道名称提取，优先处理 tvg-name 属性。
    将详细的处理过程日志输出到 processing.log 文件。
    错误日志仍然输出到 extract_iptv_errors.log 文件和控制台。
    """
    try:
        source_file_path = os.path.join(os.path.dirname(__file__), source_file)
        results_file_path = os.path.join(os.path.dirname(__file__), results_file)
        with open(source_file_path, 'r', encoding='utf-8') as infile:
            source_urls = [line.strip() for line in infile]

        iptv_data = []  # 使用列表存储所有条目
        processed_urls = set() # 用于记录已处理的源 URL
        process_logger.info(f"开始处理源文件：{source_file}")
        print(f"开始处理源文件：{source_file}")

        for source_url in source_urls:
            if not source_url or source_url in processed_urls:
                continue
            processed_urls.add(source_url)
            process_logger.info(f"正在处理链接：{source_url}")
            print(f"正在处理链接：{source_url}")
            try:
                response = requests.get(source_url, timeout=10)  # 增加超时时间
                response.raise_for_status()  # 检查 HTTP 请求是否成功
                content = response.text
                process_logger.info(f"成功获取链接内容：{source_url}")
                # 成功获取内容时不输出到控制台

                if source_url.endswith('.m3u'):
                    process_logger.info(f"开始解析 M3U 文件：{source_url}")
                    current_channel_name = ""
                    for line in content.splitlines():
                        if line.startswith('#EXTM3U'):
                            continue
                        elif line.startswith('#EXTINF:'):
                            channel_name_match = re.search(r'tvg-name="([^"]*)"', line)
                            if channel_name_match:
                                current_channel_name = channel_name_match.group(1).strip()
                            else:
                                name_match = re.search(r',([\s\S]*?)(?:\s*\(|\s*$)', line)
                                current_channel_name = name_match.group(1).strip() if name_match else "未知频道"
                        elif line.startswith('http'):
                            iptv_data.append((current_channel_name, line.strip()))
                            process_logger.info(f"提取到频道：{current_channel_name}, 地址：{line.strip()}")
                            current_channel_name = ""
                    process_logger.info(f"M3U 文件解析完成：{source_url}")
                elif source_url.endswith('.txt'):
                    process_logger.info(f"开始解析 TXT 文件：{source_url}")
                    for line in content.splitlines():
                        if line.startswith('http'):
                            iptv_data.append(("", line.strip()))
                            process_logger.info(f"提取到地址：{line.strip()}")
                    process_logger.info(f"TXT 文件解析完成：{source_url}")

            except requests.exceptions.RequestException as e:
                logging.error(f"下载 {source_url} 时出错：{e}")
                print(f"下载 {source_url} 时出错：{e}") # 获取失败时输出到控制台
            except Exception as e:
                logging.error(f"处理 {source_url} 时发生错误：{e}")
                print(f"处理 {source_url} 时发生错误：{e}") # 其他处理错误也输出到控制台

        # 基于播放地址去重
        unique_iptv_data = {}
        process_logger.info("开始去重处理...")
        print("开始去重处理...")
        for channel, url in iptv_data:
            if url not in unique_iptv_data:
                unique_iptv_data[url] = channel
                process_logger.info(f"新增唯一地址：{url}, 频道：{channel}")
            elif not unique_iptv_data[url] and channel:
                unique_iptv_data[url] = channel
                process_logger.info(f"更新地址 {url} 的频道名称为：{channel}")

        process_logger.info(f"去重处理完成，共保留 {len(unique_iptv_data)} 条记录。")
        print(f"去重处理完成，共保留 {len(unique_iptv_data)} 条记录。")

        with open(results_file_path, 'w', encoding='utf-8') as outfile:
            process_logger.info(f"开始写入结果到文件：{results_file}")
            print(f"开始写入结果到文件：{results_file}")
            for url, channel in unique_iptv_data.items():
                outfile.write(f"{channel},{url}\n")
            process_logger.info(f"结果已成功写入到文件：{results_file}")
            print(f"结果已成功写入到文件：{results_file}")

        print(f"IPTV 播放地址和频道名称已提取并去重（基于播放地址），结果保存在 {results_file} 中。")

    except FileNotFoundError:
        print(f"错误：文件 {source_file} 未找到。")
    except Exception as e:
        print(f"发生错误：{e}")

# 调用函数进行处理
source_file = 'source.txt'
results_file = 'results.txt'
extract_and_deduplicate_iptv(source_file, results_file)
