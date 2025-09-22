// 数据存储管理 - 用于跨浏览器共享用户数据

// 导出数据到本地文件（包含用户数据、论坛帖子、答题记录和成就数据）
function exportUserData() {
    try {
        // 获取所有用户数据
        const users = JSON.parse(localStorage.getItem('users') || '[]');
        
        // 获取论坛帖子数据
        const forumPosts = JSON.parse(localStorage.getItem('forumPosts') || '[]');
        
        // 获取所有用户的答题记录和成就数据
        const userQuizData = {};
        const userAchievements = {};
        
        users.forEach(user => {
            const username = user.username;
            
            // 导出用户答题记录
            const quizKey = `quizData_${username}`;
            const quizDataStr = localStorage.getItem(quizKey);
            if (quizDataStr) {
                try {
                    userQuizData[username] = JSON.parse(quizDataStr);
                } catch (error) {
                    console.warn(`解析用户 ${username} 的答题数据失败:`, error);
                }
            }
            
            // 导出用户成就数据
            const achievementKey = `achievements_${username}`;
            const achievementDataStr = localStorage.getItem(achievementKey);
            if (achievementDataStr) {
                try {
                    userAchievements[username] = JSON.parse(achievementDataStr);
                } catch (error) {
                    console.warn(`解析用户 ${username} 的成就数据失败:`, error);
                }
            }
        });
        
        // 创建数据对象
        const exportData = {
            users: users,
            forumPosts: forumPosts,
            userQuizData: userQuizData,
            userAchievements: userAchievements,
            exportTime: new Date().toISOString(),
            version: '2.6' // 更新版本标识
        };
        
        // 转换为JSON字符串并格式化
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        
        // 创建下载链接
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `cplusplus-learning-users-${new Date().toISOString().split('T')[0]}.json`;
        
        // 模拟点击下载
        document.body.appendChild(link);
        link.click();
        
        // 清理
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        return true;
    } catch (error) {
        console.error('导出用户数据失败:', error);
        return false;
    }
}

// 从本地文件导入数据（包含用户数据、论坛帖子、答题记录和成就数据）
function importUserData(file, callback) {
    const reader = new FileReader();
    
    reader.onload = function(event) {
        try {
            const importData = JSON.parse(event.target.result);
            
            // 验证数据格式
            if (!importData.users || !Array.isArray(importData.users)) {
                throw new Error('无效的数据格式：缺少用户数据');
            }
            
            console.log('开始导入数据，版本:', importData.version || '未知');
            
            // 保存用户数据到localStorage
            localStorage.setItem('users', JSON.stringify(importData.users));
            console.log(`成功导入 ${importData.users.length} 个用户账号`);
            
            // 保存论坛帖子数据到localStorage（如果存在）
            if (importData.forumPosts && Array.isArray(importData.forumPosts)) {
                localStorage.setItem('forumPosts', JSON.stringify(importData.forumPosts));
                console.log(`成功导入 ${importData.forumPosts.length} 个论坛帖子`);
            } else {
                // 如果导入的数据中没有论坛帖子，清空现有的帖子数据
                localStorage.setItem('forumPosts', JSON.stringify([]));
                console.log('导入数据中无论坛帖子，已清空现有帖子数据');
            }
            
            // 导入用户答题记录（如果存在）
            let quizDataCount = 0;
            if (importData.userQuizData && typeof importData.userQuizData === 'object') {
                Object.keys(importData.userQuizData).forEach(username => {
                    const quizKey = `quizData_${username}`;
                    const quizData = importData.userQuizData[username];
                    if (quizData) {
                        localStorage.setItem(quizKey, JSON.stringify(quizData));
                        quizDataCount++;
                    }
                });
                console.log(`成功导入 ${quizDataCount} 个用户的答题记录`);
            } else {
                console.log('导入数据中无用户答题记录');
            }
            
            // 导入用户成就数据（如果存在）
            let achievementDataCount = 0;
            if (importData.userAchievements && typeof importData.userAchievements === 'object') {
                Object.keys(importData.userAchievements).forEach(username => {
                    const achievementKey = `achievements_${username}`;
                    const achievementData = importData.userAchievements[username];
                    if (achievementData) {
                        localStorage.setItem(achievementKey, JSON.stringify(achievementData));
                        achievementDataCount++;
                    }
                });
                console.log(`成功导入 ${achievementDataCount} 个用户的成就数据`);
            } else {
                console.log('导入数据中无用户成就数据');
            }
            
            // 通知相关系统刷新数据
            // 触发用户登录状态变化事件，让题库系统重新加载数据
            if (window.dispatchEvent) {
                window.dispatchEvent(new CustomEvent('userLoginStateChanged'));
            }
            
            // 通知成就系统刷新数据
            if (window.AchievementSystem && typeof window.AchievementSystem.refreshUserData === 'function') {
                window.AchievementSystem.refreshUserData();
            }
            
            // 调用回调函数通知导入成功
            if (callback && typeof callback === 'function') {
                callback(true, `成功导入：${importData.users.length} 个用户、${importData.forumPosts ? importData.forumPosts.length : 0} 个帖子、${quizDataCount} 个答题记录、${achievementDataCount} 个成就数据`);
            }
            
        } catch (error) {
            console.error('导入数据失败:', error);
            if (callback && typeof callback === 'function') {
                callback(false, error.message);
            }
        }
    };
    
    reader.onerror = function() {
        console.error('文件读取失败');
        if (callback && typeof callback === 'function') {
            callback(false, '文件读取失败');
        }
    };
    
    // 开始读取文件
    reader.readAsText(file);
}

