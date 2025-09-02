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
    try:
        # 获取上传的CSV文件
        file = request.files['csv-file']
        if not file or not file.filename.endswith('.csv'):
            return jsonify({'success': False, 'message': '请上传CSV文件'})
        
        # 保存CSV文件
        csv_path = os.path.join('mpspdz/usercsv', 'input.csv')
        file.save(csv_path)
        
        # 读取CSV内容用于预览
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        # 执行加密命令
        os.chdir('mpspdz')
        
        # 运行encode脚本
        encode_process = subprocess.Popen(
            ['./compile.py', '-R', '64', 'encode'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        encode_process.communicate(input=os.path.abspath('usercsv') + '\n')
        
        # 运行ring.sh
        subprocess.run(['./Scripts/ring.sh', 'encode'], check=True)
        
        os.chdir('..')
        
        # 读取加密文件并进行Base64编码
        p0_path = 'mpspdz/Persistence/Transactions-P0.data'
        p1_path = 'mpspdz/Persistence/Transactions-P1.data'
        p2_path = 'mpspdz/Persistence/Transactions-P2.data'
        
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
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/decrypt', methods=['POST'])
def decrypt():
    try:
        
        # 获取上传的zip文件
        file = request.files['zip-file']
        if not file or not file.filename.endswith('.zip'):
            return jsonify({'success': False, 'message': '请上传ZIP文件'})
        else:
            if os.path.exists('mpspdz/user'):
                shutil.rmtree('mpspdz/user')
            os.makedirs('mpspdz/user')
        
        # 保存并解压zip文件
        zip_path = os.path.join('mpspdz/user', 'result_table.zip')
        file.save(zip_path)
        
        # 执行解密命令
        os.chdir('mpspdz')
        subprocess.run(['bash', 'decode.sh'], check=True)
        os.chdir('..')
        
        # 查找生成的CSV文件
        csv_files = [f for f in os.listdir('mpspdz/user') if f.endswith('.csv')]
        if not csv_files:
            return jsonify({'success': False, 'message': '未找到解密后的CSV文件'})
        
        csv_path = os.path.join('mpspdz/user', csv_files[0])
        
        # 读取CSV内容用于预览
        with open(csv_path, 'r', encoding='utf-8') as f:
            csv_content = f.read()
        
        return jsonify({
            'success': True,
            'preview': csv_content,
            'filename': csv_files[0]
        })
        
    except Exception as e:
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
