from flask import Flask, render_template, request, jsonify, send_file, session
from table_manager import TableManager
from sqlexecutor import SQLExecutor
import os
import subprocess
import shutil
import json
import time
import zipfile
import re
import mysql.connector
import bcrypt
from functools import wraps
import uuid  # 导入 uuid 模块
import threading
import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import hashlib
import stat
import shlex
from mpspdz.sql_discribe import Parsed

app = Flask(__name__, static_folder='static', static_url_path='')
app.secret_key = 'a7c231f0a4eb41d6b9c435c838f1e68b'

# MySQL 数据库配置 - 其他人只需修改这里
DB_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': 'nocola',  # 修改为你的 MySQL 密码
    'port': 3306  # 修改为你的 MySQL 端口
}

# 数据库名称
DB_NAME = 'mpc_system'


# 初始化数据库
def init_db():
    try:
        # 创建数据库连接
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            use_pure=True,
            ssl_disabled=True  # 禁用 SSL
        )
        cursor = conn.cursor()

        # 创建数据库（如果不存在）
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
        cursor.execute(f"USE {DB_NAME}")

        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建流式查询表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stream_queries (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL,
                email VARCHAR(100) NOT NULL,
                query_text TEXT NOT NULL,
                time_settings VARCHAR(50) NOT NULL,
                script_name VARCHAR(100) DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化错误: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()


# 获取数据库连接
def get_db_connection():
    return mysql.connector.connect(
        host=DB_CONFIG['host'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password'],
        port=DB_CONFIG['port'],
        database=DB_NAME,
        use_pure=True,
        ssl_disabled=True  # 禁用 SSL
    )


# 登录验证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'message': '请先登录', 'redirect': True})
        return f(*args, **kwargs)

    return decorated_function


def generate_shell_script(sql_query, user_email):
    """
    为定时SQL查询生成shell脚本文件
    
    参数:
    - sql_query: SQL查询语句
    - user_email: 接收结果的邮箱地址
    
    返回:
    - script_path: 生成的脚本路径
    - script_name: 脚本名称
    """
    # 生成唯一的脚本名称
    timestamp = int(time.time() * 1000)
    script_id = str(uuid.uuid4())[:8]  # 使用UUID的前8位作为ID
    script_name = f"query_{timestamp}_{script_id}.sh"
    
    # 脚本目录和路径
    script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stream_sql")
    os.makedirs(script_dir, exist_ok=True)  # 确保目录存在
    script_path = os.path.join(script_dir, script_name)
    
    # 脚本内容
    script_content = f"""#!/bin/bash
# 自动生成的查询脚本 - {timestamp}

# ------ 配置参数 ------
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EXECUTE_SCRIPT="${{BASE_DIR}}/stream_sql/execute_query.sh"
RESULT_FILE="${{BASE_DIR}}/mpspdz/user/result_table.zip"
USER_EMAIL="{user_email}"
rm -rf "${{BASE_DIR}}/mpspdz/user/*"
# ------ 执行查询 ------
echo "开始执行查询: {sql_query}"
"$EXECUTE_SCRIPT" "{sql_query}"

# ------ 验证结果 ------
if [ -f "$RESULT_FILE" ]; then
    # ------ 发送邮件 ------
    echo "正在使用 Python 脚本发送结果到 $USER_EMAIL"
    
    # 调用 Python 脚本发送邮件
    python3 "${{BASE_DIR}}/stream_sql/send_email.py" \\
        "$USER_EMAIL" \\
        "SQL查询结果 - $(date '+%Y%m%d_%H%M%S')" \\
        "查询语句: {sql_query}

查询已完成，结果见附件。" \\
        "$RESULT_FILE"
    
    mail_status=$?
    
    if [ $mail_status -eq 0 ]; then
        echo "邮件发送成功"
    else
        echo "邮件发送失败，错误代码: $mail_status"
        exit 2
    fi
else
    echo "查询结果文件不存在: $RESULT_FILE"
    exit 1
fi

exit 0
"""
    
    # 写入文件并设置权限
    with open(script_path, "w") as f:
        f.write(script_content)
    
    # 添加执行权限
    st = os.stat(script_path)
    os.chmod(script_path, st.st_mode | stat.S_IEXEC)

    return script_path, script_name



# 配置路径
MP_SPDZ_DIR = "./mpspdz"  # MP-SPDZ安装目录
BASE_DIR = os.path.abspath(os.path.dirname(__file__))  # 定义 BASE_DIR
# TEMP_DIR 现在作为临时上传的根目录
TEMP_UPLOAD_DIR = os.path.join(BASE_DIR, "temp_uploads")  # 现在可以使用 BASE_DIR
USER_DIR = os.path.join(MP_SPDZ_DIR, "user")
DB_DIR = os.path.join(MP_SPDZ_DIR, "db")
Persis_DIR = os.path.join(MP_SPDZ_DIR, "Persistence")
USER_INFO_DIR = os.path.join(MP_SPDZ_DIR, "user_information") # 新增用户JSON信息目录
# BASE_DIR = os.path.abspath(os.path.dirname(__file__)) # 从这里移除

# 创建必要的目录
os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)  # 创建临时上传根目录
os.makedirs(USER_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)
os.makedirs(Persis_DIR, exist_ok=True)


# 修改 move_files 函数以处理来自特定临时目录的文件
def move_files(temp_dir_path):
    """
    将指定临时目录中的文件移动到数据库目录。

    参数:
    - temp_dir_path: 包含上传文件的临时目录路径

    返回:
    - (成功与否, 消息)的元组
    """
    try:
        columns_json_path = os.path.join(temp_dir_path, "columns.json")
        if not os.path.exists(columns_json_path):
            return False, "未找到 columns.json 文件"

        # 读取表名 (此时 columns.json 已包含权限信息)
        with open(columns_json_path, 'r') as f:
            data = json.load(f)
            table_name = data.get('table_name')

        if not table_name:
            return False, "无法从 columns.json 中获取表名"

        # 检查表是否已存在
        table_dir = os.path.join(DB_DIR, table_name)
        if (os.path.exists(table_dir)):
            # 清理临时目录
            shutil.rmtree(temp_dir_path)
            return False, f"表 {table_name} 已存在"

        # 创建表目录
        os.makedirs(table_dir, exist_ok=True)

        # 移动文件
        files_to_move = ['Transactions-P0.data', 'Transactions-P1.data', 'Transactions-P2.data', 'columns.json']
        all_files_exist = True
        for file_name in files_to_move:
            src = os.path.join(temp_dir_path, file_name)
            if not os.path.exists(src):
                all_files_exist = False
                print(f"警告: 文件 {src} 在临时目录中不存在")
                # 根据需要决定是否中断，这里选择继续尝试移动其他文件
                continue  # 跳过不存在的文件
            dst = os.path.join(table_dir, file_name)
            shutil.move(src, dst)

        # 清理临时目录
        shutil.rmtree(temp_dir_path)

        if not all_files_exist:
            # 即使部分文件不存在也可能需要报告成功，取决于业务逻辑
            # 这里假设只要 columns.json 和至少一个 data 文件移动了就算部分成功
            print(f"警告: 表 {table_name} 的部分文件未能移动，因为它们在临时目录中不存在。")
            # 仍返回成功，但可能需要在日志中记录更详细的信息

        return True, f"表 {table_name} 已成功创建并保存"
    except Exception as e:
        # 尝试清理临时目录，即使出错
        if os.path.exists(temp_dir_path):
            try:
                shutil.rmtree(temp_dir_path)
            except Exception as cleanup_e:
                print(f"清理临时目录 {temp_dir_path} 时出错: {cleanup_e}")
        return False, f"处理过程中出错: {str(e)}"


# 工具：移除 crontab 中某一行
def remove_cron_job(cron_cmd):
    """
    从当前用户的 crontab 中删除包含 cron_cmd 的那一行
    """
    try:
        current_crontab = subprocess.check_output(['crontab', '-l'], text=True)
    except subprocess.CalledProcessError:
        # 用户没有 crontab，直接返回
        return True

    lines = current_crontab.splitlines()
    new_lines = [ln for ln in lines if cron_cmd not in ln]

    if len(new_lines) == len(lines):
        return False  # 没找到，说明已经删了或不存在

    # 写入新的 crontab
    proc = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
    proc.communicate(input='\n'.join(new_lines) + '\n')
    return proc.returncode == 0



@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/delete_stream_task/<int:task_id>', methods=['DELETE'])
@login_required
def delete_stream_task(task_id):
    """
    删除一条流式查询：DB 记录 + crontab 任务 + 脚本文件
    """
    username = session.get('username')
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 1. 查询任务信息
    cursor.execute(
        "SELECT id, script_name, time_settings FROM stream_queries WHERE id = %s AND username = %s",
        (task_id, username)
    )
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        return jsonify({'success': False, 'message': '任务不存在或无权限'})

    script_name = row['script_name']
    time_settings = row['time_settings']

    # 2. 删除 DB 记录
    cursor.execute("DELETE FROM stream_queries WHERE id = %s", (task_id,))
    conn.commit()

    # 3. 计算脚本绝对路径
    script_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stream_sql")
    script_path = os.path.join(script_dir, script_name)

    # 4. 从 crontab 移除对应任务行
    cron_cmd = script_path
    cron_removed = remove_cron_job(cron_cmd)

    # 5. 删除脚本文件
    file_removed = False
    if os.path.isfile(script_path):
        os.remove(script_path)
        file_removed = True

    cursor.close()
    conn.close()

    return jsonify({
        'success': True,
        'message': f'任务已删除 (crontab: {"已清理" if cron_removed else "未找到"}, 文件: {"已删除" if file_removed else "未找到"})',
        'deleted_script_name': script_name
    })
# 用户登录API
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'message': '请填写用户名和密码'})

        # 创建数据库连接
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 查询用户
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'success': False, 'message': '用户名或密码错误'})

        # 验证密码
        if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            # 登录成功，设置会话
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'success': True, 'username': username})
        else:
            return jsonify({'success': False, 'message': '用户名或密码错误'})

    except Exception as e:
        print(f"登录错误: {e}")
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'})

    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()


