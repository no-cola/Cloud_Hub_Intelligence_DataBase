import os
import re
import subprocess
import shutil
import zipfile
class SQLExecutor:
    def __init__(self, mp_spdz_dir="./mpspdz", user_dir="user", db_dir="db", persis_dir="Persistence"):
        self.mp_spdz_dir = mp_spdz_dir
        self.user_dir = os.path.join(mp_spdz_dir, user_dir)
        self.db_dir = os.path.join(mp_spdz_dir, db_dir)
        self.persis_dir = os.path.join(mp_spdz_dir, persis_dir)
        self.cache_dir=os.path.join(mp_spdz_dir, "cache")
        self._OP_MAP = {'<=': 'le', '>=': 'ge', '!=': 'ne', '<>': 'ne','<': 'lt', '>': 'gt', '=': 'eq'}
        # 创建必要目录
        os.makedirs(self.user_dir, exist_ok=True)
        os.makedirs(self.db_dir, exist_ok=True)
        os.makedirs(self.persis_dir, exist_ok=True)

    def query_execute(self, sql_query):
        """执行select_SQL查询并返回(success, message)元组"""
        try:
            # 保存SQL查询到临时文件
            query_path = os.path.join(self.mp_spdz_dir, 'current_query.sql')
            with open(query_path, 'w') as f:
                f.write(sql_query)
            
            # 启动MP-SPDZ
            if not self._run_command("./Scripts/setup-ssl.sh 3"):
                return False, "MP-SPDZ初始化失败"

            # 编译并执行查询
            #compile_cmd = f'echo "{sql_query}" | ./compile.py -R 64 select_query'
            #if not self._run_command(compile_cmd):
            #    return False, "SQL编译失败"
            compile_cmd = f'echo "{sql_query}" | ./compile.py -R 64 select_query'
            compile_result = self._run_command(compile_cmd, get_output=True)
            if not compile_result[0]:
                print(f"编译失败，错误信息: {compile_result[1]}")
                return False, f"SQL编译失败: {compile_result[1]}"
            ring_cmd = './Scripts/ring.sh select_query'
            ring_result = self._run_command(ring_cmd, get_output=True)
            if not ring_result[0]:
                print(f"zhi xing 失败，错误信息: {ring_result[1]}")
                return  False, ring_result[1]
            
            # 处理特殊输出信息
            output = ring_result[1]
            if "免费查询次数已用完" in output:
                return False, "免费查询次数已用完"
            if "无权限访问受限列" in output:
                return False, "权限错误，无权限访问受限列"

            # 预处理结果
            if not self._run_command("python3 decode_prework.py"):
                return False, "结果预处理失败"

            # 移动结果文件
            if not self._move_result_files():
                return False, "结果文件处理失败"  

            # 创建结果压缩包
            result_zip = os.path.join(self.user_dir, 'result_table.zip')
            with zipfile.ZipFile(result_zip, 'w') as zipf:
                for fname in ['columns_result.json', 'Transactions-P0.data',
                             'Transactions-P1.data', 'Transactions-P2.data']:
                    path = os.path.join(self.user_dir, fname)
                    if os.path.exists(path):
                        zipf.write(path, arcname=fname)

            return True, "查询执行成功，结果已准备好下载"
            
        except Exception as e:
            return False, f"查询执行过程中出错: {str(e)}"

    def _run_command(self, command, get_output=False, timeout=300):
        """执行shell命令并返回(success, output)"""
        try:
            print(f"执行命令: {command}")
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.mp_spdz_dir,
                capture_output=True,
                text=True,
                timeout=timeout  # 添加超时设置
            )
            
            print(f"命令返回码: {result.returncode}")
            print(f"标准输出: {result.stdout}")
            print(f"标准错误: {result.stderr}")
            
            if result.returncode != 0:
                return (False, result.stderr) if get_output else False
            return (True, result.stdout) if get_output else True
            
        except subprocess.TimeoutExpired:
            error_msg = f"命令执行超时 ({timeout}秒): {command}"
            print(error_msg)
            return (False, error_msg) if get_output else False
        except Exception as e:
            error_msg = f"执行命令时发生异常: {str(e)}"
            print(error_msg)
            return (False, error_msg) if get_output else False

    def _move_result_files(self):
        """移动持久化文件到用户目录"""
        try:
            for party in [0, 1, 2]:
                src = os.path.join(self.persis_dir, f'Transactions-P{party}.data')
                dst = os.path.join(self.user_dir, f'Transactions-P{party}.data')
                if os.path.exists(src):
                    shutil.move(src, dst)
                else:
                    return False
            return True
        except Exception as e:
            print(f"移动文件失败: {str(e)}")
            return False
    

    def _sanitize(self,name: str) -> str:
        """把 SQL 片段变成文件系统安全的短横线分隔字符串"""
        # 1. 替换运算符
        for op, abbr in sorted(self._OP_MAP.items(), key=lambda kv: -len(kv[0])):
            name = name.replace(op, f'-{abbr}-')
        # 2. 把非数字字母下划线中划线全部换成 -
        name = re.sub(r'[^A-Za-z0-9_-]+', '-', name)
        # 3. 合并多个连续的 -
        name = re.sub(r'-+', '-', name).strip('-')
        return name


    def _move_cache_files(self, sql: str) -> bool:
        """将 cache 文件移动到形如 data-data1-A-lt-1 的目录"""
        try:
            # 1. 抽表名：支持 FROM t1 [alias] JOIN t2 [alias]
            from_part = re.split(r'\bwhere\b', sql, flags=re.I)[0]        # FROM 开始到 WHERE 前
            tables = re.findall(r'\b(?:from|join)\s+([^\s(]+)', from_part, flags=re.I)

            # 2. 抽 WHERE 条件
            where_re = re.compile(r'where\s+(.+)', re.I)
            w = where_re.search(sql)
            if not w:
                return False
            cond = w.group(1)

            # 3. 生成目录名：表名-表名-条件
            parts = [self._sanitize(t) for t in tables] + [self._sanitize(cond)]
            folder = '-'.join(parts)

            cache_save_dir = os.path.join(self.cache_dir, folder)
            os.makedirs(cache_save_dir, exist_ok=True)

            # 4. 移动文件
            for p in range(3):
                src = os.path.join(self.persis_dir, f'Transactions-P{p}.data')
                dst = os.path.join(cache_save_dir, f'Transactions-P{p}.data')
                if not os.path.exists(src):
                    return False
                shutil.move(src, dst)
            return True

        except Exception as e:
            print(f'移动文件失败: {e}')
            return False
    def cache_execute(self, sql_query):
        """执行select_SQL查询并返回(success, message)元组"""
        try:
            # 保存SQL查询到临时文件
            query_path = os.path.join(self.mp_spdz_dir, 'current_query.sql')
            with open(query_path, 'w') as f:
                f.write(sql_query)
            # 启动MP-SPDZ
            if not self._run_command("./Scripts/setup-ssl.sh 3"):
                return False, "MP-SPDZ初始化失败"

            # 编译并执行查询
            #compile_cmd = f'echo "{sql_query}" | ./compile.py -R 64 select_query'
            #if not self._run_command(compile_cmd):
            #    return False, "SQL编译失败"
            compile_cmd = f'echo "{sql_query}" | ./compile.py -R 64 select_cache'
            compile_result = self._run_command(compile_cmd, get_output=True)
            if not compile_result[0]:
                print(f"编译失败，错误信息: {compile_result[1]}")
                return False, f"SQL编译失败: {compile_result[1]}"
            ring_cmd = './Scripts/ring.sh select_cache'
            ring_result = self._run_command(ring_cmd, get_output=True)
            if not ring_result[0]:
                print(f"zhi xing 失败，错误信息: {ring_result[1]}")
                return  False, ring_result[1]
            # 预处理结果
            if not self._run_command("python3 decode_prework.py"):
                return False, "结果预处理失败"
            # 移动结果文件
            if not self._move_cache_files(sql_query):
                return False, "结果文件处理失败"
            return True, "缓存查询执行成功"
        except Exception as e:
            return False, f"查询执行过程中出错: {str(e)}"
    def execute(self, sql_query: str):
        """
        1) 先完整执行 sql_query（query_execute）
        2) 把 WHERE 拆成单条件子语句
        3) 对每条子语句：若缓存目录已存在则跳过，否则执行 cache_execute
        """
        try:
            # ---------- 1. 完整查询 ----------
            ok, msg = self.query_execute(sql_query)
            if not ok:
                return ok, msg

            # ---------- 2. 解析子语句 ----------
            # 去掉 GROUP BY 及其后内容
            sql_no_group = re.split(r'\bgroup\s+by\b', sql_query, flags=re.I)[0].strip()

            # 抽出 FROM ... WHERE 之前的列、表、WHERE 条件
            select_part, from_where = re.split(r'\bfrom\b', sql_no_group, flags=re.I, maxsplit=1)
            select_part = select_part.strip()

            # 再拆出表列表和 WHERE
            from_where_parts = re.split(r'\bwhere\b', from_where, flags=re.I, maxsplit=1)
            tables_part = from_where_parts[0].strip()
            where_part  = from_where_parts[1].strip() if len(from_where_parts) > 1 else ""

            # 按 AND/OR 分割（简单办法：按空格+and/or+空格 切）
            # 如需更严谨可用 sqlparse，这里保持轻量
            conditions = re.split(r'\s+(and|or)\s+', where_part, flags=re.I)
            conditions = [c.strip() for c in conditions
                          if c and c.lower() not in ('and', 'or')]
            print(conditions)
            # ---------- 3. 逐条处理子语句 ----------
            for cond in conditions:
                sub_sql = f"SELECT * FROM {tables_part} WHERE {cond}"
                print(sub_sql)
                # 计算这条子语句对应的缓存目录名（复用 _move_cache_files 的逻辑）
                from_part = re.split(r'\bwhere\b', sql_query, flags=re.I)[0]        # FROM 开始到 WHERE 前
                tables = re.findall(r'\b(?:from|join)\s+([^\s(]+)', from_part, flags=re.I)
                safe_conds = self._sanitize(cond)
                folder_name = '-'.join([self._sanitize(t) for t in tables] + [safe_conds])
                cache_sub_dir = os.path.join(self.cache_dir, folder_name)
                print(cache_sub_dir)
                print("检查缓存目录是否存在:", cache_sub_dir, os.path.isdir(cache_sub_dir))
                if os.path.isdir(cache_sub_dir):
                    # 已缓存，跳过
                    
                    continue

                # 未缓存，执行
                ok_sub, msg_sub = self.cache_execute(sub_sql)
                if not ok_sub:
                    print(f'子查询缓存失败: {sub_sql} -> {msg_sub}')

            return True, "主查询完成，子语句缓存处理结束"

        except Exception as e:
            return False, f"execute 异常: {str(e)}"

# 使用示例
#executor = SQLExecutor()
#success, message = executor.execute("SELECT * FROM data join data1 join data2 WHERE A>2")
