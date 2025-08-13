import json
import os
import shutil
from sql_discribe import Parsed as parsed 
import re

class Load:
    def __init__(self, sql):
        self.parser = parsed(sql)
        self.table_name = self.parser.form()  # 获取表名
        self.columns = self.parser.o_col()  # 获取列名列表
        self.method=self.parser.mtd()
        self.where_condition = self.parser.where_stack()  # 获取where条件列表
        self.cache_hit_count = 0  # 添加缓存命中计数器
        self.End=[]
        self._OP_MAP = {'<=': 'le', '>=': 'ge', '!=': 'ne', '<>': 'ne','<': 'lt', '>': 'gt', '=': 'eq'}
        # 路径设置
        self.base_dir = os.path.dirname(os.path.abspath(__file__))  # 脚本所在目录
        self.db_dir = os.path.join(self.base_dir, "db")  # db文件夹路径
        self.table_dir = os.path.join(self.db_dir, self.table_name)  # 表名文件夹路径
        self.persistence_dir = os.path.join(self.base_dir, "Persistence")  # Persistence文件夹路径
        self.summary_path = os.path.join(self.base_dir, "columns_sum.json")  #columns_sum.json文件路径
        self.result_path=os.path.join(self.base_dir,"user","columns_result.json")
        self.sql = sql
        self.metadata_path = os.path.join(self.table_dir, "columns.json")
        
    def r_table_name(self):
        return self.table_name
    def r_where(self):
        return self.where_condition
    def r_updated_where(self):
        """返回处理缓存后更新的where条件"""
        return self.where_condition
    
    def get_cache_hit_count(self):
        """返回缓存命中次数"""
        return self.cache_hit_count
    
    def _ensure_summary_file(self):
        """确保columns_sum.json文件存在且结构正确"""
        if not os.path.exists(self.summary_path):
            # 如果文件不存在，创建并初始化
            with open(self.summary_path, "w") as f:
                json.dump({
                    "table_name": [],
                    "end": [],
                }, f, indent=2)
    def write_result_file(self):
        """确保columns_result.json文件存在且结构正确"""
        try:
            # 确保user目录存在
            os.makedirs(os.path.dirname(self.result_path), exist_ok=True)
            
            # creat or clear document
            with open(self.result_path, "w") as f:
                json.dump({
                    "table_name": [],
                    "columns": [],
                    "rows": 0,
                    "cols": 0,
                    "string_encoding": "base64_value",  # 记录编码方式改为base64
                    "string_columns": []    # 记录哪些列是字符串类型
                }, f, indent=2)
        
            str_indices, column_names, _, selected_columns = self.ReadColumns()
            rows_array, cols_array = self.RowColNum()
        
            with open(self.result_path, "r+") as f:
                data = json.load(f)
                
                # 构建表名字符串：主表名 + JOIN表（如果存在）
                table_name_str = self.table_name
                join_tables = self.parser.join_tables_list()
                if join_tables:
                    table_name_str += "," + ",".join(join_tables)
                
                data["table_name"].append(table_name_str)  # 添加表名（包括JOIN表）
                data["columns"] = selected_columns
                
                # 计算rows：如果有JOIN表，则将所有表的行数相乘
                if join_tables:
                    total_rows = 1
                    # 将所有表的行数相乘
                    for row_count in rows_array:
                        total_rows *= row_count
                    data["rows"] = total_rows
                else:
                    data["rows"] = rows_array[0]  # 只有主表时，取第一个元素
                
                data["cols"] = len(selected_columns)
                data["string_columns"] = str_indices
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
                
            return "文件写入成功"
            
        except Exception as e:
            return f"写入失败: {str(e)}"


    def ReadColumns(self):
        """读取columns.json并生成列下标映射"""
        try:
            # 获取所有表名（主表 + JOIN表）
            all_tables = [self.table_name]
            join_tables = self.parser.join_tables_list()
            if join_tables:
                all_tables.extend(join_tables)
            
            # 初始化全局列表和字符串列索引
            all_columns_list = []
            all_str_col = []
            current_offset = 0
            
            # 循环读取所有表的columns.json文件
            for table_name in all_tables:
                table_dir = os.path.join(self.db_dir, table_name)
                with open(os.path.join(table_dir, "columns.json"), "r") as f:
                    data = json.load(f)
                    table_columns = data["columns"]
                    table_str_col = data.get("string_columns", [])
                    
                    # 将当前表的列名添加到全局列表
                    all_columns_list.extend(table_columns)
                    
                    # 调整字符串列索引并添加到全局列表
                    adjusted_str_col = [idx + current_offset for idx in table_str_col]
                    all_str_col.extend(adjusted_str_col)
                    
                    # 更新偏移量
                    current_offset += len(table_columns)
            
            # 如果查询所有列，则更新self.columns
            if self.columns == ['*']:
                self.columns = all_columns_list
            
            # 创建列名到索引的映射字典
            col_to_idx = {col: idx for idx, col in enumerate(all_columns_list)}
            
            # 生成SQL列对应的索引列表
            # column_indices = [col_to_idx[col] for col in self.columns]
            # common_elements = set(column_indices) & set(all_str_col)
            # str_indices = [idx for idx, num in enumerate(all_str_col) if num in common_elements]

            column_indices = []
            for col in self.columns:
                if col in col_to_idx:
                    column_indices.append(col_to_idx[col])
            
            # 计算字符串列在查询结果中的索引
            str_indices = []
            for i, col_idx in enumerate(column_indices):
                if col_idx in all_str_col:
                    str_indices.append(i)  # 使用查询结果中的索引，不是全局索引
            
            # 获取列方法列表
            column_methods = self.parser.column_methods_list()
            
            # 创建去除groupby方法的列列表
            selected_columns = []
            for i, col in enumerate(self.columns):
                # 如果索引超出方法列表范围，或者方法不是groupby，则添加到selected_columns
                if i >= len(column_methods) or column_methods[i] != 'groupby':
                    selected_columns.append(col)
            
            return str_indices, all_columns_list, self.columns, selected_columns
        except Exception as e:
            raise RuntimeError(f"读取columns.json失败: {str(e)}")

    def RowColNum(self):
        """获取行数和列数"""
        try:
            # 获取所有表名（主表 + JOIN表）
            all_tables = [self.table_name]
            join_tables = self.parser.join_tables_list()
            if join_tables:
                all_tables.extend(join_tables)
            
            # 初始化行数和列数数组
            rows_array = []
            cols_array = []
            
            # 循环读取所有表的columns.json文件
            for table_name in all_tables:
                table_dir = os.path.join(self.db_dir, table_name)
                with open(os.path.join(table_dir, "columns.json"), "r") as f:
                    data = json.load(f)
                    rows_array.append(data["rows"])
                    cols_array.append(data["cols"])
            
            return rows_array, cols_array  # 返回行数数组和列数数组
        except Exception as e:
            raise RuntimeError(f"读取行列数失败: {str(e)}")

    def ClearNew(self):
        """清空Persistence文件夹并重置columns_sum.json中的列表"""
        try:
            # 清空Persistence文件夹
            if os.path.exists(self.persistence_dir):
                shutil.rmtree(self.persistence_dir)
            os.makedirs(self.persistence_dir, exist_ok=True)
            
            # 创建三个空文件
            for i in range(3):
                with open(os.path.join(self.persistence_dir, f"Transactions-P{i}.data"), "w") as f:
                    pass

            # 确保columns_sum.json文件存在
            self._ensure_summary_file()

            # 清空columns_sum.json中的列表
            with open(self.summary_path, "r+") as f:
                data = json.load(f)
                for key in data:
                    if isinstance(data[key], list):
                        data[key].clear()
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()

        except Exception as e:
            raise RuntimeError(f"初始化Persistence失败: {str(e)}")

    def LoadSecret(self,x):
        """追加加载加密数据文件并更新columns_sum.json"""
        try:
            # 确保columns_sum.json文件存在
            self._ensure_summary_file()
            
            # 获取所有表名（主表 + JOIN表）
            all_tables = [self.table_name]
            join_tables = self.parser.join_tables_list()
            if join_tables:
                all_tables.extend(join_tables)
            
            # 构建表名字符串用于缓存查询
            table_name_str = ",".join(all_tables)
            
            
            
            # 处理每个数据文件
            for i in range(3):
                dest = os.path.join(self.persistence_dir, f"Transactions-P{i}.data")
                
                # 第一步：复制主表文件到Persistence（覆盖）
                main_src = os.path.join(self.table_dir, f"Transactions-P{i}.data")
                
                if os.path.exists(main_src):
                    with open(main_src, "rb") as s_file, open(dest, "wb") as d_file:
                        s_file.seek(x)
                        d_file.write(s_file.read())
                else:
                    # 如果主表文件不存在，创建空文件
                    open(dest, 'w').close()
                
                # 第二步：追加JOIN表文件的内容（跳过前28字节）
                for join_table in join_tables:
                    join_table_dir = os.path.join(self.db_dir, join_table)
                    join_src = os.path.join(join_table_dir, f"Transactions-P{i}.data")
                    
                    if os.path.exists(join_src):
                        file_size = os.path.getsize(join_src)
                        
                        if file_size > 28:
                            with open(join_src, 'rb') as src:
                                src.seek(28)  # 跳过前28字节
                                content_to_append = src.read()
                            
                            with open(dest, 'ab') as dest_file:  # 以二进制追加模式打开
                                dest_file.write(content_to_append)
            # 检查并处理缓存
            self._process_cache_conditions(table_name_str)
            # 读取Persistence文件夹下Transactions-P0.data文件的当前字节大小
            p0_path = os.path.join(self.persistence_dir, "Transactions-P0.data")
            initial_size = os.path.getsize(p0_path) if os.path.exists(p0_path) else 0

            # 更新columns_sum.json文件
            with open(self.summary_path, "r+") as f:
                data = json.load(f)
                data["table_name"].append(self.table_name)  # 添加表名
                data["end"].append(initial_size)  # 添加当前文件大小
                self.End.append(initial_size)
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()

        except Exception as e:
            raise RuntimeError(f"加载加密文件失败: {str(e)}")
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
    def _process_cache_conditions(self, table_name_str):
        """处理缓存条件，查找并应用缓存数据"""
        try:
            cache_dir = os.path.join(self.base_dir, "cache")
            # 如果cache目录不存在，直接返回
            if not os.path.exists(cache_dir):
                return
            
            # 获取所有表名列表用于缓存目录命名
            all_tables = [self.table_name]
            join_tables = self.parser.join_tables_list()
            if join_tables:
                all_tables.extend(join_tables)
            
            # 构建表名部分：['data','data1','data2']
            safe_tables = [self._sanitize(t) for t in all_tables]
            table_part = "-".join(safe_tables)
            # 解析where条件栈，提取独立的子条件
            sub_conditions = self._parse_sub_conditions(self.where_condition)
            print(sub_conditions)
            # 遍历解析出的子条件
            for condition in sub_conditions:
                if condition == '%':  # 跳过已经处理过的条件
                    continue
                
                # 3. 把子条件也做一次 sanitize，得到形如 B-lt-8
                safe_condition = self._sanitize(condition)

                # 4. 最终目录名：data-data1-data2-B-lt-8
                cache_folder_name = f"{table_part}-{safe_condition}"
                cache_folder_path = os.path.join(cache_dir, cache_folder_name)
                print(cache_folder_path)
                # 检查缓存文件夹是否存在
                if os.path.exists(cache_folder_path):
                    print(f"找到缓存: {cache_folder_name}")
                    
                    # 将缓存文件追加到Persistence文件
                    self._append_cache_files(cache_folder_path)
                    
                    # 将原始where条件栈中对应的条件替换为%号
                    self._replace_condition_in_stack(condition)
                    
                    # 增加缓存命中计数
                    self.cache_hit_count += 1
                    print(f"条件 '{condition}' 已替换为 ''，缓存命中次数: {self.cache_hit_count}")
                else:
                    print(f"未找到缓存: {cache_folder_name}")
                    
        except Exception as e:
            print(f"处理缓存条件时出错: {str(e)}")
    
    def _parse_sub_conditions(self, postfix_tokens):
        """
        从后缀表达式 token 列表中提取所有独立的原子比较条件
        输入: ['A','4','<','B','5','>','and','C','6','>','or']
        输出: ['A<4', 'B>5', 'C>6']
        """
        if not postfix_tokens:
            return []

        cmp_ops = {'<', '<=', '>', '>=', '=', '==', '!=', '<>'}
        stack   = []
        results = []

        for tok in postfix_tokens:
            if tok.lower() in {'and', 'or'}:          # 逻辑运算符：弹出两个操作数
                stack.pop()
                stack.pop()
            elif tok in cmp_ops:                      # 比较运算符：弹出两个操作数
                right = stack.pop()
                left  = stack.pop()
                results.append(f'{left}{tok}{right}')
                # 把该条件整体重新压栈，供上层逻辑节点引用（不再拆分）
                stack.append(f'{left}{tok}{right}')
            else:                                     # 操作数（列名/常量）
                stack.append(tok)

        return results
    
    def _replace_condition_in_stack(self, condition):
        """在where条件栈中替换指定条件为%号"""
        try:
            # 解析条件，获取列名、操作符和值
            match = re.match(r'([A-Za-z_]\w*)([<>=!]+)([A-Za-z0-9_]+)', condition)
            if not match:
                return
                
            column, operator, value = match.groups()
            
            # where_condition的格式是：['A', '4', '<', 'B', '5', '>', 'and']
            # 正确的查找方式：列名、值、操作符
            for i in range(len(self.where_condition) - 2):
                if (self.where_condition[i] == column and 
                    self.where_condition[i + 1] == value and
                    self.where_condition[i + 2] == operator):
                    
                    # 将这三个位置都替换为*
                    self.where_condition[i] = '%'
                    self.where_condition[i + 1] = '"'
                    self.where_condition[i + 2] = '"'
                    print(f"已将条件 {column}{operator}{value} 替换为 ***，另外两个值替换为双引号")
                    break
                    
        except Exception as e:
            print(f"替换条件栈时出错: {str(e)}")
    
    def _append_cache_files(self, cache_folder_path):
        """将缓存文件追加到Persistence文件中"""
        try:
            # 处理每个数据文件 (P0, P1, P2)
            for i in range(3):
                cache_file = os.path.join(cache_folder_path, f"Transactions-P{i}.data")
                dest_file = os.path.join(self.persistence_dir, f"Transactions-P{i}.data")
                
                if os.path.exists(cache_file):
                    file_size = os.path.getsize(cache_file)
                    
                    # 如果文件大小大于28字节，跳过前28字节后追加
                    if file_size > 28:
                        with open(cache_file, 'rb') as src:
                            src.seek(28)  # 跳过前28字节
                            content_to_append = src.read()
                        
                        with open(dest_file, 'ab') as dest:  # 以二进制追加模式打开
                            dest.write(content_to_append)
                        
                        print(f"已追加缓存文件: {cache_file} -> {dest_file}")
                        
                        # 更新end值
                        new_size = os.path.getsize(dest_file)
                        if self.End:
                            self.End[-1] = new_size  # 更新最后一个end值
                        
                        # 更新columns_sum.json中的end值
                        if os.path.exists(self.summary_path):
                            with open(self.summary_path, "r+") as f:
                                data = json.load(f)
                                if data.get("end") and len(data["end"]) > 0:
                                    data["end"][-1] = new_size
                                    f.seek(0)
                                    json.dump(data, f, indent=2)
                                    f.truncate()
                    else:
                        print(f"缓存文件太小，跳过: {cache_file}")
                else:
                    print(f"缓存文件不存在: {cache_file}")
                    
        except Exception as e:
            print(f"追加缓存文件时出错: {str(e)}")

    def r_end(self):
        return self.End

    def r_column_methods(self):
        """返回列操作方法列表"""
        return self.parser.column_methods_list()

    # def read_permissions(self):
    #     # 读取权限信息
    #     try:
    #         with open(self.metadata_path, 'r') as f:
    #             metadata = json.load(f)
    #             permissions = metadata.get('permissions', [])
    #             free_access_count = metadata.get('free_access_count', 0)
    #             return permissions, free_access_count
    #     except Exception as e:
    #         print(f"读取权限信息出错: {e}")
    #         return [], 0
    
    def read_permissions(self):
        """
        读取表格的访问权限和免费查询次数
        
        返回:
        - permissions: 每一列的访问权限 (1表示允许, 0表示限制)
        - free_access_count: 剩余的免费查询次数
        """
        try:
            with open(self.metadata_path, 'r') as f:
                metadata = json.load(f)
                permissions = metadata.get('permissions', [])
                free_access_count = metadata.get('free_access_count', 0)
                
                # 如果没有权限信息，默认全部允许访问
                if not permissions:
                    permissions = [1] * len(metadata.get('columns', []))
                    
                return permissions, free_access_count
        except Exception as e:
            print(f"读取权限信息出错: {e}")
            return [], 0



#l=Load("select SUM(A),SUM(H),C from data join data1 join data2 where A>2 and B<8 group by C")

# Example usage
#print(l.r_table_name())  # 输出表名
#print(l.r_where())  # 输出where条件
#print(l.r_column_methods())  # 输出列操作方法列表
#print(l.write_result_file())  # 写入结果文件
#print(l.ReadColumns())  # 读取列信息
#l.ClearNew()  # 清空Persistence文件夹并重置columns_sum.json
#l.LoadSecret(0)  # 加载加密数据文件并更新columns_sum.json
#print(l.r_end())  # 输出End列表
#print(l.read_permissions())  # 读取权限信息
#print("缓存命中次数:", l.get_cache_hit_count())  # 输出缓存命中次数
#print("更新后的where条件:", l.r_updated_where())  # 输出更新后的where条件

