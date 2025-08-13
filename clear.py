import os
import shutil

def ensure_directory_exists(directory):
    """确保目录存在，不存在则创建"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录: {directory}")
        return False
    return True

def clear_and_copy_files():
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 定义路径
    db_data_dir = os.path.join(script_dir, 'db', 'data')
    db_data1_dir = os.path.join(script_dir, 'db', 'data1')
    db_data2_dir = os.path.join(script_dir, 'db', 'data2')
    persistence_dir = os.path.join(script_dir, 'Persistence')
    
    # 确保所有目录都存在
    ensure_directory_exists(db_data_dir)
    ensure_directory_exists(db_data1_dir)
    ensure_directory_exists(persistence_dir)
    
    # 目标文件列表
    target_files = [
        'Transactions-P0.data',
        'Transactions-P1.data',
        'Transactions-P2.data'
    ]
    
    # 处理每个文件
    for filename in target_files:
        # 第一步：复制db/data中的文件到Persistence（覆盖）
        source_path = os.path.join(db_data_dir, filename)
        dest_path = os.path.join(persistence_dir, filename)
        
        if os.path.exists(source_path):
            shutil.copy2(source_path, dest_path)
            print(f"已复制: {source_path} → {dest_path}")
        else:
            # 如果源文件不存在，创建空文件
            open(dest_path, 'a').close()
            print(f"警告: {source_path} 不存在，已在目标位置创建空文件")
        
        # 第二步：追加db/data1中文件的内容（跳过前28字节）
        append_source_path = os.path.join(db_data1_dir, filename)
        
        if os.path.exists(append_source_path):
            file_size = os.path.getsize(append_source_path)
            
            if file_size > 28:
                with open(append_source_path, 'rb') as src:
                    src.seek(28)  # 跳过前28字节
                    content_to_append = src.read()
                
                with open(dest_path, 'ab') as dest:  # 以二进制追加模式打开
                    dest.write(content_to_append)
                
                print(f"已追加: {append_source_path} (跳过28字节) → {dest_path}")
            else:
                print(f"跳过: {append_source_path} 小于28字节，无法跳过28字节")
        else:
            print(f"警告: {append_source_path} 不存在，跳过追加")
        append_source_path = os.path.join(db_data2_dir, filename)

        if os.path.exists(append_source_path):
            file_size = os.path.getsize(append_source_path)

            if file_size > 28:
                with open(append_source_path, 'rb') as src:
                    src.seek(28)  # 跳过前28字节
                    content_to_append = src.read()

                with open(dest_path, 'ab') as dest:  # 以二进制追加模式打开
                    dest.write(content_to_append)

                print(f"已追加: {append_source_path} (跳过28字节) → {dest_path}")
            else:
                print(f"跳过: {append_source_path} 小于28字节，无法跳过28字节")
        else:
            print(f"警告: {append_source_path} 不存在，跳过追加")

if __name__ == "__main__":
    clear_and_copy_files()
    print("\n操作完成!")
