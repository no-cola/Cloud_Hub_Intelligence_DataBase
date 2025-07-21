document.addEventListener('DOMContentLoaded', function() {
    // 检查用户是否已登录
    checkLoginStatus();

    // 登录注册界面切换逻辑
    const tabs = document.querySelectorAll('.tab');
    const authForms = document.querySelectorAll('.auth-form');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // 移除所有激活状态
            tabs.forEach(t => t.classList.remove('active'));
            authForms.forEach(form => form.classList.remove('active'));
            
            // 添加激活状态
            this.classList.add('active');
            const formId = this.getAttribute('data-tab') + '-form';
            document.getElementById(formId).classList.add('active');
            
            // 清除消息
            document.getElementById('login-message').className = 'message';
            document.getElementById('login-message').textContent = '';
            document.getElementById('register-message').className = 'message';
            document.getElementById('register-message').textContent = '';
        });
    });
    
    // 登录表单处理
    const loginForm = document.getElementById('login-form');
    loginForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        
        if (!username || !password) {
            showMessage('login-message', '请填写所有字段', 'error');
            return;
        }
        
        // 显示loading状态
        const submitBtn = loginForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = '登录中...';
        submitBtn.disabled = true;

         // 发送到服务器验证
         fetch('/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            // 恢复按钮状态
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
            
            handleLoginResponse(data);
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('login-message', '登录失败，请稍后再试', 'error');
            
            // 恢复按钮状态
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
        });

    });
    
    // 注册表单处理
    const registerForm = document.getElementById('register-form');
    registerForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const username = document.getElementById('register-username').value.trim();
        const password = document.getElementById('register-password').value;
        const confirmPassword = document.getElementById('register-confirm-password').value;
        
        if (!username || !password || !confirmPassword) {
            showMessage('register-message', '请填写所有字段', 'error');
            return;
        }
        
        if (password !== confirmPassword) {
            showMessage('register-message', '两次密码输入不一致', 'error');
            return;
        }

        // 显示loading状态
        const submitBtn = registerForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = '注册中...';
        submitBtn.disabled = true;

        // 发送到服务器处理
        fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        })
        .then(response => response.json())
        .then(data => {
            // 恢复按钮状态
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
            
            if (data.success) {
                showMessage('register-message', data.message || '注册成功，请登录', 'success');
                registerForm.reset();
        
                // 切换到登录选项卡
                setTimeout(() => {
                    document.querySelector('.tab[data-tab="login"]').click();
                }, 1500);
            } else {
                showMessage('register-message', data.message || '注册失败', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('register-message', '注册失败，请稍后再试', 'error');
            
            // 恢复按钮状态
            submitBtn.textContent = originalBtnText;
            submitBtn.disabled = false;
        });
    });
    
    // 退出登录
    const logoutBtn = document.getElementById('logout-btn');
    logoutBtn.addEventListener('click', function() {
        // 发送请求到服务器注销
        fetch('/logout', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            logout();
        })
        .catch(error => {
            console.error('Error:', error);
            logout(); // 即使请求失败，也进行本地退出处理
        });
    });
    
    function handleLoginResponse(data) {
        if (data.success) {
            // 登录成功
            document.getElementById('current-user').textContent = '欢迎，' + data.username;
            
            // 隐藏登录界面，显示应用界面
            document.getElementById('auth-container').classList.add('hidden');
            document.getElementById('app-container').classList.remove('hidden');
            
            // 清除登录表单
            loginForm.reset();
        } else {
            showMessage('login-message', data.message || '用户名或密码错误', 'error');
        }
    }
    
    function logout() {
        // 显示登录界面，隐藏应用界面
        document.getElementById('auth-container').classList.remove('hidden');
        document.getElementById('app-container').classList.add('hidden');
        
        // 重置所有表单和消息
        loginForm.reset();
        registerForm.reset();
        document.getElementById('login-message').className = 'message';
        document.getElementById('login-message').textContent = '';
        document.getElementById('register-message').className = 'message';
        document.getElementById('register-message').textContent = '';
    }
    
     // 检查登录状态
     function checkLoginStatus() {
        fetch('/check_login')
        .then(response => response.json())
        .then(data => {
            if (data.loggedIn) {
                // 已登录，直接显示应用界面
                document.getElementById('current-user').textContent = '欢迎，' + data.username;
                document.getElementById('auth-container').classList.add('hidden');
                document.getElementById('app-container').classList.remove('hidden');
            }
        })
        .catch(error => {
            console.error('Error checking login status:', error);
        });
    }

    // Global variable to store temporary upload data
    let currentUploadData = null;

    // 页面切换逻辑
    const navLinks = document.querySelectorAll('.nav a');
    const pages = document.querySelectorAll('.page');

    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();

            // 移除所有激活状态
            navLinks.forEach(item => item.classList.remove('active'));
            pages.forEach(page => page.classList.remove('active'));

            // 添加激活状态到当前链接和页面
            this.classList.add('active');
            const pageId = this.getAttribute('data-page') + '-page';
            const targetPage = document.getElementById(pageId);
            if (targetPage) {
                targetPage.classList.add('active');
            }

            // Reset messages and specific page states
            resetMessages();
            document.getElementById('result-container').classList.add('hidden');
            // Hide permission form if navigating away from upload page
            document.getElementById('permission-settings-container').classList.add('hidden');
            document.getElementById('upload-container').classList.remove('hidden'); // Show upload form again

            // If navigating to Data Management, load tables
            if (pageId === 'data-management-page') {
                loadTableList();
            }
            // If navigating to My Stream Tasks, load tasks
            if (pageId === 'my-stream-tasks-page') {
                loadMyStreamTasks();
            }
        });
    });

    // 上传表格表单提交处理 - Modified
    const uploadForm = document.getElementById('upload-form');
    uploadForm.addEventListener('submit', function(e) {
        e.preventDefault();
        showMessage('upload-message', '', ''); // Clear previous message
        showMessage('permission-message', '', '');

        const formData = new FormData();
        const secret1 = document.getElementById('secret1').files[0];
        const secret2 = document.getElementById('secret2').files[0];
        const secret3 = document.getElementById('secret3').files[0];
        const tableInfo = document.getElementById('table_info').files[0];

        if (!secret1 || !secret2 || !secret3 || !tableInfo) {
            showMessage('upload-message', '请上传所有必需的文件', 'error');
            return;
        }
         if (tableInfo.type !== 'application/json') {
            showMessage('upload-message', '表信息文件必须是 .json 格式', 'error');
            return;
        }

        formData.append('secret1', secret1, 'Transactions-P0.data');
        formData.append('secret2', secret2, 'Transactions-P1.data');
        formData.append('secret3', secret3, 'Transactions-P2.data');
        formData.append('table_info', tableInfo, 'columns.json');

        // Show loading indicator (optional)
        const submitBtn = uploadForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = '上传中...';
        submitBtn.disabled = true;

        fetch('/upload_table', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            submitBtn.textContent = originalBtnText; // Restore button text
            submitBtn.disabled = false; // Re-enable button

            if (data.success) {
                showMessage('upload-message', data.message, 'success');
                // Store data needed for permission step
                currentUploadData = {
                    temp_id: data.temp_id,
                    columns: data.columns,
                    table_name: data.table_name
                };
                // Prepare and show permission form
                setupPermissionForm(currentUploadData.columns, currentUploadData.table_name);
                document.getElementById('upload-container').classList.add('hidden');
                document.getElementById('permission-settings-container').classList.remove('hidden');
                uploadForm.reset(); // Reset the upload form fields
            } else {
                showMessage('upload-message', data.message || '上传失败', 'error');
                currentUploadData = null; // Clear temp data on failure
                document.getElementById('upload-container').classList.remove('hidden');
                document.getElementById('permission-settings-container').classList.add('hidden');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            submitBtn.textContent = originalBtnText; // Restore button text
            submitBtn.disabled = false; // Re-enable button
            showMessage('upload-message', '上传失败，请稍后再试', 'error');
            currentUploadData = null; // Clear temp data on error
            document.getElementById('upload-container').classList.remove('hidden');
            document.getElementById('permission-settings-container').classList.add('hidden');
        });
    });


    // Permission form submission handler
    const permissionForm = document.getElementById('permission-form');
    permissionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        showMessage('permission-message', '', ''); // Clear previous message

        if (!currentUploadData || !currentUploadData.temp_id) {
            showMessage('permission-message', '无法提交权限，缺少上传信息。请重新上传。', 'error');
            return;
        }

        const permissions = [];
        const checkboxes = document.querySelectorAll('#column-permissions-list input[type="checkbox"]');
        checkboxes.forEach(checkbox => {
            permissions.push(checkbox.checked ? 0 : 1); // 0 if checked (restricted), 1 if unchecked (allowed)
        });

        const freeCountInput = document.getElementById('free-access-count');
        const priceInput = document.getElementById('price-per-access');
        const freeCount = parseInt(freeCountInput.value, 10);
        const price = parseFloat(priceInput.value);

        // Basic validation
        if (isNaN(freeCount) || freeCount < 0) {
            showMessage('permission-message', '请输入有效的非负整数作为免费次数。', 'error');
            freeCountInput.focus();
            return;
        }
        if (isNaN(price) || price < 0) {
            showMessage('permission-message', '请输入有效的非负数作为价格。', 'error');
            priceInput.focus();
            return;
        }


        const payload = {
            temp_id: currentUploadData.temp_id,
            permissions: permissions,
            free_count: freeCount,
            price: price
        };

        // Show loading indicator (optional)
        const submitBtn = permissionForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.textContent;
        submitBtn.textContent = '提交中...';
        submitBtn.disabled = true;


        fetch('/set_permissions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        })
        .then(response => response.json())
        .then(data => {
            submitBtn.textContent = originalBtnText; // Restore button
            submitBtn.disabled = false;

            if (data.success) {
                showMessage('permission-message', data.message || '权限设置成功！', 'success');
                // Hide permission form, show upload form again
                document.getElementById('permission-settings-container').classList.add('hidden');
                document.getElementById('upload-container').classList.remove('hidden');
                currentUploadData = null; // Clear temp data
                permissionForm.reset(); // Reset permission form fields
                 // Optionally, navigate to data management page
                // document.querySelector('.nav a[data-page="data-management"]').click();
            } else {
                showMessage('permission-message', data.message || '权限设置失败。', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
             submitBtn.textContent = originalBtnText; // Restore button
            submitBtn.disabled = false;
            showMessage('permission-message', '提交权限失败，请稍后再试。', 'error');
        });
    });

    // SQL查询表单提交处理
    const searchForm = document.getElementById('search-form');
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        showMessage('search-message', '', ''); // Clear message

        const sqlQuery = document.getElementById('sql-query').value.trim();

        if (!sqlQuery) {
            showMessage('search-message', '请输入SQL查询语句', 'error');
            return;
        }

        // 显示加载中
        document.getElementById('loading').classList.remove('hidden');
        document.getElementById('result-container').classList.add('hidden'); // Hide previous result

        fetch('/execute_query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: sqlQuery })
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById('loading').classList.add('hidden'); // 隐藏加载中

            if (data.success) {
                showMessage('search-message', data.message, 'success');
                document.getElementById('result-container').classList.remove('hidden'); // 显示下载结果区域
            } else {
                showMessage('search-message', data.message || '查询执行失败', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('loading').classList.add('hidden');
            showMessage('search-message', '查询执行失败，请稍后再试', 'error');
        });
    });

    function loadMyStreamTasks() {
        const container = document.getElementById('my-tasks-list-container');
        container.innerHTML = '<p>正在加载任务列表...</p>'; // Show loading state
        showMessage('my-tasks-message', '', ''); // Clear message

        fetch('/my_stream_tasks')
        .then(response => {
             if (!response.ok) {
                // Handle non-2xx responses, especially 401 Unauthorized
                if (response.status === 401) {
                    logout(); // Redirect to login if unauthorized
                    throw new Error('Unauthorized');
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.tasks) {
                if (data.tasks.length === 0) {
                    container.innerHTML = '<p>您还没有创建任何流式SQL任务。</p>';
                    return;
                }
                
                // Add tasks summary
                const summaryHtml = `
                    <div class="tasks-summary">
                        <h3>📊 当前共有 ${data.tasks.length} 个活跃的流式任务</h3>
                    </div>
                `;
                
                // Build task list HTML with enhanced structure
                let tasksHtml = summaryHtml + '<ul class="task-list">';
                data.tasks.forEach(task => {
                    const formattedTimeDisplay = formatCronTime(task.time_settings);
                    const createdAt = new Date(task.created_at).toLocaleString('zh-CN');
                    
                    tasksHtml += `
                        <li class="task-item" data-task-id="${task.id}">
                            <div class="task-header">
                                <div class="task-meta">
                                    <div class="task-status">活跃任务</div>
                                    <div class="task-time">
                                        <strong>执行时间:</strong> ${escapeHtml(formattedTimeDisplay)}
                                    </div>
                                </div>
                                <button class="btn delete-task-btn" data-task-id="${task.id}">删除任务</button>
                            </div>
                            <div class="task-details">
                                <p><strong>SQL语句:</strong></p>
                                <pre>${escapeHtml(task.query_text)}</pre>
                                <div class="task-script-info">
                                    <small>脚本文件: ${escapeHtml(task.script_name || 'N/A')}</small>
                                    <small style="margin-left: 20px;">创建时间: ${createdAt}</small>
                                </div>
                            </div>
                        </li>
                    `;
                });
                tasksHtml += '</ul>';
                container.innerHTML = tasksHtml;

                // Add event listeners for the new delete buttons
                addDeleteTaskListeners();

            } else {
                container.innerHTML = '<p>加载任务列表失败。</p>';
                showMessage('my-tasks-message', data.message || '无法获取任务信息', 'error');
                 if (data.redirect) { // Handle potential redirect flag from login_required
                    logout();
                }
            }
        })
        .catch(error => {
            console.error('Error loading stream tasks:', error);
             if (error.message !== 'Unauthorized') { // Avoid double message if already handled
                container.innerHTML = '<p>加载任务列表时出错。</p>';
                showMessage('my-tasks-message', '网络错误或权限问题，无法加载列表', 'error');
            }
        });
    }

    // Function to load and display the table list
    function loadTableList() {
        const container = document.getElementById('table-list-container');
        container.innerHTML = '<p>正在加载数据表列表...</p>'; // Show loading state
        showMessage('table-list-message', '', ''); // Clear message

        fetch('/list_tables')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.tables) {
                if (data.tables.length === 0) {
                    if (data.message && data.message.includes('用户数据文件不存在')) {
                        container.innerHTML = `<p>您似乎还没有上传或被授权访问任何数据表。请先在“上传表格”页面操作或使用邀请码。</p>`;
                    } else {
                        container.innerHTML = '<p>目前没有可管理的数据表。</p>';
                    }
                    return;
                }
                // Build table HTML
                let tableHtml = `
                    <table class="table-list">
                        <thead>
                            <tr>
                                <th>表名</th>
                                <th>类型</th>
                                <th>列名</th>
                                <th>行数</th>
                                <th>受限/可访问列</th>
                                <th>免费/剩余次数</th>
                                <th>价格/次</th>
                                <th>管理员邀请码</th>
                                <th>访问邀请码</th>
                            </tr>
                        </thead>
                        <tbody>
                `;
                data.tables.forEach(table => {
                    if (table.error) {
                        tableHtml += `
                            <tr>
                                <td colspan="9" class="error-row">加载表 ${escapeHtml(table.name || '未知')} 出错: ${escapeHtml(table.error)}</td>
                            </tr>
                        `;
                        return; // Skip to next table
                    }

                    if (table.type === 'owned') {
                        tableHtml += `
                            <tr>
                                <td>${escapeHtml(table.name)}</td>
                                <td>拥有的表</td>
                                <td title="${escapeHtml(table.columns ? table.columns.join(', ') : '')}">${escapeHtml(table.columns ? table.columns.join(', ').substring(0, 30) + (table.columns.join(', ').length > 30 ? '...' : '') : 'N/A')}</td>
                                <td>${escapeHtml(table.rows !== undefined ? table.rows : 'N/A')}</td>
                                <td title="${escapeHtml(table.restricted_columns ? table.restricted_columns.join(', ') : '')}">${escapeHtml(table.restricted_columns ? table.restricted_columns.join(', ').substring(0, 20) + (table.restricted_columns.join(', ').length > 20 ? '...' : '') : '无')}</td>
                                <td>${escapeHtml(table.base_free_access_count !== undefined ? table.base_free_access_count : 'N/A')}</td>
                                <td>${escapeHtml(table.price_per_access !== undefined ? table.price_per_access.toFixed(2) : 'N/A')}</td>
                                <td class="invite-code">${escapeHtml(table.owner_invite_code || 'N/A')}</td>
                                <td class="invite-code">${escapeHtml(table.available_invite_code || 'N/A')}</td>
                            </tr>
                        `;
                    } else if (table.type === 'accessible') {
                        tableHtml += `
                            <tr>
                                <td>${escapeHtml(table.name)}</td>
                                <td>可访问的表</td>
                                <td title="${escapeHtml(table.all_columns ? table.all_columns.join(', ') : '')}">${escapeHtml(table.all_columns ? table.all_columns.join(', ').substring(0, 30) + (table.all_columns.join(', ').length > 30 ? '...' : '') : 'N/A')}</td>
                                <td>N/A</td> {/* 行数通常不直接对受限访问者显示 */}
                                <td title="${escapeHtml(table.accessible_columns ? table.accessible_columns.join(', ') : '')}">${escapeHtml(table.accessible_columns ? table.accessible_columns.join(', ').substring(0, 20) + (table.accessible_columns.join(', ').length > 20 ? '...' : '') : 'N/A')}</td>
                                <td>${escapeHtml(table.remaining_access_count !== undefined ? table.remaining_access_count : 'N/A')}</td>
                                <td>${escapeHtml(table.price_per_access !== undefined ? table.price_per_access.toFixed(2) : 'N/A')}</td>
                                <td>N/A</td>
                                <td>N/A</td>
                            </tr>
                        `;
                    }
                });
                tableHtml += '</tbody></table>';
                container.innerHTML = tableHtml;

                // Add click-to-copy for invite codes
                document.querySelectorAll('.invite-code').forEach(codeElement => {
                    if (codeElement.textContent !== 'N/A' && codeElement.textContent.trim() !== '') {
                        codeElement.style.cursor = 'pointer';
                        codeElement.title = '点击复制邀请码';
                        codeElement.addEventListener('click', function() {
                            navigator.clipboard.writeText(this.textContent)
                                .then(() => {
                                    showMessage('table-list-message', `邀请码 "${this.textContent}" 已复制到剪贴板!`, 'success');
                                    setTimeout(() => showMessage('table-list-message', '', ''), 3000); // Clear message after 3s
                                })
                                .catch(err => {
                                    console.error('无法复制邀请码: ', err);
                                    showMessage('table-list-message', '复制邀请码失败。', 'error');
                                    setTimeout(() => showMessage('table-list-message', '', ''), 3000);
                                });
                        });
                    }
                });

            } else {
                container.innerHTML = '<p>加载数据表列表失败。</p>';
                showMessage('table-list-message', data.message || '无法获取数据表信息', 'error');
            }
        })
        .catch(error => {
            console.error('Error loading table list:', error);
            container.innerHTML = '<p>加载数据表列表时出错。</p>';
            showMessage('table-list-message', '网络错误，无法加载列表', 'error');
        });
    }

    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return unsafe;
        return unsafe
             .replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
             .replace(/"/g, "&quot;")
             .replace(/'/g, "&#039;");
     }

    // 新增：格式化 Cron 时间字符串的辅助函数
    function formatCronTime(cronString) {
        const parts = cronString.split(' ');
        if (parts.length < 5) return cronString; // Fallback for invalid format

        const minuteStr = parts[0];
        const hourStr = parts[1];
        const dayOfMonthStr = parts[2];
        const monthStr = parts[3];
        const dayOfWeekStr = parts[4];

        // P1: 月份部分 (x月)
        const p1_month = (monthStr === '*') ? '每月' : `${monthStr}月`;

        // P2: 日期/星期部分 (每周x / x日)
        let p2_dayweek;
        const weekMap = {
            '0': '日', '1': '一', '2': '二', '3': '三', '4': '四', '5': '五', '6': '六'
        };

        if (dayOfMonthStr === '*' && dayOfWeekStr === '*') {
            p2_dayweek = '每日';
        } else if (dayOfMonthStr !== '*') { // 特定日期，dayOfWeekStr 必须是 '*'
            p2_dayweek = `${dayOfMonthStr}日`;
        } else { // 特定星期，dayOfMonthStr 必须是 '*'
            p2_dayweek = `每周${weekMap[dayOfWeekStr] || dayOfWeekStr}`;
        }

        // P3: 小时部分 (x时)
        const p3_hour = (hourStr === '*') ? '每时' : `${hourStr}时`;
        // P4: 分钟部分 (x分)
        const p4_minute = (minuteStr === '*') ? '每分' : `${minuteStr}分`;

        // 组合成 "x月 每周x/x日 x时x分" 格式
        return `${p1_month} ${p2_dayweek} ${p3_hour}${p4_minute}`;
    }

    // 新增：Function to add event listeners to delete buttons
    function addDeleteTaskListeners() {
        const deleteButtons = document.querySelectorAll('.delete-task-btn');
        deleteButtons.forEach(button => {
            // Remove existing listener to prevent duplicates if list is reloaded
            button.replaceWith(button.cloneNode(true));
        });
        // Re-query buttons after cloning
        document.querySelectorAll('.delete-task-btn').forEach(button => {
             button.addEventListener('click', function() {
                const taskId = this.getAttribute('data-task-id');
                if (confirm(`确定要删除这个流式任务吗？`)) {
                    deleteStreamTask(taskId);
                }
            });
        });
    }


    // 新增：Function to handle deleting a stream task
    function deleteStreamTask(taskId) {
        showMessage('my-tasks-message', '正在删除任务...', ''); // Indicate processing

        fetch(`/delete_stream_task/${taskId}`, {
            method: 'DELETE',
        })
        .then(response => {
             if (!response.ok) {
                 if (response.status === 401) {
                    logout();
                    throw new Error('Unauthorized');
                }
                // Try to parse error message from JSON response body
                return response.json().then(errData => {
                    throw new Error(errData.message || `HTTP error! status: ${response.status}`);
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                showMessage('my-tasks-message', `${data.message}. Script name: ${data.deleted_script_name}`, 'success');
                // Remove the task item from the list visually
                const taskItem = document.querySelector(`.task-item[data-task-id="${taskId}"]`);
                if (taskItem) {
                    taskItem.remove();
                }
                 // Optional: Reload the list if needed, e.g., if the list becomes empty
                 const container = document.getElementById('my-tasks-list-container');
                 if (!container.querySelector('.task-item')) {
                     container.innerHTML = '<p>您还没有创建任何流式SQL任务。</p>';
                 }
            } else {
                showMessage('my-tasks-message', data.message || '删除任务失败', 'error');
                 if (data.redirect) { // Handle potential redirect flag
                    logout();
                }
            }
        })
        .catch(error => {
            console.error('Error deleting stream task:', error);
             if (error.message !== 'Unauthorized') {
                showMessage('my-tasks-message', `删除任务出错: ${error.message}`, 'error');
            }
        });
    }


    // Helper function to reset all message areas
    function resetMessages() {
         showMessage('login-message', '', '');
         showMessage('register-message', '', '');
         showMessage('upload-message', '', '');
         showMessage('permission-message', '', '');
         showMessage('search-message', '', '');
         showMessage('table-list-message', '', '');
         showMessage('stream-sql-message', '', ''); // Added for stream sql page
         showMessage('my-tasks-message', '', ''); // Added for my tasks page
    }

    // 辅助函数：显示消息 - Modified to handle different areas
    function showMessage(elementId, message, type) {
        const messageElement = document.getElementById(elementId);
        if (messageElement) {
            messageElement.textContent = message;
            // Reset classes first, then add the new type
            messageElement.className = 'message';
            if (type) {
                messageElement.classList.add(type);
            }
        } else {
            console.warn(`Message element with ID ${elementId} not found.`);
        }
    }

    // 流式SQL查询功能
    // 处理流式SQL查询表单提交
    const streamSqlForm = document.getElementById('stream-sql-form');
    streamSqlForm.addEventListener('submit', function(e) {
        e.preventDefault();
        showMessage('stream-sql-message', '', ''); // 清空消息

        // 获取表单数据
        const sqlQuery = document.getElementById('stream-sql-query').value.trim();
        const email = document.getElementById('email-address').value.trim();
        
        // 获取五个时间下拉框的值（按照分、时、日、月、周的顺序）
        const minute = document.getElementById('minute-select').value;
        const hour = document.getElementById('hour-select').value;
        const day = document.getElementById('day-select').value;
        const month = document.getElementById('month-select').value;
        const week = document.getElementById('week-select').value;
        
        // 检查日期和星期至少有一个为空
        if (day !== "" && week !== "") {
            showMessage('stream-sql-message', '日期和星期不能同时设置，必须有一个为空', 'error');
            return;
        }
        
        // 检查日期和星期不能同时为空
        if (day === "" && week === "") {
            showMessage('stream-sql-message', '日期和星期必须至少设置一个', 'error');
            return;
        }
        
        // 确定哪个字段为空（用于后端判断）
        const day_empty = day === "";
        const week_empty = week === "";
        
        // 组合时间设置（按照分、时、日、月、周的顺序）
        const timeSettings = `${minute} ${hour} ${day} ${month} ${week}`;

        // 简单验证
        if (!sqlQuery) {
            showMessage('stream-sql-message', '请输入SQL查询语句', 'error');
            return;
        }
        if (!email) {
            showMessage('stream-sql-message', '请输入有效的邮箱地址', 'error');
            return;
        }

        // 开始按钮变为加载状态
        const startBtn = document.querySelector('.stream-start-btn');
        const originalBtnText = startBtn.textContent;
        startBtn.textContent = '正在保存...';
        startBtn.disabled = true;

        // 发送请求到后端保存流式查询
        fetch('/save_stream_query', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                query: sqlQuery, 
                email: email,
                time_settings: timeSettings,
                day_empty: day_empty,
                week_empty: week_empty
            })
        })
        .then(response => response.json())
        .then(data => {
            startBtn.textContent = originalBtnText;
            startBtn.disabled = false;

            if (data.success) {
                // 显示成功消息
                showMessage('stream-sql-message', data.message || '流式查询已成功保存', 'success');
                // 重置表单
                streamSqlForm.reset();
            } else {
                showMessage('stream-sql-message', data.message || '保存流式查询失败', 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            startBtn.textContent = originalBtnText;
            startBtn.disabled = false;
            showMessage('stream-sql-message', '保存流式查询失败，请稍后再试', 'error');
        });
    });

    // 修改删除按钮功能
    const stopStreamBtn = document.querySelector('.stream-stop-btn');
    if (stopStreamBtn) {
        stopStreamBtn.textContent = '删除流式查询';
        stopStreamBtn.addEventListener('click', function() {
            showMessage('stream-sql-message', '删除功能暂未实现', 'error');
        });
    }

    // 隐藏不再需要的状态区域
    const streamStatus = document.getElementById('stream-status');
    if (streamStatus) {
        streamStatus.classList.add('hidden');
    }

    // Initial actions on load
    checkLoginStatus();
    // Optionally load table list if data management is the default view after login
    // loadTableList();

    const submitInviteCodeBtn = document.getElementById('submitInviteCodeBtn');
    if (submitInviteCodeBtn) {
        submitInviteCodeBtn.addEventListener('click', async function() {
            const inviteCodeInput = document.getElementById('inviteCodeInput');
            const inviteCodeMessage = document.getElementById('inviteCodeMessage');
            const inviteCode = inviteCodeInput.value.trim();

            // 重置消息显示
            inviteCodeMessage.style.display = 'none';
            inviteCodeMessage.className = 'message';
            inviteCodeMessage.innerHTML = ''; // 清空之前的内容

            if (!inviteCode) {
                showInviteMessage('请输入邀请码', 'error');
                return;
            }

            // 显示加载状态
            const originalBtnText = this.textContent;
            this.textContent = '验证中...';
            this.disabled = true;

            try {
                const response = await fetch('/add_table_by_invite', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ invite_code: inviteCode }),
                });

                const result = await response.json();

                // 恢复按钮状态
                this.textContent = originalBtnText;
                this.disabled = false;

                if (result.success) {
                    // 构建成功消息
                    let messageHTML = `<div class="invite-success-details">`;
                    messageHTML += `<h4>✅ 添加成功！</h4>`;
                    messageHTML += `<p><strong>表名：</strong>${escapeHtml(result.table_name)}</p>`;
                    messageHTML += `<p><strong>权限类型：</strong>${escapeHtml(result.permission_type)}</p>`;
                    messageHTML += `<p><strong>授权方：</strong>${escapeHtml(result.generated_by || '未知')}</p>`;
                    
                    if (result.permission_type === '受限访问权限') {
                        messageHTML += `<div class="permission-details">`;
                        messageHTML += `<p><strong>免费访问次数：</strong>${result.free_access_count}</p>`;
                        if (result.accessible_columns && result.accessible_columns.length > 0) {
                            messageHTML += `<p><strong>可访问列：</strong>${result.accessible_columns.join(', ')}</p>`;
                        }
                        if (result.restricted_columns && result.restricted_columns.length > 0) {
                            messageHTML += `<p><strong>受限列：</strong>${result.restricted_columns.join(', ')}</p>`;
                        }
                        messageHTML += `</div>`;
                    }
                    
                    messageHTML += `<p class="details-text">${escapeHtml(result.details || '')}</p>`;
                    messageHTML += `</div>`;
                    
                    inviteCodeMessage.innerHTML = messageHTML;
                    inviteCodeMessage.classList.add('success');
                    inviteCodeInput.value = ''; // 清空输入框

                    // 如果用户在数据管理页面，刷新表格列表
                    if (document.getElementById('data-management-page').classList.contains('active')) {
                        setTimeout(() => loadTableList(), 1500);
                    }
                } else {
                    // 构建错误消息
                    let messageHTML = `<div class="invite-error-details">`;
                    messageHTML += `<h4>❌ 添加失败</h4>`;
                    
                    if (result.table_name) {
                        messageHTML += `<p><strong>表名：</strong>${escapeHtml(result.table_name)}</p>`;
                    }
                    
                    if (result.permission_type) {
                        messageHTML += `<p><strong>权限类型：</strong>${escapeHtml(result.permission_type)}</p>`;
                    }
                    
                    // 根据错误类型显示不同的图标和描述
                    let errorIcon = '';
                    let errorDescription = '';
                    
                    switch (result.error_type) {
                        case 'duplicate':
                            errorIcon = '🔄';
                            errorDescription = '重复添加';
                            break;
                        case 'invalid_code':
                            errorIcon = '🔑';
                            errorDescription = '邀请码无效';
                            break;
                        case 'table_not_found':
                            errorIcon = '📁';
                            errorDescription = '表不存在';
                            break;
                        case 'already_owner':
                            errorIcon = '👑';
                            errorDescription = '已拥有更高权限';
                            break;
                        case 'metadata_error':
                            errorIcon = '⚠️';
                            errorDescription = '元数据错误';
                            break;
                        default:
                            errorIcon = '❗';
                            errorDescription = '未知错误';
                    }
                    
                    messageHTML += `<p><strong>${errorIcon} 错误类型：</strong>${errorDescription}</p>`;
                    messageHTML += `<p class="error-reason">${escapeHtml(result.message)}</p>`;
                    messageHTML += `</div>`;
                    
                    inviteCodeMessage.innerHTML = messageHTML;
                    inviteCodeMessage.classList.add('error');

                    if (result.redirect) {
                        alert("会话已过期或未登录，请重新登录。");
                        logout();
                    }
                }
                
                inviteCodeMessage.style.display = 'block';

            } catch (error) {
                console.error('Error submitting invite code:', error);
                
                // 恢复按钮状态
                this.textContent = originalBtnText;
                this.disabled = false;
                
                showInviteMessage('提交邀请码时发生网络错误，请检查网络连接后重试', 'error');
            }
        });
    }

    // 辅助函数：显示邀请码消息
    function showInviteMessage(message, type) {
        const inviteCodeMessage = document.getElementById('inviteCodeMessage');
        if (inviteCodeMessage) {
            inviteCodeMessage.innerHTML = `<p>${escapeHtml(message)}</p>`;
            inviteCodeMessage.className = `message ${type}`;
            inviteCodeMessage.style.display = 'block';
        }
    }

    // ...existing code...

