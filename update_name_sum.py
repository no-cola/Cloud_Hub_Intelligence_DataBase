import os

# 读取 name.txt 文件内容
class upload_name_txt:
    """此类功能如下："""
    """将name.txt文件（框架\Temp目录下）更新到name_sum.txt（根目录下）"""
    """name.txt文件格式：表名:列名1,列名2,列名3"""
    """name_sum.txt文件格式：表名:列名1,列名2,列名3:数据表偏移地址"""
    """若表名不存在，将用户的data文件（框架\Temp目录下）追加到现有数据表秘密份额文件末尾（根目录下），并将追加起始位置写入name_sum.txt文件中"""
    """两者先调用read_name_file函数输入name.txt地址再调用update_name_sum函数即可"""
    """仍需实现的功能："""
    """给定列名表名读取name_sum.txt找到对应数据表偏移地址与数据区间大小"""
    def __init__(self):
        self.name_sum_path=os.path.join(os.getcwd(), 'name_sum.txt')
        self.lines=None
        self.source_path=os.path.join(os.getcwd(),'temp')
        self.destination_path=os.path.join(os.getcwd(),'Persistence')
    def read_name_file(self,file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                self.lines = file.readlines()
        except FileNotFoundError:
            print(f"未找到文件: {file_path}")
    # 读取 name_sum.txt 中已有的表名
    def get_existing_table_names(self):
        existing_table_names = set()
        try:
            with open(self.name_sum_path, 'r', encoding='utf-8') as file:
                for line in file:
                    table_name = line.strip().split(':')[0]
                    existing_table_names.add(table_name)
        except FileNotFoundError:
            pass
        return existing_table_names
    #追加data文件
    def append_data_file_with_position(self):
        try:
            start_position=[]
            # 读取源文件中的内容
            for i in range(3):
                with open(os.path.join(self.source_path,f"Transactions-P{i}.data"), 'r') as source_file:
                    content = source_file.read()

                # 获取目标文件的当前大小（字节数）
                with open(os.path.join(self.destination_path,f"Transactions-P{i}.data"), 'a+') as destination_file:
                    destination_file.seek(0, 2)  # 移动到文件末尾
                    start_position.append(destination_file.tell())
                    # 将内容追加到目标文件末尾
                    destination_file.write(content)

                    print(f"Content successfully appended from {i}")
            print(f"Start position of the appended content: {start_position} bytes")
            for i in range(3):
                with open(os.path.join(self.source_path,f"Transactions-gf2n-P{i}.data"), 'r') as source_file:
                    content = source_file.read()

                # 获取目标文件的当前大小（字节数）
                with open(os.path.join(self.destination_path,f"Transactions-gf2n-P{i}.data"), 'a+') as destination_file:
                    destination_file.seek(0, 2)  # 移动到文件末尾
                    start_position.append(destination_file.tell())
                    # 将内容追加到目标文件末尾
                    destination_file.write(content)

                    print(f"Content successfully appended from {i}")
            print(f"Start position of the appended content: {start_position} bytes")
            return start_position
        except Exception as e:
            print(f"An error occurred: {e}")
            return []
    # 更新 name_sum.txt 文件内容
    def update_name_sum(self):
        existing_table_names = self.get_existing_table_names()
        try:
            with open(self.name_sum_path, 'a', encoding='utf-8') as file:
                for line in self.lines:
                    table_name, columns = line.strip().split(':')
                    # 检查表名是否已存在
                    if table_name not in existing_table_names:
                        start_position=self.append_data_file_with_position()
                        # 写入表名、列名和数据文件路径，并且另起一行
                        file.write(f"{table_name}:{columns}:{start_position}\n")
                        existing_table_names.add(table_name)
                    else:
                        print(f"表名 {table_name} 已存在于 name_sum.txt 中，跳过此表。")
        except FileNotFoundError:
            print(f"未找到文件: {self.name_sum_path}")
        except ValueError:
            print(f"name.txt 文件中格式有误，无法正确解析行: {line}")



def main():
    uu=upload_name_txt()
    uu.read_name_file(os.path.join(os.getcwd(), 'Temp','name.txt'))
    # 为了保证代码跨平台性，使用 os.path.join 构建路径
    uu.update_name_sum()

if __name__ == "__main__":
    main()