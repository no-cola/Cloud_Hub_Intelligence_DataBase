#!/bin/bash
set -f  # 禁用通配符扩展（重要！）
# 动态设置用户级定时任务的脚本
# 用法：./set_mission.sh "<时间表达式>" "<命令>"

# ----------------------------------
# 参数检查
# ----------------------------------
if [ $# -ne 2 ]; then
    echo "错误：参数不正确！"
    echo "用法：$0 \"<时间表达式>\" \"<命令>\""
    echo "示例：$0 \"*/5 * * * *\" \"/home/user/check_disk.sh\""
    exit 1
fi

# 从参数中读取时间和命令
CRON_TIME="$1"
CRON_CMD="$2"

# ----------------------------------
# 验证时间格式合法性
# ----------------------------------
validate_cron_time() {
    local time_expression="$1"
    echo "[DEBUG] 输入的时间表达式: '$time_expression'" >&2

    # 安全拆分字段（避免通配符扩展）
    local time_fields
    IFS=' ' read -r -a time_fields <<< "$time_expression"

    echo "[DEBUG] 拆分后的字段: ${time_fields[@]}" >&2
    echo "[DEBUG] 字段数量: ${#time_fields[@]}" >&2

    if [ ${#time_fields[@]} -ne 5 ]; then
        echo "错误：时间表达式必须包含 5 个字段（分 时 日 月 周）"
        return 1
    fi

    local valid_chars='^[*0-9/, -]+$'
    for field in "${time_fields[@]}"; do
        if ! [[ "$field" =~ $valid_chars ]]; then
            echo "错误：非法时间字段 '$field'"
            return 1
        fi
    done
    return 0
}

# 调用验证函数
if ! validate_cron_time "$CRON_TIME"; then
    exit 1
fi

# ----------------------------------
# 构造完整的 cron 任务行
# ----------------------------------
CRON_JOB="$CRON_TIME $CRON_CMD"

# ----------------------------------
# 检查任务是否已存在
# ----------------------------------
check_existing_job() {
    crontab -l 2>/dev/null | grep -qF "$CRON_JOB"
}

if check_existing_job; then
    echo "警告：相同的定时任务已存在，无需重复添加。"
    exit 0
fi

# ----------------------------------
# 添加任务到 crontab
# ----------------------------------
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

# 检查是否成功
if [ $? -eq 0 ]; then
    echo "定时任务添加成功！"
    echo "当前用户的任务列表："
    crontab -l
else
    echo "错误：任务添加失败！"
    exit 1
fi