# 用户注册API
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'success': False, 'message': '请填写用户名和密码'})

        # 创建数据库连接
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '用户名已存在'})

        # 哈希处理密码
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # 插入新用户
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                       (username, hashed_password))
        conn.commit()

        # 创建用户信息文件
        user_info_dir = os.path.join('mpspdz', 'user_information')
        os.makedirs(user_info_dir, exist_ok=True)
        user_file_path = os.path.join(user_info_dir, f'{username}.json')
        initial_data = {
            "own_table_name": [],
            "owner_invite": [],
            "available_invite": [],
            "available_table_name": [],
            "access_count": []
        }
        try:
            with open(user_file_path, 'w') as f:
                json.dump(initial_data, f, indent=4)
        except Exception as e:
            # 回滚数据库操作
            cursor.execute("DELETE FROM users WHERE username = %s", (username,))
            conn.commit()
            return jsonify({'success': False, 'message': '注册失败：无法创建用户配置文件'})

        return jsonify({'success': True, 'message': '注册成功，请登录'})

    except Exception as e:
        print(f"注册错误: {e}")
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'})

    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()

# 退出API
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})


# 检查登录状态API
@app.route('/check_login')
def check_login():
    if 'user_id' in session:
        return jsonify({
            'loggedIn': True,
            'username': session.get('username')
        })
    return jsonify({'loggedIn': False})