// 保存用户数据到localStorage
function saveUsersToLocalStorage(users) {
    try {
        localStorage.setItem('users', JSON.stringify(users));
        return true;
    } catch (error) {
        console.error('保存用户数据失败:', error);
        return false;
    }
}

// 从localStorage加载用户数据
function loadUsersFromLocalStorage() {
    try {
        return JSON.parse(localStorage.getItem('users') || '[]');
    } catch (error) {
        console.error('加载用户数据失败:', error);
        return [];
    }
}

// 从localStorage加载当前登录用户
function loadCurrentUser() {
    try {
        const currentUserStr = localStorage.getItem('currentUser');
        return currentUserStr ? JSON.parse(currentUserStr) : null;
    } catch (error) {
        console.error('加载当前用户失败:', error);
        return null;
    }
}

// 保存任意数据到localStorage
function saveData(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error(`保存${key}数据失败:`, error);
        return false;
    }
}

// 从localStorage加载任意数据
function loadData(key) {
    try {
        const dataStr = localStorage.getItem(key);
        return dataStr ? JSON.parse(dataStr) : null;
    } catch (error) {
        console.error(`加载${key}数据失败:`, error);
        return null;
    }
}

// 检查是否有用户数据
function hasUserData() {
    const users = loadUsersFromLocalStorage();
    return users && users.length > 0;
}

// 自动加载默认配置
function loadDefaultConfig() {
    return new Promise((resolve, reject) => {
        // 检测协议类型
        const isFileProtocol = window.location.protocol === 'file:';
        
        if (isFileProtocol) {
            // file://协议下，使用JavaScript版本的配置
            console.log('检测到file://协议，使用JavaScript配置文件...');
            
            // 检查是否已经加载了JavaScript配置
            if (window.DEFAULT_CONFIG) {
                processDefaultConfig(window.DEFAULT_CONFIG, resolve);
            } else {
                // 如果还没加载，等待一下再检查
                let attempts = 0;
                const maxAttempts = 10;
                const checkInterval = setInterval(() => {
                    attempts++;
                    if (window.DEFAULT_CONFIG) {
                        clearInterval(checkInterval);
                        processDefaultConfig(window.DEFAULT_CONFIG, resolve);
                    } else if (attempts >= maxAttempts) {
                        clearInterval(checkInterval);
                        console.warn('JavaScript配置文件加载超时，将使用空数据');
                        saveUsersToLocalStorage([]);
                        localStorage.setItem('forumPosts', JSON.stringify([]));
                        resolve(false);
                    }
                }, 100);
            }
        } else {
            // http://协议下，使用JSON文件
            console.log('检测到http://协议，使用JSON配置文件...');
            fetch('js/default-config.json')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('无法加载默认配置文件');
                    }
                    return response.json();
                })
                .then(defaultData => {
                    processDefaultConfig(defaultData, resolve);
                })
                .catch(error => {
                    console.warn('加载JSON配置失败，尝试使用JavaScript配置:', error);
                    // JSON加载失败时，尝试使用JavaScript配置作为备选
                    if (window.DEFAULT_CONFIG) {
                        processDefaultConfig(window.DEFAULT_CONFIG, resolve);
                    } else {
                        console.warn('JavaScript配置也不可用，将使用空数据');
                        saveUsersToLocalStorage([]);
                        localStorage.setItem('forumPosts', JSON.stringify([]));
                        resolve(false);
                    }
                });
        }
    });
}

