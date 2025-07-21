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
        self.End=[]
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
    
    def update_free_access_count(self, new_count):
        # 更新免费访问次数
        try:
            with open(self.metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metadata['free_access_count'] = new_count
            
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
                
            return True
        except Exception as e:
            print(f"更新免费访问次数出错: {e}")
            return False
    
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

    def update_free_access_count(self, new_count):
        """
        更新表格的免费查询次数
        
        参数:
        - new_count: 新的免费查询次数
        
        返回:
        - 更新是否成功
        """
        try:
            with open(self.metadata_path, 'r') as f:
                metadata = json.load(f)
            
            metadata['free_access_count'] = new_count
            
            with open(self.metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
                
            return True
        except Exception as e:
            print(f"更新免费访问次数出错: {e}")
            return False


l=Load("select SUM(A),C from data join data1 join data2 where A<4 and B>5 GROUP BY C,D")

# Example usage
print(l.r_table_name())  # 输出表名
print(l.r_where())  # 输出where条件
print(l.r_column_methods())  # 输出列操作方法列表
print(l.write_result_file())  # 写入结果文件
print(l.ReadColumns())  # 读取列信息
l.ClearNew()  # 清空Persistence文件夹并重置columns_sum.json
l.LoadSecret(0)  # 加载加密数据文件并更新columns_sum.json
print(l.r_end())  # 输出End列表
print(l.read_permissions())  # 读取权限信息