@app.route('/upload_table', methods=['POST'])
@login_required
def upload_table():
    try:
        manager = TableManager(session['username'])
        result = manager.handle_upload(request.files)
        if not result['success']:
            return jsonify(result)
        return jsonify({
            'success': True,
            'temp_id': result['temp_id'],
            'columns': result['columns'],
            'table_name': result['table_name']
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/set_permissions', methods=['POST'])
@login_required
def set_permissions():
    try:
        data = request.json
        temp_id = data.get('temp_id')
        if not temp_id:
            return jsonify({'success': False, 'message': '缺少 temp_id 参数'})
        
        manager = TableManager(session['username'])
        result = manager.commit_permissions(
            temp_id=temp_id,
            permissions=data['permissions'],
            free_count=data['free_count'],
            price=data['price']
        )
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/execute_query', methods=['POST'])
@login_required
def execute_query():
    try:
        username = session.get('username')
        data = request.json  # 修复：获取完整的 request.json
        sql_query = data.get('query')  # 修复：从 data 中获取 'query' 字段
        
        if not sql_query:
            return jsonify({'success': False, 'message': '请输入SQL查询语句'})
        
        # 解析SQL语句
        parser = Parsed(sql_query)
        selected_columns = parser.o_col()
        column_methods = parser.column_methods_list()  # 获取列方法列表
        from_table = parser.form()
        
        if not from_table:
            return jsonify({'success': False, 'message': 'SQL语句中缺少FROM子句'})
        
        # 检查表是否存在及用户权限
        table_columns_json_path = os.path.join(DB_DIR, from_table, 'columns.json')
        if not os.path.exists(table_columns_json_path):
            return jsonify({'success': False, 'message': f'表 {from_table} 不存在'})
        
        # 读取表的元数据
        with open(table_columns_json_path, 'r') as f:
            metadata = json.load(f)
        
        # 检查用户是否有访问权限
        user_info_path = os.path.join(USER_INFO_DIR, f'{username}.json')
        has_owner_access = False
        has_available_access = False
        remaining_access = 0
        
        if os.path.exists(user_info_path):
            with open(user_info_path, 'r') as f:
                user_data = json.load(f)
            
            # 检查是否为表的拥有者
            if from_table in user_data.get('own_table_name', []):
                has_owner_access = True
            
            # 检查是否有受限访问权限
            available_tables = user_data.get('available_table_name', [])
            access_counts = user_data.get('access_count', [])
            
            if from_table in available_tables:
                table_index = available_tables.index(from_table)
                if table_index < len(access_counts):
                    remaining_access = access_counts[table_index]
                    if remaining_access > 0:
                        has_available_access = True
        
        if not has_owner_access and not has_available_access:
            return jsonify({'success': False, 'message': f'您没有访问表 {from_table} 的权限'})
        
        # 权限检查
        table_columns = metadata.get('columns', [])
        permissions = metadata.get('permissions', [1] * len(table_columns))
        restricted_columns = []
        
        for i, col in enumerate(selected_columns):
            if col == '*':
                # 检查所有列的权限
                for j, table_col in enumerate(table_columns):
                    if j < len(permissions) and permissions[j] == 0:
                        if not has_owner_access:
                            restricted_columns.append(table_col)
            elif col in table_columns:
                col_index = table_columns.index(col)
                if col_index < len(permissions) and permissions[col_index] == 0:
                    if not has_owner_access:
                        # 检查是否为受限列，以及使用的方法是否被允许
                        query_method = column_methods[i] if i < len(column_methods) else None
                        allowed_methods = metadata.get(col, [])
                        print(query_method)
                        
                        # 如果查询方法不在允许列表中，则为受限访问
                        if query_method is None:
                            # 没有使用任何方法，如果没有允许任何方法则受限
                            restricted_columns.append(col)
                        elif query_method not in allowed_methods:
                            restricted_columns.append(col)
        
        if restricted_columns:
            return jsonify({
                'success': False, 
                'message': f'您没有权限访问以下列: {", ".join(restricted_columns)}'
            })
        
        # 执行查询
        #executor = SQLExecutor()
        #result = executor.execute(sql_query)
        
        try:
            executor = SQLExecutor()
            print(f"开始执行查询: {sql_query}")
            result = executor.execute(sql_query)
            print(f"查询执行完成，结果: {result}")
            
            # 处理 SQLExecutor 返回的元组格式
            if isinstance(result, tuple):
                success, message = result
                result = {'success': success, 'message': message}
            elif not isinstance(result, dict):
                # 如果不是字典也不是元组，转换为标准格式
                result = {'success': False, 'message': str(result)}
                
        except Exception as exec_error:
            print(f"执行查询时发生异常: {exec_error}")
            return jsonify({'success': False, 'message': f'执行查询时发生异常: {str(exec_error)}'})
        
        # 扣除访问次数
        if has_available_access and not has_owner_access and result.get('success'):
            with open(user_info_path, 'r+') as f:
                user_data = json.load(f)
                available_tables = user_data.get('available_table_name', [])
                access_counts = user_data.get('access_count', [])
                
                if from_table in available_tables:
                    table_index = available_tables.index(from_table)
                    if table_index < len(access_counts):
                        access_counts[table_index] = max(0, access_counts[table_index] - 1)
                        
                f.seek(0)
                json.dump(user_data, f, indent=4)
                f.truncate()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'执行查询时发生错误: {str(e)}'})


