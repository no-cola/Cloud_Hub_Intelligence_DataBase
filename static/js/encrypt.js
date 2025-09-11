// 监听文件上传变化
document.getElementById('csv-file').addEventListener('change', handleFileUpload);

// 处理文件上传和预览
function handleFileUpload(event) {
    const file = event.target.files[0];
    
    if (!file) {
        return;
    }
    
    if (!file.name.endsWith('.csv')) {
        alert('请选择CSV文件');
        return;
    }
    
    // 显示加载状态
    document.getElementById('loading').classList.remove('hidden');
    
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const csvContent = e.target.result;
        
        // 解析CSV内容
        const lines = csvContent.split('\n').filter(line => line.trim());
        if (lines.length === 0) {
            alert('CSV文件为空');
            document.getElementById('loading').classList.add('hidden');
            return;
        }
        
        // 显示文件信息
        document.getElementById('file-name').textContent = file.name;
        document.getElementById('row-count').textContent = lines.length - 1; // 减去标题行
        document.getElementById('col-count').textContent = lines[0].split(',').length;
        
        // 生成表格
        generateTable(csvContent);
        
        // 隐藏加载状态，显示预览
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('preview-section').classList.remove('hidden');
        document.getElementById('result-section').classList.add('hidden');
    };
    
    reader.onerror = function() {
        alert('读取文件失败');
        document.getElementById('loading').classList.add('hidden');
    };
    
    reader.readAsText(file);
}

// 生成CSV表格
function generateTable(csvContent) {
    const lines = csvContent.split('\n').filter(line => line.trim());
    const table = document.getElementById('csv-table');
    
    // 清空表格
    table.innerHTML = '';
    
    // 创建表头
    const headers = lines[0].split(',').map(h => h.trim());
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    
    headers.forEach(header => {
        const th = document.createElement('th');
        th.textContent = header;
        headerRow.appendChild(th);
    });
    
    thead.appendChild(headerRow);
    table.appendChild(thead);
    
    // 创建表体
    const tbody = document.createElement('tbody');
    
    // 最多显示100行数据（防止大文件卡顿）
    const maxRows = Math.min(lines.length - 1, 100);
    
    for (let i = 1; i <= maxRows; i++) {
        const values = lines[i].split(',').map(v => v.trim());
        const row = document.createElement('tr');
        
        headers.forEach((_, index) => {
            const td = document.createElement('td');
            td.textContent = values[index] || '';
            row.appendChild(td);
        });
        
        tbody.appendChild(row);
    }
    
    table.appendChild(tbody);
    
    // 如果数据太多，添加提示
    if (lines.length - 1 > 100) {
        const info = document.createElement('div');
        info.style.textAlign = 'center';
        info.style.color = '#666';
        info.style.marginTop = '10px';
        info.textContent = `显示前100行，共${lines.length - 1}行数据`;
        document.getElementById('preview-section').appendChild(info);
    }
}

// 处理加密
document.getElementById('encrypt-btn').addEventListener('click', async () => {
    const fileInput = document.getElementById('csv-file');
    
    if (!fileInput.files[0]) {
        alert('请先选择CSV文件');
        return;
    }
    
    const formData = new FormData();
    formData.append('csv-file', fileInput.files[0]);
    
    // 显示加载状态
    document.getElementById('loading').classList.remove('hidden');
    
    try {
        const response = await fetch('/api/encrypt', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 显示加密结果
            document.getElementById('p0-result').textContent = result.p0_base64;
            document.getElementById('p1-result').textContent = result.p1_base64;
            document.getElementById('p2-result').textContent = result.p2_base64;
            document.getElementById('result-section').classList.remove('hidden');
            
            // 滚动到结果区域
            document.getElementById('result-section').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert('加密失败: ' + result.message);
        }
    } catch (error) {
        alert('发生错误: ' + error.message);
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
});

// 下载文件功能保持不变
function downloadFile(filename) {
    window.location.href = `/api/download/${filename}`;
}
