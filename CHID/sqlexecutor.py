import os
import subprocess
import shutil
import zipfile
class SQLExecutor:
    def __init__(self, mp_spdz_dir="./mpspdz", user_dir="user", db_dir="db", persis_dir="Persistence"):
        self.mp_spdz_dir = mp_spdz_dir
        self.user_dir = os.path.join(mp_spdz_dir, user_dir)
        self.db_dir = os.path.join(mp_spdz_dir, db_dir)
        self.persis_dir = os.path.join(mp_spdz_dir, persis_dir)
        
        # 创建必要目录
        os.makedirs(self.user_dir, exist_ok=True)
        os.makedirs(self.db_dir, exist_ok=True)
        os.makedirs(self.persis_dir, exist_ok=True)

    def execute(self, sql_query):
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
                return ring_result
            
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

# 使用示例
# executor = SQLExecutor()
# success, message = executor.execute("SELECT * FROM table")
