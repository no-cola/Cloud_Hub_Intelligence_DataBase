#!/bin/bash

# 定义路径
TEMP_DIR="./Temp"
DB_DIR="./db"
JSON_FILE="$TEMP_DIR/columns.json"

# 检查 JSON 文件是否存在
if [ ! -f "$JSON_FILE" ]; then
  echo "错误: $JSON_FILE 文件不存在"
  exit 1
fi

# 读取 table_name 属性值
TABLE_NAME=$(jq -r '.table_name' "$JSON_FILE")

# 检查 table_name 是否为空
if [ -z "$TABLE_NAME" ]; then
  echo "错误: 无法从 $JSON_FILE 中读取 table_name 属性"
  exit 1
fi

# 在 db 文件夹下创建与 table_name 同名的文件夹
TARGET_DIR="$DB_DIR/$TABLE_NAME"
mkdir -p "$TARGET_DIR"

# 检查文件夹是否创建成功
if [ ! -d "$TARGET_DIR" ]; then
  echo "错误: 无法创建文件夹 $TARGET_DIR"
  exit 1
fi

# 移动 Temp 文件夹下的四个文件到目标文件夹
mv "$TEMP_DIR/Transactions-P0.data" "$TARGET_DIR/"
mv "$TEMP_DIR/Transactions-P1.data" "$TARGET_DIR/"
mv "$TEMP_DIR/Transactions-P2.data" "$TARGET_DIR/"
mv "$TEMP_DIR/columns.json" "$TARGET_DIR/"

# 检查文件是否移动成功
if [ $? -eq 0 ]; then
  echo "文件已成功移动到 $TARGET_DIR"
else
  echo "错误: 文件移动失败"
  exit 1
fi

exit 0
