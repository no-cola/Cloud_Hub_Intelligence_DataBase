import os
import json
import struct
import csv

    # 路径配置
user_dir = "user"
columns_json_path = os.path.join(user_dir, "columns_result.json")
binary_file_path = os.path.join(user_dir, "Binary-Output-P0-0")
    
    # 读取元数据
with open(columns_json_path, "r") as f:
    metadata = json.load(f)
    
    # 解析元数据
table_name = metadata["table_name"]
string_columns = metadata["string_columns"]
rows = int(metadata["rows"])
cols = int(metadata["cols"])
columns = metadata["columns"]
    
    # 读取二进制文件
with open(binary_file_path, "rb") as f:
    raw_data = f.read()
    
    # 数据完整性校验
if len(raw_data) % 8 != 0:
    raise ValueError("二进制文件长度不是8的倍数，数据可能损坏")
    
    # 转换二进制数据

base_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ _"
present_col = 0
data = []
for i in range(0, len(raw_data), 8):
    chunk = raw_data[i:i+8]
    # 使用无符号长整型解析 (Q格式)
    num = struct.unpack('<Q', chunk)[0]  # 小端模式
    data.append(num)
    
    # 验证数据维度
expected_size = rows * cols
if len(data) != expected_size:
    raise ValueError(f"数据量不匹配，预期{expected_size}个值，实际得到{len(data)}个")
    
    # 重组二维数据
structured_data = []
for row in range(rows):
    start = row * cols
    end = start + cols
    structured_data.append(data[start:end])
    
    # 写入CSV
output_filename = f"{table_name}.csv"
with open(os.path.join("user",output_filename), "w", newline='') as f:
    writer = csv.writer(f)
    writer.writerow(columns)  # 写入列头
    writer.writerows(structured_data)  # 写入数据行
    
print(f"转换完成！生成文件：{output_filename}")
print(f"数据维度：{rows}行 x {cols}列")


