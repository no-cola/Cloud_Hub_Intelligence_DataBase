document.getElementById('decrypt-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const fileInput = document.getElementById('zip-file');
    const file = fileInput.files[0];

    if (!file || !file.name.endsWith('.zip')) {
        alert('请上传ZIP文件');
        return;
    }

    const formData = new FormData();
    formData.append('zip-file', file);

    document.getElementById('loading').classList.remove('hidden');
    document.getElementById('preview-section').classList.add('hidden');
    document.getElementById('download-section').classList.add('hidden');

    try {
        const response = await fetch('/api/decrypt', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            // 显示文件信息
            document.getElementById('file-name').textContent = result.filename;
            
            // 解析CSV内容并生成表格
            const lines = result.preview.split('\n').filter(line => line.trim());
            document.getElementById('row-count').textContent = lines.length - 1;
            document.getElementById('col-count').textContent = lines[0].split(',').length;

            generateTable(result.preview);

            // 显示预览区域
            document.getElementById('preview-section').classList.remove('hidden');
            document.getElementById('download-section').classList.remove('hidden');

            // 滚动到预览区域
            document.getElementById('preview-section').scrollIntoView({ behavior: 'smooth' });
        } else {
            alert('解密失败: ' + result.message);
        }
    } catch (error) {
        alert('发生错误: ' + error.message);
    } finally {
        document.getElementById('loading').classList.add('hidden');
    }
});

// 生成CSV表格（与加密页面共用逻辑）
function generateTable(csvContent) {
    const lines = csvContent.split('\n').filter(line => line.trim());
    const table = document.getElementById('csv-table');
    table.innerHTML = '';

    if (lines.length === 0) return;

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
    const maxRows = Math.min(lines.length - 1, 100); // 限制最多100行

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

// 下载CSV文件
function downloadCSV() {
    window.location.href = '/api/download/decrypted';
}