@app.route('/download')
def download():
    try:
        result_path = os.path.join(USER_DIR, 'result_table.zip')
        if os.path.exists(result_path):
            return send_file(result_path,
                             mimetype='application/zip',
                             as_attachment=True,
                             download_name='result_table.zip')
        else:
            return "结果文件不存在，请先执行查询", 404
    except Exception as e:
        return str(e), 500


@app.route('/list_tables')
@login_required # 如果需要登录才能查看列表，取消注释
def list_tables():
    tables_to_display = []
    username = session.get('username')

    if not username:
        return jsonify({'success': False, 'message': '用户未登录或会话已过期', 'tables': []})

    user_json_path = os.path.join(USER_INFO_DIR, f"{username}.json")

    if not os.path.exists(user_json_path):
        return jsonify({'success': True, 'message': '用户数据文件不存在', 'tables': []})

    try:
        with open(user_json_path, 'r') as f:
            user_data = json.load(f)
    except Exception as e:
        print(f"读取用户 {username} 的JSON文件失败: {e}")
        return jsonify({'success': False, 'message': f'读取用户信息失败: {str(e)}', 'tables': []})

    # 处理拥有的表
    owned_table_names = user_data.get('own_table_name', [])
    owner_invites = user_data.get('owner_invite', [])
    available_invites_for_owned = user_data.get('available_invite', [])

    for i, table_name in enumerate(owned_table_names):
        table_columns_json_path = os.path.join(DB_DIR, table_name, 'columns.json')
        if os.path.exists(table_columns_json_path):
            try:
                with open(table_columns_json_path, 'r') as f:
                    col_info = json.load(f)
                
                all_columns = col_info.get('columns', [])
                permissions = col_info.get('permissions', [1] * len(all_columns))
                restricted_columns = [all_columns[idx] for idx, perm in enumerate(permissions) if perm == 0 and idx < len(all_columns)]

                table_info = {
                    'type': 'owned',
                    'name': table_name,
                    'columns': all_columns,
                    'rows': col_info.get('rows', 0),
                    'restricted_columns': restricted_columns,
                    'base_free_access_count': col_info.get('free_access_count', 0),
                    'price_per_access': col_info.get('price_per_access', 0.0),
                    'owner_invite_code': owner_invites[i] if i < len(owner_invites) else 'N/A',
                    'available_invite_code': available_invites_for_owned[i] if i < len(available_invites_for_owned) else 'N/A'
                }
                tables_to_display.append(table_info)
            except Exception as e:
                print(f"处理拥有的表 {table_name} 的元数据失败: {e}")
                tables_to_display.append({
                    'type': 'owned', 'name': table_name, 'error': f'无法读取元数据: {str(e)}'
                })
        else:
            print(f"拥有的表 {table_name} 的 columns.json 未找到")
            tables_to_display.append({
                'type': 'owned', 'name': table_name, 'error': '元数据文件 (columns.json) 未找到'
            })

    # 处理可访问的表
    available_table_names = user_data.get('available_table_name', [])
    access_counts = user_data.get('access_count', [])

    for i, table_name in enumerate(available_table_names):
        table_columns_json_path = os.path.join(DB_DIR, table_name, 'columns.json')
        if os.path.exists(table_columns_json_path):
            try:
                with open(table_columns_json_path, 'r') as f:
                    col_info = json.load(f)

                all_columns = col_info.get('columns', [])
                permissions = col_info.get('permissions', [1] * len(all_columns))
                accessible_columns = [all_columns[idx] for idx, perm in enumerate(permissions) if perm == 1 and idx < len(all_columns)]
                
                table_info = {
                    'type': 'accessible',
                    'name': table_name,
                    'all_columns': all_columns, # 提供所有列名供参考
                    'accessible_columns': accessible_columns,
                    'remaining_access_count': access_counts[i] if i < len(access_counts) else 'N/A',
                    'price_per_access': col_info.get('price_per_access', 0.0)
                }
                tables_to_display.append(table_info)
            except Exception as e:
                print(f"处理可访问的表 {table_name} 的元数据失败: {e}")
                tables_to_display.append({
                    'type': 'accessible', 'name': table_name, 'error': f'无法读取元数据: {str(e)}'
                })
        else:
            print(f"可访问的表 {table_name} 的 columns.json 未找到")
            tables_to_display.append({
                'type': 'accessible', 'name': table_name, 'error': '元数据文件 (columns.json) 未找到'
            })
            
    return jsonify({'success': True, 'tables': tables_to_display})