function setupPermissionForm(columns, tableName) {
    const container = document.getElementById('permission-settings-container');
    container.innerHTML = `
        <div class="upload-container">
            <h3>设置数据访问权限 - ${tableName}</h3>
            <form id="permission-form">
                <div class="permissions-list">
                    ${columns.map((col, index) => `
                        <div class="permission-item">
                            <div class="column-permission">
                                <label>
                                    <input type="checkbox" name="permission_${index}" value="1" checked>
                                    允许访问列: <strong>${col}</strong>
                                </label>
                            </div>
                            <div class="method-selection hidden" id="method-selection-${index}">
                                <label class="method-label">选择允许的操作方法：</label>
                                <div class="method-tags">
                                    <label class="method-tag">
                                        <input type="checkbox" name="method_${index}" value="sum"> Sum
                                    </label>
                                    <label class="method-tag">
                                        <input type="checkbox" name="method_${index}" value="average"> Average
                                    </label>
                                    <label class="method-tag">
                                        <input type="checkbox" name="method_${index}" value="max"> Max
                                    </label>
                                    <label class="method-tag">
                                        <input type="checkbox" name="method_${index}" value="min"> Min
                                    </label>
                                    <label class="method-tag">
                                        <input type="checkbox" name="method_${index}" value="count"> Count
                                    </label>
                                    <label class="method-tag">
                                        <input type="checkbox" name="method_${index}" value="groupby"> Group By
                                    </label>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                <div class="pricing-settings">
                    <div class="form-group">
                        <label for="free-count">免费访问次数:</label>
                        <input type="number" id="free-count" min="0" value="10" required>
                    </div>
                    <div class="form-group">
                        <label for="price-per-access">每次访问价格 (元):</label>
                        <input type="number" id="price-per-access" min="0" step="0.01" value="1.00" required>
                    </div>
                </div>
                
                <button type="submit" class="btn">确认权限设置</button>
            </form>
        </div>
    `;

    // 添加权限切换事件监听
    columns.forEach((col, index) => {
        const checkbox = document.querySelector(`input[name="permission_${index}"]`);
        const methodSelection = document.getElementById(`method-selection-${index}`);
        
        checkbox.addEventListener('change', function() {
            if (this.checked) {
                // 允许访问，隐藏方法选择
                methodSelection.classList.add('hidden');
            } else {
                // 受限访问，显示方法选择
                methodSelection.classList.remove('hidden');
            }
        });

        const methodCheckboxes = document.querySelectorAll(`input[name="method_${index}"]`);
        methodCheckboxes.forEach(methodCheckbox => {
            methodCheckbox.addEventListener('change', function() {
                const label = this.closest('.method-tag');
                if (this.checked) {
                    label.classList.add('checked');
                } else {
                    label.classList.remove('checked');
                }
            });
        });
    });

    // 处理权限表单提交
    document.getElementById('permission-form').addEventListener('submit', function(e) {
        e.preventDefault();
        
        const permissions = [];
        const restrictedColumnMethods = {};
        const freeCount = document.getElementById('free-count').value;
        const price = document.getElementById('price-per-access').value;

        columns.forEach((col, index) => {
            const isAllowed = document.querySelector(`input[name="permission_${index}"]`).checked;
            permissions.push(isAllowed ? 1 : 0);
            
            // 如果是受限列，收集允许的方法
            if (!isAllowed) {
                const methodCheckboxes = document.querySelectorAll(`input[name="method_${index}"]:checked`);
                const allowedMethods = Array.from(methodCheckboxes).map(cb => cb.value);
                restrictedColumnMethods[col] = allowedMethods;
            }
        });

        // 提交权限设置
        fetch('/commit_permissions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                temp_id: currentUploadData.temp_id,
                permissions: permissions,
                free_count: parseInt(freeCount),
                price: parseFloat(price),
                restricted_column_methods: restrictedColumnMethods
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showMessage('permission-message', data.message, 'success');
                setTimeout(() => {
                    document.getElementById('permission-settings-container').classList.add('hidden');
                    document.getElementById('upload-container').classList.remove('hidden');
                    document.getElementById('upload-form').reset();
                }, 2000);
            } else {
                showMessage('permission-message', data.message, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showMessage('permission-message', '设置权限时发生错误', 'error');
        });
    });
}

// ...existing code...


});