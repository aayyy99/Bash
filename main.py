import requests
import re
import logging
import os

# 配置基本日志记录到错误日志文件
logging.basicConfig(
    filename='extract_iptv_errors.log',
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 创建一个专门用于详细处理日志的 logger
process_logger = logging.getLogger('process_log')
process_logger.setLevel(logging.INFO)

# 创建一个 FileHandler，用于将日志写入特定文件
process_log_file = 'processing.log'
fh = logging.FileHandler(process_log_file, encoding='utf-8')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)

# 将 FileHandler 添加到 process_logger
process_logger.addHandler(fh)

def clean_channel_name(channel_name):
    """
    先尝试将编码错误的字符串转为 UTF-8，再清理频道名称中的乱码。
    保留中英文、数字、空格、连字符、下划线和 # 符号。
    """
    # 先尝试转码
    try:
        channel_name = channel_name.encode('latin-1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    # 再清理不需要的字符
    cleaned_name = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s\-_#]', '', channel_name)
    return cleaned_name.strip()

def extract_and_deduplicate_iptv(source_file, results_file):
    """
    从 source_file 中的链接提取 IPTV 播放地址和频道名称，去重后写入 results_file。
    支持 .m3u 和 .txt 文件，自动识别每个地址的格式。
    """
    try:
        source_file_path = os.path.join(os.path.dirname(__file__), source_file)
        results_file_path = os.path.join(os.path.dirname(__file__), results_file)
        with open(source_file_path, 'r', encoding='utf-8') as infile:
            source_urls = [line.strip() for line in infile if line.strip()]

        iptv_data = []
        processed_urls = set()
        process_logger.info(f"开始处理源文件：{source_file}")
        print(f"开始处理源文件：{source_file}")

        for source_url in source_urls:
            if not source_url or source_url in processed_urls:
                continue
            processed_urls.add(source_url)
            process_logger.info(f"正在处理链接：{source_url}")
            print(f"正在处理链接：{source_url}")
            try:
                response = requests.get(source_url, timeout=10)
                response.raise_for_status()
                content = response.text
                process_logger.info(f"成功获取链接内容：{source_url}")

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
                            current_channel_name = clean_channel_name(current_channel_name)
                        elif line.startswith('http'):
                            iptv_data.append((current_channel_name, line.strip()))
                            process_logger.info(f"提取到频道：{current_channel_name}, 地址：{line.strip()}")
                            current_channel_name = ""
                    process_logger.info(f"M3U 文件解析完成：{source_url}")

                elif source_url.endswith('.txt'):
                    process_logger.info(f"开始解析 TXT 文件：{source_url}")
                    for line in content.splitlines():
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if ',' in line:
                            channel, url = line.split(',', 1)
                            channel = clean_channel_name(channel)
                            if not channel:
                                channel = "未知频道"
                            iptv_data.append((channel, url.strip()))
                            process_logger.info(f"提取到频道：{channel}, 地址：{url.strip()}")
                        elif line.startswith('http'):
                            iptv_data.append(("未知频道", line))
                            process_logger.info(f"提取到地址：{line}")
                    process_logger.info(f"TXT 文件解析完成：{source_url}")

            except requests.exceptions.RequestException as e:
                logging.error(f"下载 {source_url} 时出错：{e}")
                print(f"下载 {source_url} 时出错：{e}")
            except Exception as e:
                logging.error(f"处理 {source_url} 时发生错误：{e}")
                print(f"处理 {source_url} 时发生错误：{e}")

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