# 流式SQL查询API - 新版本，只保存到数据库
@app.route('/save_stream_query', methods=['POST'])
@login_required
def save_stream_query():
    try:
        data = request.json
        query = data.get('query')
        email = data.get('email')
        time_settings = data.get('time_settings')
        day_empty = data.get('day_empty', False)
        week_empty = data.get('week_empty', False)

        if not query:
            return jsonify({'success': False, 'message': '缺少SQL查询语句'})

        if not email:
            return jsonify({'success': False, 'message': '缺少接收结果的邮箱地址'})

        if not time_settings:
            return jsonify({'success': False, 'message': '缺少时间设置'})

        # 分割时间设置字符串
        time_parts = time_settings.split()

        # 获取分、时部分（这两个一定不为空）
        minute = time_parts[0]
        hour = time_parts[1]

        # 根据前端标记确定日和周的值
        day = ""
        month = ""
        week = ""

        if day_empty and not week_empty:  # 日为空，星期有值
            day = "*"  # 将空日期存储为"*"
            month = time_parts[2]
            week = time_parts[3]
        elif week_empty and not day_empty:  # 星期为空，日有值
            day = time_parts[2]
            month = time_parts[3]
            week = "*"  # 将空星期存储为"*"
        else:  # 正常情况，所有值都有（但前端已验证日和周不会同时有值）
            day = time_parts[2]
            month = time_parts[3]
            week = time_parts[4]

        # 将"每"也转换为"*" (如果前端传来的值不是"*")
        day = "*" if day == "" else day
        week = "*" if week == "" else week

        # 重新组合时间设置字符串，确保顺序为：分、时、日、月、周
        time_settings = f"{minute} {hour} {day} {month} {week}"
        print(time_settings)
        # 生成脚本文件（修正参数名称）
        script_path, script_name = generate_shell_script(query, email)  # 参数修正为 query 和 email

        # --------------------------------------------
        # 新增：调用 set_mission.sh 添加定时任务
        # --------------------------------------------
        import subprocess
        current_dir = os.path.dirname(os.path.abspath(__file__))
        set_mission_script = os.path.join(current_dir, "stream_sql", "set_mission.sh")

        try:
            # 确保脚本有执行权限
            os.chmod(set_mission_script, os.stat(set_mission_script).st_mode | stat.S_IEXEC)

            # 使用绝对路径确保可靠性
            result = subprocess.run(
                [set_mission_script, time_settings, script_path],
                check=True,
                capture_output=True,
                text=True
            )
            print("定时任务添加输出:", result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"执行 set_mission.sh 失败 - stdout: {e.stdout}")
            print(f"执行 set_mission.sh 失败: {e.stderr}")
            return jsonify({'success': False, 'message': f'定时任务添加失败: {e.stderr}'})

        # 获取当前用户名
        username = session.get('username')

        # 将流式查询保存到数据库
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO stream_queries (username, email, query_text, script_name, time_settings) VALUES (%s, %s, %s, %s, %s)",
            (username, email, query, script_name, time_settings)
        )
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'message': '流式查询设置已成功保存'
        })
    except Exception as e:
        print(f"保存流式查询出错: {e}")
        return jsonify({'success': False, 'message': f'保存流式查询出错: {str(e)}'})


