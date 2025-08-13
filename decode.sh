#!/bin/bash

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR" || { echo "无法进入工作目录"; exit 1; }

chmod +x "$BASE_DIR/compile.py" "$BASE_DIR/Scripts/ring.sh" 2>/dev/null

cd "$BASE_DIR/user" || { echo "无法进入user目录"; exit 1; }
if [ -f "result_table.zip" ]; then
    unzip -o "result_table.zip" >/dev/null || { echo "解压失败"; exit 1; }
elif [ -f "result_table.tar.gz" ]; then
    tar -xzvf "result_table.tar.gz" >/dev/null || { echo "解压失败"; exit 1; }
else
    echo "未找到压缩包"
    exit 1
fi

cd "$BASE_DIR" || { echo "无法返回工作目录"; exit 1; }
[ -d "$BASE_DIR/Persistence" ] || mkdir -p "$BASE_DIR/Persistence"
rm -rf "$BASE_DIR/Persistence"/* 2>/dev/null

mv "$BASE_DIR/user/Transactions-P0.data" "$BASE_DIR/Persistence/" || { echo "移动P0失败"; exit 1; }
mv "$BASE_DIR/user/Transactions-P1.data" "$BASE_DIR/Persistence/" || { echo "移动P1失败"; exit 1; }
mv "$BASE_DIR/user/Transactions-P2.data" "$BASE_DIR/Persistence/" || { echo "移动P2失败"; exit 1; }

"$BASE_DIR/compile.py" -R 64 decode || { echo "编译失败"; exit 1; }
"$BASE_DIR/Scripts/ring.sh" decode || { echo "ring执行失败"; exit 1; }

if [ -f "$BASE_DIR/Player-Data/Binary-Output-P0-0" ]; then
    mv "$BASE_DIR/Player-Data/Binary-Output-P0-0" "$BASE_DIR/user/" || { echo "移动输出失败"; exit 1; }
fi

python3 "$BASE_DIR/convert.py" || { echo "转换失败"; exit 1; }

echo "所有操作完成"
