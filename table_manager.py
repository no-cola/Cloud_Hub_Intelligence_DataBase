# table_manager.py
import os
import json
import time
import uuid
import hashlib
from shutil import rmtree

class TableManager:
    def __init__(self, username):
        self.username = username
        self.base_path = os.path.abspath(os.path.dirname(__file__))
        self.temp_uploads_dir = os.path.join(self.base_path, "temp_uploads")
    
    def handle_upload(self, request_files):
        """处理文件上传到临时目录，返回 temp_id"""
        try:
            required_files = ['secret1', 'secret2', 'secret3', 'table_info']
            if any(f not in request_files for f in required_files):
                raise ValueError("请上传所有必需的文件")

            temp_id = str(uuid.uuid4())
            temp_dir = os.path.join(self.temp_uploads_dir, temp_id)
            os.makedirs(temp_dir, exist_ok=True)

            # 保存文件
            files = {
                'secret1': 'Transactions-P0.data',
                'secret2': 'Transactions-P1.data',
                'secret3': 'Transactions-P2.data',
                'table_info': 'columns.json'
            }
            for field, filename in files.items():
                file = request_files[field]
                file.save(os.path.join(temp_dir, filename))

            # 读取表名
            with open(os.path.join(temp_dir, 'columns.json'), 'r') as f:
                metadata = json.load(f)
                table_name = metadata.get('table_name')
                if not table_name:
                    raise ValueError("columns.json 中缺少表名")

            return {
                'success': True,
                'temp_id': temp_id,
                'table_name': table_name,
                'columns': metadata.get('columns', [])
            }

        except Exception as e:
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                rmtree(temp_dir)
            return {'success': False, 'message': str(e)}


    def commit_permissions(self, temp_id, permissions, free_count, price, restricted_column_methods=None):
        try:
            temp_dir = os.path.join(self.temp_uploads_dir, temp_id)
            if not os.path.isdir(temp_dir):
                raise FileNotFoundError(f"临时目录不存在: {temp_id}")
        
            # 读取临时目录中的columns.json
            metadata_path = os.path.join(temp_dir, 'columns.json')
            if not os.path.exists(metadata_path):
                raise FileNotFoundError("无法找到对应的 columns.json 文件")
                
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                
            table_name = metadata.get('table_name')
            if not table_name:
                raise ValueError("columns.json 中缺少表名")
                
            # 验证权限列表长度是否与列数匹配
            if len(permissions) != len(metadata.get('columns', [])):
                raise ValueError('权限列表长度与列数不匹配')
            
            # 验证 free_count 和 price 是否为有效数字
            try:
                free_count = int(free_count)
                price = float(price)
                if free_count < 0 or price < 0:
                    raise ValueError("数值不能为负")
            except ValueError as ve:
                raise ValueError(f'无效的数值: {ve}')
            
            # 在临时目录的columns.json中添加权限信息
            metadata['permissions'] = permissions  # 0 表示不允许访问, 1 表示允许访问
            metadata['free_access_count'] = free_count
            metadata['price_per_access'] = price
            
            # 添加受限列的方法权限
            if restricted_column_methods:
                columns = metadata.get('columns', [])
                for i, permission in enumerate(permissions):
                    if permission == 0 and i < len(columns):  # 受限列
                        column_name = columns[i]
                        if column_name in restricted_column_methods:
                            metadata[column_name] = restricted_column_methods[column_name]
            
            # 写回更新后的临时JSON数据
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=4)
            
            # 移动文件到正式目录（此时会删除临时目录）
            from app import move_files
            success, msg = move_files(temp_dir)
            if not success:
                return {'success': False, 'message': msg}
            
            # 生成邀请码
            owner_code = self._generate_invite_code(table_name, 'owner')
            available_code = self._generate_invite_code(table_name, 'available')
        
            # 更新用户文件
            user_file = os.path.join(self.base_path, 'mpspdz', 'user_information', f'{self.username}.json')
            
            # 确保用户文件存在
            if not os.path.exists(user_file):
                user_data = {
                    'own_table_name': [],
                    'owner_invite': [],
                    'available_invite': [],
                    'available_table_name': [],
                    'access_count': []
                }
                with open(user_file, 'w') as f:
                    json.dump(user_data, f, indent=4)
            
            with open(user_file, 'r+') as f:
                user_data = json.load(f)
                if table_name not in user_data['own_table_name']:
                    user_data['own_table_name'].append(table_name)
                    user_data['owner_invite'].append(owner_code)
                    user_data['available_invite'].append(available_code)
                f.seek(0)
                json.dump(user_data, f, indent=4)
                f.truncate()
        
            # 更新全局邀请码文件
            self._update_global_invites(table_name, owner_code, available_code)
        
            return {'success': True, 'message': '权限设置成功'}

        except Exception as e:
            return {'success': False, 'message': str(e)}

    
    def _generate_invite_code(self, table_name, invite_type):
        """生成唯一邀请码"""
        timestamp = str(time.time_ns())
        raw_str = f"{self.username}-{table_name}-{timestamp}"
        code = hashlib.sha3_256(raw_str.encode()).hexdigest()[:16]
        target_file = 'OwnerInvite.json' if invite_type == 'owner' else 'AvailableInvite.json'
        code_file = os.path.join(self.base_path, 'mpspdz', 'user_information', target_file)

        # 确保唯一性
        with open(code_file, 'r+') as f:
            codes = json.load(f) if os.path.getsize(code_file) > 0 else {}
            while code in codes:
                raw_str += str(time.time_ns())
                code = hashlib.sha3_256(raw_str.encode()).hexdigest()[:16]
            codes[code] = {
                "table": table_name,
                "owner": self.username,
                "type": invite_type
            }
            f.seek(0)
            json.dump(codes, f, indent=4)
        return code

    def _update_global_invites(self, table_name, owner_code, available_code):
        """更新全局邀请码文件"""
        # 更新 OwnerInvite.json
        owner_path = os.path.join(
            self.base_path, 'mpspdz', 'user_information', 'OwnerInvite.json'
        )
        with open(owner_path, 'r+') as f:
            owner_data = json.load(f) if os.path.getsize(owner_path) > 0 else {}
            owner_data[owner_code] = {
                "table": table_name,
                "generated_by": self.username,
                "permissions": "full"
            }
            f.seek(0)
            json.dump(owner_data, f, indent=4)

        # 更新 AvailableInvite.json
        available_path = os.path.join(
            self.base_path, 'mpspdz', 'user_information', 'AvailableInvite.json'
        )
        with open(available_path, 'r+') as f:
            available_data = json.load(f) if os.path.getsize(available_path) > 0 else {}
            available_data[available_code] = {
                "table": table_name,
                "generated_by": self.username,
                "permissions": "restricted"
            }
            f.seek(0)
            json.dump(available_data, f, indent=4)
