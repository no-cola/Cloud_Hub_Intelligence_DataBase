#!/bin/bash
# stream_sql/execute_query.sh

# 进入脚本所在目录
cd "$(dirname "$0")" || exit 1

# 设置全局路径
PROJECT_ROOT="$(cd .. && pwd)"            # 项目根目录
SQL_EXECUTOR="$PROJECT_ROOT/sqlexecutor.py" # 类文件绝对路径
MP_SPDZ_DIR="$PROJECT_ROOT/mpspdz"        # MP-SPDZ目录绝对路径

# 设置Python环境变量
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

# 检查输入参数
if [ $# -eq 0 ]; then
    echo "错误：必须提供SQL查询语句"
    echo "用法：$0 \"SQL_QUERY\""
    exit 1
fi

# 处理含特殊字符的SQL查询
SQL_QUERY="$*"  # 获取所有参数作为完整查询

# 执行Python代码
python3 - <<END
import sys
import os
from sqlexecutor import SQLExecutor
from mpspdz.sql_discribe import Parsed
# 初始化执行器（使用绝对路径）
executor = SQLExecutor(
    mp_spdz_dir=os.path.abspath("$MP_SPDZ_DIR"),
    user_dir="user",
    db_dir="db",
    persis_dir="Persistence"
)
parser = Parsed('''$SQL_QUERY''')
if parser.mtd()=="SELECT":
    try:
        # 执行查询
        success, message = executor.execute('''$SQL_QUERY''')
    
        # 输出结果
        if success:
            print("[成功] " + message)
            result_path = os.path.join("$MP_SPDZ_DIR", "user", "result_table.zip")
            print("结果文件路径:", os.path.abspath(result_path))
            sys.exit(0)
        else:
            print("[错误] " + message, file=sys.stderr)
            sys.exit(2)

    except Exception as e:
        print("[系统错误] " + str(e), file=sys.stderr)
        sys.exit(3)
else:
    print("isn't SELECT")
END

# 处理退出代码
case $? in
    0) exit 0 ;;
    2) exit 2 ;;
    3) exit 3 ;;
    *) exit 99 ;;
esac
