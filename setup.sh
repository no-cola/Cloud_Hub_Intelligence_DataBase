#!/usr/bin/env bash
# 一键部署脚本：拉取 MP-SPDZ、改名、安装依赖、准备目录、拷贝文件、安装 Python 依赖并运行示例

set -e  # 遇到错误立即退出

# 1. 克隆仓库并重命名
echo "[1/7] 克隆 MP-SPDZ ..."
git clone https://github.com/data61/MP-SPDZ.git
mv MP-SPDZ mpspdz
cd mpspdz

# 2. 安装系统依赖
echo "[2/7] 安装系统依赖 ..."
sudo apt-get update
sudo apt-get install -y \
    automake build-essential clang cmake git \
    libboost-dev libboost-filesystem-dev libboost-iostreams-dev libboost-thread-dev \
    libgmp-dev libntl-dev libsodium-dev libssl-dev libtool python3

# 3. 创建所需文件夹
echo "[3/7] 创建目录结构 ..."
mkdir -p db user user_information

# 4. 将 .mpc 源文件拷贝到 Programs/Source
echo "[4/7] 拷贝 MPC 源文件 ..."
# 请确认这些文件已提前放在脚本同级目录
for f in encode.mpc decode.mpc select_cache.mpc select_query.mpc; do
    if [[ -f "../$f" ]]; then
        cp "../$f" Programs/Source/
    else
        echo "⚠️  文件 $f 不存在，跳过"
    fi
done

# 5. 将其他脚本/配置文件拷贝到 mpspdz 根目录
echo "[5/7] 拷贝其他脚本与配置文件 ..."
for f in clear.py columns.json columns_sum.json convert.py current_query.sql \
         decode.sh decode_prework.py Load.py Move.sh sql_discribe.py; do
    if [[ -f "../$f" ]]; then
        cp "../$f" .
    else
        echo "⚠️  文件 $f 不存在，跳过"
    fi
done

# 6. 安装 Python 依赖
echo "[6/7] 安装 Python 依赖 ..."
pip3 install --user flask mysql-connector-python bcrypt

# 7. 编译并运行示例
echo "[7/7] 编译并运行 tutorial 示例 ..."
./compile.py -R 64 tutorial
Scripts/ring.sh tutorial

echo "✅ 部署完成！"