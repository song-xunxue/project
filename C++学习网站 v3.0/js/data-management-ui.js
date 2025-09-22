// 全局数据管理UI功能
(function() {
    // 确保页面完全加载
    function initWhenReady(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    }
    
    // 创建数据管理模态框
    function createDataManagementModal() {
        // 检查模态框是否已存在
        if (document.getElementById('data-management-modal')) return;
        
        // 创建模态框HTML
        const modalHtml = `
        <div id="data-management-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <span class="close-button">&times;</span>
                <h2>数据管理</h2>
                
                <div class="data-management-section">
                    <h3>导出完整数据</h3>
                    <p>将所有数据导出到本地文件，包括：用户账号、论坛帖子、答题记录、成就数据。可在其他浏览器中导入使用。</p>
                    <button id="export-users-btn" class="btn">导出完整数据</button>
                </div>
                
                <div class="data-management-section">
                    <h3>导入完整数据</h3>
                    <p>从本地文件导入所有数据，包括：用户账号、论坛帖子、答题记录、成就数据。将覆盖当前所有数据。</p>
                    <input type="file" id="import-users-file" accept=".json">
                    <button id="import-users-btn" class="btn">导入完整数据</button>
                </div>
                
                <div class="data-management-section">
                    <h3>重置为默认配置</h3>
                    <p>清除所有当前数据，恢复为网站的默认管理员帖子和配置。这将删除所有用户数据、自定义帖子和进度记录。</p>
                    <button id="reset-to-default-btn" class="btn btn-warning">重置为默认配置</button>
                </div>
            </div>
        </div>
        `;
        
        // 添加样式
        const styleHtml = `
        <style>
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                overflow: auto;
                background-color: rgba(0,0,0,0.4);
            }
            
            .modal-content {
                background-color: #fefefe;
                margin: 10% auto;
                padding: 20px;
                border: 1px solid #888;
                width: 90%;
                max-width: 600px;
                border-radius: 5px;
            }
            
            .close-button {
                color: #aaa;
                float: right;
                font-size: 28px;
                font-weight: bold;
                cursor: pointer;
            }
            
            .close-button:hover, .close-button:focus {
                color: black;
                text-decoration: none;
                cursor: pointer;
            }
            
            .data-management-section {
                margin-bottom: 20px;
                padding-bottom: 20px;
                border-bottom: 1px solid #ddd;
            }
            
            .data-management-section:last-child {
                border-bottom: none;
            }
            
            .data-management-section h3 {
                margin-top: 0;
                margin-bottom: 10px;
            }
            
            .data-management-section p {
                margin-bottom: 15px;
                color: #666;
            }
            
            #import-users-file {
                margin-bottom: 15px;
                display: block;
            }
            
            .btn {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 3px;
                cursor: pointer;
                font-size: 14px;
            }
            
            .btn:hover {
                background-color: #45a049;
            }
            
            .btn-warning {
                background-color: #ff9800;
            }
            
            .btn-warning:hover {
                background-color: #e68900;
            }
        </style>
        `;
        
        // 添加到页面
        document.head.insertAdjacentHTML('beforeend', styleHtml);
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // 获取模态框元素
        const modal = document.getElementById('data-management-modal');
        const closeButton = modal.querySelector('.close-button');
        const exportBtn = document.getElementById('export-users-btn');
        const importFileInput = document.getElementById('import-users-file');
        const importBtn = document.getElementById('import-users-btn');
        const resetBtn = document.getElementById('reset-to-default-btn');
        
        // 关闭模态框
        function closeModal() {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
        
        // 打开模态框
        window.openDataManagementModal = function() {
            modal.style.display = 'block';
            document.body.style.overflow = 'hidden';
        };
        
        // 绑定关闭事件
        closeButton.addEventListener('click', closeModal);
        
        // 点击外部关闭
        window.addEventListener('click', function(e) {
            if (e.target === modal) {
                closeModal();
            }
        });
        
        // 导出按钮点击事件
        exportBtn.addEventListener('click', function() {
            if (window.DataStorage && typeof window.DataStorage.exportUserData === 'function') {
                const success = window.DataStorage.exportUserData();
                if (success) {
                    showToast('完整数据导出成功（包含用户账号、论坛帖子、答题记录、成就数据）', 'success');
                } else {
                    showToast('数据导出失败', 'error');
                }
            } else {
                showToast('数据导出功能不可用', 'error');
            }
        });
        
        // 导入按钮点击事件
            importBtn.addEventListener('click', function() {
                const file = importFileInput.files[0];
                if (!file) {
                    showToast('请选择要导入的JSON文件', 'error');
                    return;
                }
                
                // 确认是否覆盖现有数据
                if (!confirm('导入数据将覆盖当前所有用户信息、论坛帖子、答题记录和成就数据，确定要继续吗？')) {
                    return;
                }
                
                // 保存当前用户信息（如果有）
                const originalCurrentUser = localStorage.getItem('currentUser');
                
                if (window.DataStorage && typeof window.DataStorage.importUserData === 'function') {
                    window.DataStorage.importUserData(file, function(success, message) {
                        if (success) {
                            // 使用更详细的成功消息
                            showToast(message || '完整数据导入成功（包含用户账号、论坛帖子、答题记录、成就数据）', 'success');
                            // 重置导入文件选择
                            importFileInput.value = '';
                            
                            // 尝试恢复原有的登录状态
                            if (originalCurrentUser) {
                                try {
                                    const parsedOriginalUser = JSON.parse(originalCurrentUser);
                                    const importedUsers = JSON.parse(localStorage.getItem('users') || '[]');
                                    
                                    // 检查导入的数据中是否包含原用户
                                    const userExists = importedUsers.some(user => user.username === parsedOriginalUser.username);
                                    
                                    if (userExists) {
                                        // 如果用户存在，保持登录状态
                                        localStorage.setItem('currentUser', originalCurrentUser);
                                    } else {
                                        // 如果用户不存在，清除登录状态
                                        localStorage.removeItem('currentUser');
                                    }
                                } catch (error) {
                                    console.error('恢复登录状态失败:', error);
                                }
                            }
                            
                            // 更新登录状态
                            if (window.updateLoginStatus && typeof window.updateLoginStatus === 'function') {
                                window.updateLoginStatus();
                            }
                            
                            // 触发登录状态变化事件，确保所有组件都能更新
                            const loginEvent = new CustomEvent('userLoginStateChanged', {
                                detail: {
                                    user: window.DataStorage ? window.DataStorage.loadCurrentUser() : null
                                }
                            });
                            document.dispatchEvent(loginEvent);
                            
                            // 触发数据导入完成事件，通知论坛模块刷新数据
                            const dataImportEvent = new CustomEvent('dataImported', {
                                detail: {
                                    message: '数据导入完成，论坛帖子已更新'
                                }
                            });
                            document.dispatchEvent(dataImportEvent);
                        } else {
                            showToast(`数据导入失败：${message || '未知错误'}`, 'error');
                        }
                    });
                } else {
                    showToast('数据导入功能不可用', 'error');
                }
            });
            
        // 重置按钮点击事件
        resetBtn.addEventListener('click', function() {
            if (!confirm('确定要重置为默认配置吗？这将清除所有当前数据，包括用户账号、论坛帖子、答题记录和成就数据，并恢复为默认的管理员帖子。此操作不可撤销！')) {
                return;
            }
            
            // 保存当前登录用户信息（如果有的话，稍后会被清除）
            const originalCurrentUser = localStorage.getItem('currentUser');
            
            // 清除所有数据
            const keysToRemove = [];
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key) {
                    keysToRemove.push(key);
                }
            }
            
            // 删除所有localStorage数据
            keysToRemove.forEach(key => localStorage.removeItem(key));
            
            if (window.DataStorage && typeof window.DataStorage.loadDefaultConfig === 'function') {
                showToast('正在重置为默认配置...', 'info');
                
                window.DataStorage.loadDefaultConfig()
                    .then(() => {
                        showToast('已成功重置为默认配置，页面将刷新以应用更改', 'success');
                        
                        // 关闭模态框
                        closeModal();
                        
                        // 延迟刷新页面以确保用户看到成功消息
                        setTimeout(() => {
                            window.location.reload();
                        }, 2000);
                    })
                    .catch(error => {
                        console.error('重置为默认配置失败:', error);
                        showToast('重置失败，请刷新页面重试', 'error');
                    });
            } else {
                showToast('重置功能不可用', 'error');
            }
        });
    }
    
    // 在导航栏添加数据管理链接
    function addDataManagementLink() {
        // 检查是否已经添加
        if (document.getElementById('data-management-link')) return;
        
        // 获取账户下拉菜单
        const dropdownMenu = document.querySelector('.dropdown-menu');
        if (!dropdownMenu) {
            // 如果找不到下拉菜单，500毫秒后重试
            setTimeout(addDataManagementLink, 500);
            return;
        }
        
        // 创建分隔线和数据管理链接
        const separator = document.createElement('li');
        separator.innerHTML = '<hr class="dropdown-divider">';
        
        const dataManagementItem = document.createElement('li');
        const dataManagementLink = document.createElement('a');
        dataManagementLink.href = '#';
        dataManagementLink.id = 'data-management-link';
        dataManagementLink.textContent = '数据管理';
        
        // 添加点击事件
        dataManagementLink.addEventListener('click', function(e) {
            e.preventDefault();
            if (window.openDataManagementModal && typeof window.openDataManagementModal === 'function') {
                window.openDataManagementModal();
            }
        });
        
        dataManagementItem.appendChild(dataManagementLink);
        
        // 添加到下拉菜单的末尾
        dropdownMenu.appendChild(separator);
        dropdownMenu.appendChild(dataManagementItem);
    }
    
    // 显示提示消息（如果没有showToast函数则创建）
    function showToast(message, type = 'info') {
        if (window.showToast && typeof window.showToast === 'function') {
            window.showToast(message, type);
            return;
        }
        
        // 创建临时提示消息
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        
        // 添加样式
        toast.style.position = 'fixed';
        toast.style.bottom = '20px';
        toast.style.right = '20px';
        toast.style.padding = '10px 15px';
        toast.style.borderRadius = '4px';
        toast.style.color = 'white';
        toast.style.zIndex = '10000';
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        
        // 根据类型设置背景色
        if (type === 'success') {
            toast.style.backgroundColor = 'rgba(76, 175, 80, 0.9)';
        } else if (type === 'error') {
            toast.style.backgroundColor = 'rgba(244, 67, 54, 0.9)';
        } else {
            toast.style.backgroundColor = 'rgba(33, 150, 243, 0.9)';
        }
        
        // 添加到页面
        document.body.appendChild(toast);
        
        // 显示提示
        setTimeout(() => {
            toast.style.opacity = '1';
        }, 10);
        
        // 3秒后隐藏
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 3000);
    }
    
    // 初始化函数
    function init() {
        // 创建数据管理模态框
        createDataManagementModal();
        
        // 立即添加数据管理链接，不需要登录
        addDataManagementLink();
        
        // 监听DOM变化，确保在动态生成的菜单中也能添加链接
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.addedNodes.length) {
                    // 检查是否添加了下拉菜单
                    if (document.querySelector('.dropdown-menu') && 
                        !document.getElementById('data-management-link')) {
                        addDataManagementLink();
                    }
                }
            });
        });
        
        // 监听文档变化
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    // 确保在页面加载后初始化
    initWhenReady(init);
})();