from flask import Flask, render_template, request, jsonify, send_file, send_from_directory
import os
import subprocess
import base64
import json
import shutil
import csv
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='user_templates', static_folder='static')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 确保必要的目录存在
os.makedirs('mpspdz/usercsv', exist_ok=True)
os.makedirs('mpspdz/user', exist_ok=True)
os.makedirs('mpspdz/Persistence', exist_ok=True)

@app.route('/')
def home():
    return render_template('userindex.html')

@app.route('/encrypt')
def encrypt_page():
    return render_template('encrypt.html')

@app.route('/decrypt')
def decrypt_page():
    return render_template('decrypt.html')

@app.route('/api/encrypt', methods=['POST'])
def encrypt():
    # --- 1. 定义清晰的绝对路径 ---
    project_root = os.path.dirname(os.path.abspath(__file__))
    mpspdz_dir = os.path.join(project_root, 'mpspdz')
    usercsv_dir = os.path.join(mpspdz_dir, 'usercsv')
    
    try:
        # 获取上传的CSV文件
        file = request.files.get('csv-file')
        if not file or not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': '请上传CSV文件'})

        filename = secure_filename(file.filename)
        
        # 确保目录存在并保存CSV文件
        os.makedirs(usercsv_dir, exist_ok=True)
        csv_path = os.path.join(usercsv_dir, filename)
        file.save(csv_path)
        
        # 读取CSV内容用于预览
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        # --- 2. 执行加密命令 (正确的方式) ---
        
        # 步骤 A: 运行 compile.py 脚本
        # 使用 cwd 参数指定子进程的工作目录，不改变主进程
        # 捕获 stdout 和 stderr 用于调试
        compile_process = subprocess.Popen(
            ['./compile.py', '-R', '64', 'encode'],
            cwd=mpspdz_dir,  # <-- 关键改动：为子进程指定工作目录
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        # 将数据源目录作为输入传递给编译器
        stdout, stderr = compile_process.communicate(input=csv_path + '\n')
        
        # --- 3. 增强错误捕获 ---
        if compile_process.returncode != 0:
            # 编译失败，返回详细错误信息
            error_message = f"编译失败 (Exit Code: {compile_process.returncode}):\n{stderr}"
            print(error_message) # 在后端打印日志
            return jsonify({'success': False, 'message': error_message})

        # 步骤 B: 运行 ring.sh 脚本
        subprocess.run(
            ['./Scripts/ring.sh', 'encode'], 
            check=True, # check=True 会在命令失败时自动抛出异常
            cwd=mpspdz_dir, # <-- 关键改动：同样指定工作目录
            capture_output=True, # 捕获输出
            text=True
        )
        
        # --- 4. 使用绝对或稳定的相对路径读取结果 ---
        p0_path = os.path.join(mpspdz_dir, 'Persistence/Transactions-P0.data')
        p1_path = os.path.join(mpspdz_dir, 'Persistence/Transactions-P1.data')
        p2_path = os.path.join(mpspdz_dir, 'Persistence/Transactions-P2.data')
        
        with open(p0_path, 'rb') as f:
            p0_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        with open(p1_path, 'rb') as f:
            p1_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        with open(p2_path, 'rb') as f:
            p2_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        return jsonify({
            'success': True,
            'preview': csv_content,
            'p0_base64': p0_base64,
            'p1_base64': p1_base64,
            'p2_base64': p2_base64
        })
        
    except subprocess.CalledProcessError as e:
        # 捕获 ring.sh 等 check=True 的命令失败
        error_message = f"脚本执行失败 (Exit Code: {e.returncode}):\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        print(error_message)
        # 注意：不要在生产环境中将详细的 stderr 暴露给前端
        return jsonify({'success': False, 'message': "后端脚本执行失败，请查看服务器日志。"})
    except Exception as e:
        # 捕获所有其他异常
        print(f"发生未知错误: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/decrypt', methods=['POST'])
def decrypt():
    # --- 1. 定义清晰的绝对路径 ---
    project_root = os.path.dirname(os.path.abspath(__file__))
    mpspdz_dir = os.path.join(project_root, 'mpspdz')
    user_dir = os.path.join(mpspdz_dir, 'user')

    try:
        # 获取上传的zip文件
        file = request.files.get('zip-file')
        if not file or not file.filename.endswith('.zip'):
            return jsonify({'success': False, 'message': '请上传ZIP文件'})

        # 清理并创建目标目录
        if os.path.exists(user_dir):
            shutil.rmtree(user_dir)
        os.makedirs(user_dir)

        # 保存zip文件
        zip_path = os.path.join(user_dir, 'result_table.zip')
        file.save(zip_path)

        # --- 2. 以正确的方式执行解密命令 ---
        # 使用 cwd 参数指定子进程的工作目录，不改变主进程
        subprocess.run(
            ['bash', 'decode.sh'], 
            check=True,  # 命令失败时自动抛出异常
            cwd=mpspdz_dir, # <-- 关键改动：为子进程指定工作目录
            capture_output=True, # 捕获输出用于调试
            text=True
        )
        
        # --- 3. 使用绝对路径查找结果文件 ---
        # 查找生成的CSV文件
        csv_files = [f for f in os.listdir(user_dir) if f.endswith('.csv')]
        if not csv_files:
            return jsonify({'success': False, 'message': '执行成功，但在输出目录未找到解密后的CSV文件。'})

        csv_path = os.path.join(user_dir, csv_files[0])

        # 读取CSV内容用于预览
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()

        return jsonify({
            'success': True,
            'preview': csv_content,
            'filename': csv_files[0]
        })

    except subprocess.CalledProcessError as e:
        # --- 4. 捕获脚本执行失败的特定异常 ---
        error_message = f"解密脚本执行失败 (Exit Code: {e.returncode}):\nSTDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
        print(error_message) # 在后端打印详细日志
        return jsonify({'success': False, 'message': "后端解密脚本执行失败，请查看服务器日志。"})
    except Exception as e:
        # 捕获所有其他未知异常
        print(f"解密过程中发生未知错误: {str(e)}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/download/<filename>')
def download_file(filename):
    try:
        if filename == 'decrypted':
            # 查找CSV文件
            csv_files = [f for f in os.listdir('mpspdz/user') if f.endswith('.csv')]
            if csv_files:
                return send_from_directory('mpspdz/user', csv_files[0], as_attachment=True)
            else:
                return jsonify({'success': False, 'message': '文件不存在'}), 404
        
        if filename in ['columns.json', 'Transactions-P0.data', 'Transactions-P1.data', 'Transactions-P2.data']:
            if filename == 'columns.json':
                path = 'mpspdz/columns.json'
            else:
                path = f'mpspdz/Persistence/{filename}'
            
            if os.path.exists(path):
                return send_file(path, as_attachment=True)
            else:
                return jsonify({'success': False, 'message': '文件不存在'}), 404
                
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=65534, debug=True)