@app.route('/my_stream_tasks', methods=['GET'])
@login_required
def my_stream_tasks():
    username = session['username']
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            port=DB_CONFIG['port'],
            database=DB_NAME,
            use_pure=True,
            ssl_disabled=True
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, query_text, time_settings, script_name, created_at FROM stream_queries WHERE username = %s ORDER BY created_at DESC", (username,))
        tasks = cursor.fetchall()
        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        print(f"Error fetching stream tasks: {e}") # 建议添加日志
        return jsonify({'success': False, 'message': f'获取任务列表失败: {str(e)}'})
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()




@app.route('/add_table_by_invite', methods=['POST'])
@login_required
def add_table_by_invite():
    username = session.get('username')
    
    try:
        data = request.json
        invite_code = data.get('invite_code')

        if not invite_code:
            return jsonify({'success': False, 'message': '请输入邀请码'})

        user_json_path = os.path.join(USER_INFO_DIR, f"{username}.json")
        if not os.path.exists(user_json_path):
            return jsonify({'success': False, 'message': '用户配置文件不存在，请重新登录或联系管理员'})

        # 1. 检查OwnerInvite.json (管理员权限)
        owner_invite_path = os.path.join(USER_INFO_DIR, 'OwnerInvite.json')
        if os.path.exists(owner_invite_path):
            try:
                with open(owner_invite_path, 'r', encoding='utf-8') as f:
                    owner_invites_data = json.load(f)
                
                if isinstance(owner_invites_data, dict) and invite_code in owner_invites_data:
                    item = owner_invites_data[invite_code]
                    
                    if isinstance(item, dict) and 'table' in item:
                        table_name = item['table']
                        generated_by = item.get('generated_by', '未知用户')
                        
                        # 检查是否已经拥有该表
                        with open(user_json_path, 'r', encoding='utf-8') as f_user:
                            user_data = json.load(f_user)
                            own_tables = user_data.get('own_table_name', [])
                            
                            if table_name in own_tables:
                                return jsonify({
                                    'success': False, 
                                    'message': f'您已经拥有表 "{table_name}" 的管理员权限，无需重复添加',
                                    'table_name': table_name,
                                    'permission_type': '管理员权限',
                                    'error_type': 'duplicate'
                                })
                        
                        # 添加到用户的拥有表列表
                        with open(user_json_path, 'r+', encoding='utf-8') as f_user:
                            user_data = json.load(f_user)
                            own_tables = user_data.setdefault('own_table_name', [])
                            own_tables.append(table_name)
                            f_user.seek(0)
                            json.dump(user_data, f_user, indent=4, ensure_ascii=False)
                            f_user.truncate()
                            
                            return jsonify({
                                'success': True, 
                                'message': f'成功添加表 "{table_name}" 的管理员权限！您现在可以完全访问该表的所有列和数据。',
                                'table_name': table_name,
                                'permission_type': '管理员权限',
                                'generated_by': generated_by,
                                'details': '拥有完全访问权限，可以查看所有列（包括受限列）'
                            })
                            
            except (json.JSONDecodeError, Exception) as e:
                print(f"处理 OwnerInvite.json 时发生错误: {e}")

        # 2. 检查AvailableInvite.json (受限访问权限)
        available_invite_path = os.path.join(USER_INFO_DIR, 'AvailableInvite.json')
        if os.path.exists(available_invite_path):
            try:
                with open(available_invite_path, 'r', encoding='utf-8') as f:
                    available_invites_data = json.load(f)

                if isinstance(available_invites_data, dict) and invite_code in available_invites_data:
                    item = available_invites_data[invite_code]

                    if isinstance(item, dict) and 'table' in item:
                        table_name = item['table']
                        generated_by = item.get('generated_by', '未知用户')
                        
                        # 检查表的元数据是否存在
                        table_columns_json_path = os.path.join(DB_DIR, table_name, 'columns.json')
                        if not os.path.exists(table_columns_json_path):
                            return jsonify({
                                'success': False, 
                                'message': f'表 "{table_name}" 的元数据文件不存在，该表可能已被删除',
                                'table_name': table_name,
                                'error_type': 'table_not_found'
                            })

                        # 读取表的访问信息
                        try:
                            with open(table_columns_json_path, 'r', encoding='utf-8') as cf:
                                col_info = json.load(cf)
                                free_access_count = col_info.get('free_access_count', 0)
                                all_columns = col_info.get('columns', [])
                                permissions = col_info.get('permissions', [1] * len(all_columns))
                                accessible_columns = [all_columns[i] for i, perm in enumerate(permissions) if perm == 1 and i < len(all_columns)]
                                restricted_columns = [all_columns[i] for i, perm in enumerate(permissions) if perm == 0 and i < len(all_columns)]
                        except Exception as e_col:
                            return jsonify({
                                'success': False, 
                                'message': f'读取表 "{table_name}" 的元数据失败: {str(e_col)}',
                                'table_name': table_name,
                                'error_type': 'metadata_error'
                            })

                        # 检查是否已经可以访问该表
                        with open(user_json_path, 'r', encoding='utf-8') as f_user:
                            user_data = json.load(f_user)
                            available_tables = user_data.get('available_table_name', [])
                            own_tables = user_data.get('own_table_name', [])
                            
                            if table_name in own_tables:
                                return jsonify({
                                    'success': False, 
                                    'message': f'您已经拥有表 "{table_name}" 的管理员权限，无需添加受限访问权限',
                                    'table_name': table_name,
                                    'permission_type': '管理员权限（已拥有）',
                                    'error_type': 'already_owner'
                                })
                                
                            if table_name in available_tables:
                                return jsonify({
                                    'success': False, 
                                    'message': f'您已经拥有表 "{table_name}" 的受限访问权限，无需重复添加',
                                    'table_name': table_name,
                                    'permission_type': '受限访问权限',
                                    'error_type': 'duplicate'
                                })

                        # 添加到用户的可访问表列表
                        with open(user_json_path, 'r+', encoding='utf-8') as f_user:
                            user_data = json.load(f_user)
                            available_tables = user_data.setdefault('available_table_name', [])
                            access_counts = user_data.setdefault('access_count', [])
                            
                            # 保持access_counts与available_tables长度一致
                            while len(access_counts) < len(available_tables):
                                access_counts.append(0)

                            available_tables.append(table_name)
                            access_counts.append(free_access_count)
                            
                            f_user.seek(0)
                            json.dump(user_data, f_user, indent=4, ensure_ascii=False)
                            f_user.truncate()
                            
                            return jsonify({
                                'success': True, 
                                'message': f'成功添加表 "{table_name}" 的受限访问权限！',
                                'table_name': table_name,
                                'permission_type': '受限访问权限',
                                'generated_by': generated_by,
                                'free_access_count': free_access_count,
                                'accessible_columns': accessible_columns,
                                'restricted_columns': restricted_columns,
                                'details': f'可访问 {len(accessible_columns)} 个列，受限 {len(restricted_columns)} 个列，免费访问 {free_access_count} 次'
                            })
                            
            except (json.JSONDecodeError, Exception) as e:
                print(f"处理 AvailableInvite.json 时发生错误: {e}")
        
        # 如果在两个文件中都没找到邀请码
        return jsonify({
            'success': False, 
            'message': '邀请码无效或已过期，请检查邀请码是否正确输入',
            'error_type': 'invalid_code'
        })

    except FileNotFoundError as e_fnf:
        print(f"文件未找到错误: {e_fnf}")
        return jsonify({
            'success': False, 
            'message': '系统文件缺失，请联系管理员',
            'error_type': 'file_not_found'
        })
    except json.JSONDecodeError as e_json:
        print(f"JSON解析错误: {e_json}")
        return jsonify({
            'success': False, 
            'message': '用户配置文件格式错误，请联系管理员',
            'error_type': 'json_error'
        })
    except Exception as e:
        print(f"未知错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False, 
            'message': '系统内部错误，请稍后重试或联系管理员',
            'error_type': 'internal_error'
        })

@app.route('/commit_permissions', methods=['POST'])
@login_required
def commit_permissions():
    try:
        username = session.get('username')
        data = request.json
        
        temp_id = data.get('temp_id')
        permissions = data.get('permissions')
        free_count = data.get('free_count')
        price = data.get('price')
        restricted_column_methods = data.get('restricted_column_methods', {})
        
        if not all([temp_id, permissions is not None, free_count is not None, price is not None]):
            return jsonify({'success': False, 'message': '缺少必要参数'})
        
        manager = TableManager(username)
        result = manager.commit_permissions(temp_id, permissions, free_count, price, restricted_column_methods)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'提交权限时发生错误: {str(e)}'})

if __name__ == '__main__':
    init_db()  # 初始化数据库
    app.run(host='0.0.0.0', port=65533, debug=True)
# cd ./mpspdz
# chmod +x Scripts/*.sh
# chmod +x compile.py
# chmod +x *.sh