// 处理默认配置数据的通用函数
function processDefaultConfig(defaultData, resolve) {
    console.log('开始加载默认配置...');
    
    // 保存用户数据到localStorage
    localStorage.setItem('users', JSON.stringify(defaultData.users));
    console.log(`成功加载 ${defaultData.users.length} 个默认用户账号`);
    
    // 保存论坛帖子数据到localStorage
    if (defaultData.forumPosts && Array.isArray(defaultData.forumPosts)) {
        localStorage.setItem('forumPosts', JSON.stringify(defaultData.forumPosts));
        console.log(`成功加载 ${defaultData.forumPosts.length} 个默认论坛帖子`);
    }
    
    // 保存其他数据（如果需要）
    if (defaultData.userQuizData && typeof defaultData.userQuizData === 'object') {
        Object.keys(defaultData.userQuizData).forEach(username => {
            const quizKey = `quizData_${username}`;
            const quizData = defaultData.userQuizData[username];
            if (quizData) {
                localStorage.setItem(quizKey, JSON.stringify(quizData));
            }
        });
    }
    
    if (defaultData.userAchievements && typeof defaultData.userAchievements === 'object') {
        Object.keys(defaultData.userAchievements).forEach(username => {
            const achievementKey = `achievements_${username}`;
            const achievementData = defaultData.userAchievements[username];
            if (achievementData) {
                localStorage.setItem(achievementKey, JSON.stringify(achievementData));
            }
        });
    }
    
    // 标记已加载默认配置
    localStorage.setItem('defaultConfigLoaded', 'true');
    
    // 通知相关系统刷新数据
    if (window.dispatchEvent) {
        window.dispatchEvent(new CustomEvent('userLoginStateChanged'));
    }
    
    // 通知论坛系统刷新数据
    const dataImportEvent = new CustomEvent('dataImported', {
        detail: {
            message: '默认配置已加载，论坛帖子已更新'
        }
    });
    document.dispatchEvent(dataImportEvent);
    
    console.log('默认配置加载完成');
    resolve(true);
}

// 检查是否需要加载默认配置
function shouldLoadDefaultConfig() {
    // 如果已经加载过默认配置，不再加载
    if (localStorage.getItem('defaultConfigLoaded') === 'true') {
        return false;
    }
    
    // 如果没有用户数据且没有论坛帖子数据，则需要加载默认配置
    const hasUsers = hasUserData();
    const forumPosts = JSON.parse(localStorage.getItem('forumPosts') || '[]');
    const hasForumPosts = forumPosts.length > 0;
    
    return !hasUsers && !hasForumPosts;
}

// 初始化数据存储系统
function initDataStorage() {
    // 检查是否需要加载默认配置
    if (shouldLoadDefaultConfig()) {
        console.log('检测到首次访问，正在加载默认配置...');
        return loadDefaultConfig();
    } else {
        console.log('数据存储系统已初始化');
        return Promise.resolve(true);
    }
}

// 导出函数供其他模块使用
window.DataStorage = {
    exportUserData,
    importUserData,
    saveUsersToLocalStorage,
    loadUsersFromLocalStorage,
    hasUserData,
    initDataStorage,
    loadCurrentUser,
    saveData,
    loadData,
    loadDefaultConfig,
    shouldLoadDefaultConfig
};