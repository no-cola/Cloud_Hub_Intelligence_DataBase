import json
import os
import shutil

with open('./columns_sum.json', 'r') as f:
    columns_sum = json.load(f)
    
    a = columns_sum['end'][-1]
    tablename = columns_sum['table_name'][-1]
    
    persistence_dir = './Persistence'
    user_dir = './user'
    
    os.makedirs(user_dir, exist_ok=True)

    # 处理Persistence文件
    for filename in os.listdir(persistence_dir):
        file_path = os.path.join(persistence_dir, filename)
        
        # 读取二进制内容
        with open(file_path, 'rb') as f:
            content = f.read()
            print(os.path.getsize(file_path))
    
        new_content = content[:28] + content[a:] # changed
        
        # 写persistence目录
        output_path = os.path.join(persistence_dir, filename)
        with open(output_path, 'wb') as f:
            f.write(new_content)
        #4. 移动结果文件
        #if os.path.exists(os.path.join('user', filename)):
        #    os.remove(os.path.join('user', filename))  # 删除文件
        #shutil.move(file_path, os.path.join('user', filename))
   
    
    print("处理完成！结果已保存至Persistence目录。")

