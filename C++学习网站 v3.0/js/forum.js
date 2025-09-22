// 论坛功能实现

// DOM元素
const postForm = document.getElementById('post-form');
const notLoggedInMessage = document.getElementById('not-logged-in-message');
const postsList = document.getElementById('posts-list');
const toastMessage = document.getElementById('toast-message');

// 新增的DOM元素
const categoriesView = document.getElementById('categories-view');
const categoryDetailView = document.getElementById('category-detail-view');
const categoriesGrid = document.getElementById('categories-grid');
const backToCategoriesBtn = document.getElementById('back-to-categories');
const currentCategoryName = document.getElementById('current-category-name');
const currentCategoryDesc = document.getElementById('current-category-desc');
const sortFilter = document.getElementById('sort-filter');

// 帖子本地存储键
const POSTS_STORAGE_KEY = 'forumPosts';

// 用户头像映射（用户名 -> 头像文件名）
const USER_AVATARS = {
    'dongshaojun': 'dongshaojun_avatar.svg',
    'hushengyuan': 'hushengyuan_avatar.svg',
    'liwenyu': 'liwenyu_avatar.svg',
    'niyujun': 'niyujun_avatar.svg',
    'xiangzetao': 'xiangzetao_avatar.svg',
    'zhangyiqiao': 'zhangyiqiao_avatar.svg'
};

// 用户个人标语映射
const USER_SIGNATURES = {
    'dongshaojun': 'C++架构师 | 代码就是艺术',
    'hushengyuan': '算法工程师 | 用代码改变世界',
    'liwenyu': '后端开发 | 简洁代码之美',
    'niyujun': 'C++专家 | 性能优化达人',
    'xiangzetao': '全栈工程师 | 热爱技术分享',
    'zhangyiqiao': '系统架构师 | 追求代码极致'
};

// 分类配置
const FORUM_CATEGORIES = {
    'basic': {
        name: '基础问题',
        description: 'C++基础语法、概念解答，新手入门指导',
        icon: 'fas fa-graduation-cap',
        color: '#4CAF50'
    },
    'advanced': {
        name: '进阶讨论',
        description: '高级特性、设计模式、性能优化等深度技术讨论',
        icon: 'fas fa-rocket',
        color: '#FF9800'
    },
    'oop': {
        name: '面向对象',
        description: '类与对象、继承多态、RAII等面向对象编程',
        icon: 'fas fa-cubes',
        color: '#2196F3'
    },
    'stl': {
        name: 'STL库',
        description: 'STL容器、算法、迭代器使用技巧和源码解析',
        icon: 'fas fa-box',
        color: '#9C27B0'
    },
    'debug': {
        name: '调试与错误',
        description: '编译错误、运行时错误、调试技巧分享',
        icon: 'fas fa-bug',
        color: '#F44336'
    },
    'other': {
        name: '其他话题',
        description: '开发工具、学习心得、职场经验等其他相关话题',
        icon: 'fas fa-ellipsis-h',
        color: '#607D8B'
    }
};

// 当前浏览的分类
let currentCategory = null;

// 获取用户头像
function getUserAvatar(username) {
    // 首先尝试从用户数据中获取实际上传的头像
    let users = [];
    if (window.DataStorage && typeof window.DataStorage.loadUsersFromLocalStorage === 'function') {
        users = window.DataStorage.loadUsersFromLocalStorage();
    } else {
        // 降级方案：直接从localStorage获取
        users = JSON.parse(localStorage.getItem('users')) || [];
    }
    
    // 查找用户并获取头像
    const user = users.find(u => u.username === username);
    if (user && user.avatar) {
        return user.avatar; // 返回用户上传的头像（base64数据）
    }
    
    // 如果用户有对应的预设头像文件，返回头像路径
    if (USER_AVATARS[username]) {
        return `images/${USER_AVATARS[username]}`;
    }
    
    // 否则返回默认头像（使用用户名首字母）
    return `https://ui-avatars.com/api/?name=${encodeURIComponent(username)}&background=007bff&color=fff&size=40`;
}

// 获取用户个人标语
function getUserSignature(username) {
    // 首先尝试从用户数据中获取实际设置的个人标语
    let users = [];
    if (window.DataStorage && typeof window.DataStorage.loadUsersFromLocalStorage === 'function') {
        users = window.DataStorage.loadUsersFromLocalStorage();
    } else {
        // 降级方案：直接从localStorage获取
        users = JSON.parse(localStorage.getItem('users')) || [];
    }
    
    // 查找用户并获取个人标语
    const user = users.find(u => u.username === username);
    if (user && user.motto) {
        return user.motto; // 返回用户设置的个人标语
    }
    
    // 如果用户有预设的个人标语，返回预设标语
    if (USER_SIGNATURES[username]) {
        return USER_SIGNATURES[username];
    }
    
    // 否则返回默认标语
    return '热爱编程 | 持续学习';
}

// 自动调整textarea高度
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 300) + 'px'; // 最大高度300px
}

// 初始化论坛
function initForum() {
    // 检查登录状态
    checkUserLoginStatus();
    
    // 显示分类浏览界面
    showCategoriesView();
    
    // 添加事件监听器
    postForm.addEventListener('submit', handlePostSubmit);
    backToCategoriesBtn.addEventListener('click', showCategoriesView);
    if (sortFilter) {
        sortFilter.addEventListener('change', () => loadCategoryPosts(currentCategory));
    }
    
    // 为主帖内容textarea添加自动调整高度
    const postContentTextarea = document.getElementById('post-content');
    if (postContentTextarea) {
        postContentTextarea.addEventListener('input', function() {
            autoResizeTextarea(this);
        });
    }
    
    // 监听登录状态变化
    document.addEventListener('userLoginStateChanged', checkUserLoginStatus);
    
    // 监听数据导入事件，刷新论坛界面
    document.addEventListener('dataImported', function(event) {
        console.log('检测到数据导入事件，刷新论坛界面');
        // 重新渲染论坛界面以显示导入的帖子
        if (typeof showCategoriesView === 'function') {
            showCategoriesView();
        }
    });
}

// 检查用户登录状态
function checkUserLoginStatus() {
    let currentUser;
    
    // 优先使用DataStorage模块
    if (window.DataStorage && typeof window.DataStorage.loadCurrentUser === 'function') {
        currentUser = window.DataStorage.loadCurrentUser();
    } else {
        // 降级方案：直接使用localStorage
        const currentUserStr = localStorage.getItem('currentUser');
        currentUser = currentUserStr ? JSON.parse(currentUserStr) : null;
    }
    
    if (currentUser) {
        // 用户已登录，显示发帖表单
        postForm.style.display = 'block';
        notLoggedInMessage.style.display = 'none';
    } else {
        // 用户未登录，隐藏发帖表单
        postForm.style.display = 'none';
        notLoggedInMessage.style.display = 'block';
    }
}

// 处理帖子提交
function handlePostSubmit(e) {
    e.preventDefault();
    
    let currentUser;
    
    // 优先使用DataStorage模块
    if (window.DataStorage && typeof window.DataStorage.loadCurrentUser === 'function') {
        currentUser = window.DataStorage.loadCurrentUser();
    } else {
        // 降级方案：直接使用localStorage
        const currentUserStr = localStorage.getItem('currentUser');
        currentUser = currentUserStr ? JSON.parse(currentUserStr) : null;
    }
    
    // 再次检查登录状态，防止绕过前端检查
    if (!currentUser) {
        showToast('请先登录后再发布帖子', 'warning');
        return;
    }
    
    // 获取表单数据
    const title = document.getElementById('post-title').value.trim();
    const category = document.getElementById('post-category').value;
    const content = document.getElementById('post-content').value.trim();
    
    // 验证表单数据
    if (!title || !category || !content) {
        showToast('请填写完整的帖子信息', 'warning');
        return;
    }
    
    // 创建帖子对象
    const post = {
        id: Date.now(), // 使用时间戳作为唯一ID
        title: title,
        category: category,
        content: content,
        author: currentUser,
        createdAt: new Date().toISOString(),
        likes: [], // 喜欢该帖子的用户列表
        replies: [] // 回复列表
    };
    
    // 保存帖子
    savePost(post);
    
    // 清空表单
    postForm.reset();
    
    // 根据当前视图状态刷新界面
    if (currentCategory) {
        // 如果在分类详情页面，重新加载该分类的帖子
        loadCategoryPosts(currentCategory);
    } else {
        // 如果在分类浏览页面，重新生成分类卡片
        generateCategoryCards();
    }
    
    // 显示成功提示
    showToast('帖子发布成功！', 'success');
}

// 保存帖子到本地存储
function savePost(post) {
    // 获取现有帖子
    const posts = getPosts();
    
    // 添加新帖子到开头
    posts.unshift(post);
    
    // 保存到本地存储
    localStorage.setItem(POSTS_STORAGE_KEY, JSON.stringify(posts));
}

// 从本地存储获取帖子
function getPosts() {
    const postsJson = localStorage.getItem(POSTS_STORAGE_KEY);
    const posts = postsJson ? JSON.parse(postsJson) : [];
    
    // 确保每个帖子都有likes和replies字段（向后兼容）
    return posts.map(post => ({
        ...post,
        likes: post.likes || [],
        replies: post.replies || []
    }));
}

// 显示分类浏览界面
function showCategoriesView() {
    categoriesView.style.display = 'block';
    categoryDetailView.style.display = 'none';
    currentCategory = null;
    
    // 生成分类卡片
    generateCategoryCards();
}

// 显示分类详情界面
function showCategoryDetail(categoryKey) {
    categoriesView.style.display = 'none';
    categoryDetailView.style.display = 'block';
    currentCategory = categoryKey;
    
    // 更新分类信息
    const category = FORUM_CATEGORIES[categoryKey];
    currentCategoryName.textContent = category.name;
    currentCategoryDesc.textContent = category.description;
    
    // 加载该分类的帖子
    loadCategoryPosts(categoryKey);
}

// 生成分类卡片
function generateCategoryCards() {
    const posts = getPosts();
    categoriesGrid.innerHTML = '';
    
    Object.keys(FORUM_CATEGORIES).forEach(categoryKey => {
        const category = FORUM_CATEGORIES[categoryKey];
        const categoryPosts = posts.filter(post => post.category === categoryKey);
        const postCount = categoryPosts.length;
        
        // 获取最新帖子
        let latestPost = null;
        if (categoryPosts.length > 0) {
            latestPost = categoryPosts.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt))[0];
        }
        
        const cardElement = createCategoryCard(categoryKey, category, postCount, latestPost);
        categoriesGrid.appendChild(cardElement);
    });
}

// 创建分类卡片元素
function createCategoryCard(categoryKey, category, postCount, latestPost) {
    const cardDiv = document.createElement('div');
    cardDiv.className = 'category-card';
    cardDiv.setAttribute('data-category', categoryKey);
    
    // 格式化最新帖子时间
    let latestPostInfo = '';
    if (latestPost) {
        const date = new Date(latestPost.createdAt);
        const formattedDate = `${date.getMonth() + 1}-${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
        
        let authorName = '';
        if (typeof latestPost.author === 'object' && latestPost.author !== null) {
            authorName = latestPost.author.username || 'Unknown';
        } else if (typeof latestPost.author === 'string') {
            authorName = latestPost.author;
        } else {
            authorName = 'Unknown';
        }
        
        latestPostInfo = `
            <div class="latest-post">
                <span class="latest-post-title">${latestPost.title}</span>
                <span class="latest-post-meta">by ${authorName} · ${formattedDate}</span>
            </div>
        `;
    } else {
        latestPostInfo = `
            <div class="latest-post">
                <span class="no-posts">暂无帖子</span>
            </div>
        `;
    }
    
    cardDiv.innerHTML = `
        <div class="category-header">
            <div class="category-icon" style="background-color: ${category.color}">
                <i class="${category.icon}"></i>
            </div>
            <div class="category-info">
                <h3 class="category-name">${category.name}</h3>
                <p class="category-description">${category.description}</p>
            </div>
        </div>
        <div class="category-stats">
            <div class="post-count">
                <i class="fas fa-comment"></i>
                <span>${postCount} 个帖子</span>
            </div>
        </div>
        ${latestPostInfo}
    `;
    
    // 添加点击事件
    cardDiv.addEventListener('click', () => showCategoryDetail(categoryKey));
    
    return cardDiv;
}

// 加载分类帖子
function loadCategoryPosts(categoryKey) {
    const posts = getPosts();
    const categoryPosts = posts.filter(post => post.category === categoryKey);
    
    // 排序
    const sortType = sortFilter ? sortFilter.value : 'latest';
    if (sortType === 'latest') {
        categoryPosts.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    } else {
        categoryPosts.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
    }
    
    // 清空帖子列表
    postsList.innerHTML = '';
    
    // 如果没有帖子，显示提示信息
    if (categoryPosts.length === 0) {
        postsList.innerHTML = `
            <div class="no-posts-message">
                <p><i class="fas fa-comment-slash"></i> 该分类下暂无帖子，快来发布第一个帖子吧！</p>
            </div>
        `;
        return;
    }
    
    // 创建帖子元素并添加到列表
    categoryPosts.forEach(post => {
        const postElement = createPostElement(post);
        postsList.appendChild(postElement);
    });
}

// 格式化帖子内容，处理换行符
function formatPostContent(content) {
    if (!content) return '';
    
    // 转义HTML特殊字符，防止XSS攻击
    const escapeHtml = (text) => {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    };
    
    // 转义HTML并将换行符转换为<br>标签
    const escapedContent = escapeHtml(content);
    return escapedContent.replace(/\n/g, '<br>');
}

// 创建帖子元素
function createPostElement(post) {
    const postDiv = document.createElement('div');
    postDiv.className = 'post';
    
    // 格式化日期
    const date = new Date(post.createdAt);
    const formattedDate = `${date.getFullYear()}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    
    // 获取分类信息
    const category = FORUM_CATEGORIES[post.category];
    const categoryName = category ? category.name : '未分类';
    const categoryIcon = category ? category.icon : 'fas fa-question-circle';
    const categoryColor = category ? category.color : '#607D8B';
    
    // 获取作者信息
    let authorName = '';
    let authorAvatar = '';
    let authorSignature = '';
    
    if (typeof post.author === 'object' && post.author !== null) {
        // 如果author是用户对象，提取用户名
        authorName = post.author.username || 'Unknown';
    } else if (typeof post.author === 'string') {
        // 如果author是字符串，直接使用
        authorName = post.author;
    } else {
        // 其他情况使用默认值
        authorName = 'Unknown';
    }
    
    authorAvatar = getUserAvatar(authorName);
    authorSignature = getUserSignature(authorName);
    
    postDiv.innerHTML = `
        <div class="post-layout">
            <div class="post-author-section">
                <div class="author-avatar-container">
                    <img src="${authorAvatar}" alt="${authorName}" class="author-avatar">
                </div>
                <div class="author-info">
                    <div class="author-name">${authorName}</div>
                    <div class="author-signature">${authorSignature}</div>
                </div>
            </div>
            <div class="post-main">
                <div class="post-header">
                    <h3 class="post-title">${post.title}</h3>
                    <div class="post-meta">
                        <span class="post-date">
                            <i class="fas fa-clock"></i> ${formattedDate}
                        </span>
                        <span class="post-category" style="color: ${categoryColor}">
                            <i class="${categoryIcon}"></i> ${categoryName}
                        </span>
                    </div>
                </div>
                <div class="post-content">
                    <p>${formatPostContent(post.content)}</p>
                </div>
                ${post.replies && post.replies.length > 0 ? createRepliesSection(post.replies, post.id) : ''}
                <div class="post-actions">
                    <button class="action-btn like-btn" data-post-id="${post.id}">
                        <i class="${getLikeIconClass(post)}" id="like-icon-${post.id}"></i>
                        <span id="like-text-${post.id}">${getLikeText(post)}</span>
                        <span class="like-count" id="like-count-${post.id}">${post.likes ? post.likes.length : 0}</span>
                    </button>
                    <button class="action-btn reply-btn" data-post-id="${post.id}">
                        <i class="fas fa-reply"></i>
                        <span>回复</span>
                        <span class="reply-count">${post.replies ? post.replies.length : 0}</span>
                    </button>
                    ${getDeleteButtonHtml(post)}
                </div>
            </div>
        </div>
    `;
    
    // 添加事件监听器
    addPostEventListeners(postDiv, post);
    
    return postDiv;
}

// 获取当前用户是否喜欢了帖子
function getCurrentUser() {
    let currentUser;
    
    // 优先使用DataStorage模块
    if (window.DataStorage && typeof window.DataStorage.loadCurrentUser === 'function') {
        currentUser = window.DataStorage.loadCurrentUser();
    } else {
        // 降级方案：直接使用localStorage
        const currentUserStr = localStorage.getItem('currentUser');
        currentUser = currentUserStr ? JSON.parse(currentUserStr) : null;
    }
    
    return currentUser;
}

// 获取喜欢按钮的图标样式
function getLikeIconClass(post) {
    const currentUser = getCurrentUser();
    if (!currentUser || !post.likes) return 'far fa-heart';
    
    const isLiked = post.likes.some(user => user.username === currentUser.username);
    return isLiked ? 'fas fa-heart liked' : 'far fa-heart';
}

// 获取喜欢按钮的文本
function getLikeText(post) {
    const currentUser = getCurrentUser();
    if (!currentUser || !post.likes) return '喜欢';
    
    const isLiked = post.likes.some(user => user.username === currentUser.username);
    return isLiked ? '已喜欢' : '喜欢';
}

// 获取删除按钮HTML（仅对帖子作者显示）
function getDeleteButtonHtml(post) {
    const currentUser = getCurrentUser();
    if (!currentUser) return '';
    
    // 获取帖子作者用户名
    let postAuthorUsername = '';
    if (typeof post.author === 'object' && post.author !== null) {
        postAuthorUsername = post.author.username || '';
    } else if (typeof post.author === 'string') {
        postAuthorUsername = post.author;
    }
    
    // 只有当前用户是帖子作者时才显示删除按钮
    if (currentUser.username === postAuthorUsername) {
        return `
            <button class="action-btn delete-btn" data-post-id="${post.id}">
                <i class="fas fa-trash"></i>
                <span>删除</span>
            </button>
        `;
    }
    
    return '';
}

// 添加帖子事件监听器
function addPostEventListeners(postElement, post) {
    const likeBtn = postElement.querySelector('.like-btn');
    const replyBtn = postElement.querySelector('.reply-btn');
    const deleteBtn = postElement.querySelector('.delete-btn');
    
    // 喜欢按钮事件
    if (likeBtn) {
        likeBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleLike(post.id);
        });
    }
    
    // 回复按钮事件
    if (replyBtn) {
        replyBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            showReplyDialog(post.id);
        });
    }
    
    // 删除按钮事件
    if (deleteBtn) {
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            showDeleteConfirmDialog(post.id, post.title);
        });
    }
}

// 切换喜欢状态
function toggleLike(postId) {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        showToast('请先登录后再点赞', 'warning');
        return;
    }
    
    // 获取所有帖子
    const posts = getPosts();
    const postIndex = posts.findIndex(p => p.id == postId);
    
    if (postIndex === -1) {
        showToast('帖子不存在', 'error');
        return;
    }
    
    const post = posts[postIndex];
    
    // 初始化likes数组
    if (!post.likes) {
        post.likes = [];
    }
    
    // 检查用户是否已经喜欢了这个帖子
    const likeIndex = post.likes.findIndex(user => user.username === currentUser.username);
    
    if (likeIndex > -1) {
        // 取消喜欢
        post.likes.splice(likeIndex, 1);
        showToast('已取消喜欢', 'info');
    } else {
        // 添加喜欢
        post.likes.push({
            username: currentUser.username,
            likedAt: new Date().toISOString()
        });
        showToast('已喜欢', 'success');
    }
    
    // 保存更新后的帖子数据
    localStorage.setItem(POSTS_STORAGE_KEY, JSON.stringify(posts));
    
    // 更新UI
    updateLikeButton(postId, post);
}

// 更新喜欢按钮UI
function updateLikeButton(postId, post) {
    const likeIcon = document.getElementById(`like-icon-${postId}`);
    const likeText = document.getElementById(`like-text-${postId}`);
    const likeCount = document.getElementById(`like-count-${postId}`);
    
    if (likeIcon && likeText && likeCount) {
        likeIcon.className = getLikeIconClass(post);
        likeText.textContent = getLikeText(post);
        likeCount.textContent = post.likes ? post.likes.length : 0;
    }
}

// 显示回复对话框
function showReplyDialog(postId) {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        showToast('请先登录后再回复', 'warning');
        return;
    }
    
    // 创建回复对话框
    const replyDialog = document.createElement('div');
    replyDialog.className = 'reply-dialog-overlay';
    replyDialog.innerHTML = `
        <div class="reply-dialog">
            <div class="reply-dialog-header">
                <h3>回复帖子</h3>
                <button class="close-reply-dialog" onclick="closeReplyDialog()">&times;</button>
            </div>
            <div class="reply-dialog-body">
                <textarea id="reply-content" placeholder="请输入您的回复内容..." rows="4"></textarea>
            </div>
            <div class="reply-dialog-footer">
                <button class="btn btn-cancel" onclick="closeReplyDialog()">取消</button>
                <button class="btn btn-submit" onclick="submitReply(${postId})">发布回复</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(replyDialog);
    
    // 聚焦到文本框并添加自动调整高度功能
    const textarea = document.getElementById('reply-content');
    if (textarea) {
        textarea.focus();
        textarea.addEventListener('input', function() {
            autoResizeTextarea(this);
        });
    }
}

// 关闭回复对话框
function closeReplyDialog() {
    const dialog = document.querySelector('.reply-dialog-overlay');
    if (dialog) {
        document.body.removeChild(dialog);
    }
}

// 提交回复
function submitReply(postId) {
    const currentUser = getCurrentUser();
    const replyContent = document.getElementById('reply-content').value.trim();
    
    if (!replyContent) {
        showToast('请输入回复内容', 'warning');
        return;
    }
    
    // 获取所有帖子
    const posts = getPosts();
    const postIndex = posts.findIndex(p => p.id == postId);
    
    if (postIndex === -1) {
        showToast('帖子不存在', 'error');
        return;
    }
    
    const post = posts[postIndex];
    
    // 初始化replies数组
    if (!post.replies) {
        post.replies = [];
    }
    
    // 创建回复对象
    const reply = {
        id: Date.now(),
        content: replyContent,
        author: currentUser,
        createdAt: new Date().toISOString()
    };
    
    // 添加回复
    post.replies.push(reply);
    
    // 保存更新后的帖子数据
    localStorage.setItem(POSTS_STORAGE_KEY, JSON.stringify(posts));
    
    // 关闭对话框
    closeReplyDialog();
    
    // 刷新当前分类的帖子显示
    if (currentCategory) {
        loadCategoryPosts(currentCategory);
    }
    
    showToast('回复发布成功！', 'success');
}

// 显示删除确认对话框
function showDeleteConfirmDialog(postId, postTitle) {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        showToast('请先登录', 'warning');
        return;
    }
    
    // 创建删除确认对话框
    const deleteDialog = document.createElement('div');
    deleteDialog.className = 'delete-dialog-overlay';
    deleteDialog.innerHTML = `
        <div class="delete-dialog">
            <div class="delete-dialog-header">
                <h3>确认删除</h3>
                <button class="close-delete-dialog" onclick="closeDeleteDialog()">&times;</button>
            </div>
            <div class="delete-dialog-body">
                <div class="delete-warning">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>您确定要删除这个帖子吗？</p>
                </div>
                <div class="post-info">
                    <strong>帖子标题：</strong><span class="post-title-preview">${postTitle}</span>
                </div>
                <div class="delete-note">
                    <p><strong>注意：</strong>删除后将无法恢复，包括该帖子下的所有回复！</p>
                </div>
            </div>
            <div class="delete-dialog-footer">
                <button class="btn btn-cancel" onclick="closeDeleteDialog()">取消</button>
                <button class="btn btn-delete-confirm" onclick="confirmDeletePost(${postId})">确认删除</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(deleteDialog);
}

// 关闭删除确认对话框
function closeDeleteDialog() {
    const dialog = document.querySelector('.delete-dialog-overlay');
    if (dialog) {
        document.body.removeChild(dialog);
    }
}

// 确认删除帖子
function confirmDeletePost(postId) {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        showToast('请先登录', 'warning');
        return;
    }
    
    // 获取所有帖子
    const posts = getPosts();
    const postIndex = posts.findIndex(p => p.id == postId);
    
    if (postIndex === -1) {
        showToast('帖子不存在', 'error');
        closeDeleteDialog();
        return;
    }
    
    const post = posts[postIndex];
    
    // 验证权限：只有帖子作者才能删除
    let postAuthorUsername = '';
    if (typeof post.author === 'object' && post.author !== null) {
        postAuthorUsername = post.author.username || '';
    } else if (typeof post.author === 'string') {
        postAuthorUsername = post.author;
    }
    
    if (currentUser.username !== postAuthorUsername) {
        showToast('您只能删除自己发布的帖子', 'error');
        closeDeleteDialog();
        return;
    }
    
    // 删除帖子
    posts.splice(postIndex, 1);
    
    // 保存更新后的帖子数据
    localStorage.setItem(POSTS_STORAGE_KEY, JSON.stringify(posts));
    
    // 关闭对话框
    closeDeleteDialog();
    
    // 刷新界面
    if (currentCategory) {
        // 如果在分类详情页面，重新加载该分类的帖子
        loadCategoryPosts(currentCategory);
    } else {
        // 如果在分类浏览页面，重新生成分类卡片
        generateCategoryCards();
    }
    
    showToast('帖子删除成功！', 'success');
}

// 显示删除回复确认对话框
function showDeleteReplyConfirmDialog(postId, replyId, replyTitle) {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        showToast('请先登录', 'warning');
        return;
    }
    
    // 创建删除确认对话框
    const deleteDialog = document.createElement('div');
    deleteDialog.className = 'delete-dialog-overlay';
    deleteDialog.innerHTML = `
        <div class="delete-dialog">
            <div class="delete-dialog-header">
                <h3>删除回复确认</h3>
                <button class="close-delete-dialog" onclick="closeDeleteReplyDialog()">&times;</button>
            </div>
            <div class="delete-dialog-body">
                <div class="warning-icon">
                    <i class="fas fa-exclamation-triangle"></i>
                </div>
                <div class="warning-text">
                    <p><strong>此操作无法撤销！</strong></p>
                    <p>您确定要删除这条回复吗？</p>
                    <div class="reply-info">
                        <strong>回复内容：</strong>${replyTitle}
                    </div>
                </div>
            </div>
            <div class="delete-dialog-footer">
                <button class="btn btn-cancel" onclick="closeDeleteReplyDialog()">取消</button>
                <button class="btn btn-delete" onclick="confirmDeleteReply(${postId}, ${replyId})">确认删除</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(deleteDialog);
}

// 关闭删除回复确认对话框
function closeDeleteReplyDialog() {
    const dialog = document.querySelector('.delete-dialog-overlay');
    if (dialog) {
        document.body.removeChild(dialog);
    }
}

// 确认删除回复
function confirmDeleteReply(postId, replyId) {
    const currentUser = getCurrentUser();
    if (!currentUser) {
        showToast('请先登录', 'warning');
        return;
    }
    
    // 获取所有帖子
    const posts = getPosts();
    const postIndex = posts.findIndex(p => p.id == postId);
    
    if (postIndex === -1) {
        showToast('帖子不存在', 'error');
        closeDeleteReplyDialog();
        return;
    }
    
    const post = posts[postIndex];
    
    if (!post.replies || post.replies.length === 0) {
        showToast('回复不存在', 'error');
        closeDeleteReplyDialog();
        return;
    }
    
    // 查找要删除的回复
    const replyIndex = post.replies.findIndex(r => r.id == replyId);
    
    if (replyIndex === -1) {
        showToast('回复不存在', 'error');
        closeDeleteReplyDialog();
        return;
    }
    
    const reply = post.replies[replyIndex];
    
    // 检查权限：只有回复作者可以删除自己的回复
    const canDelete = (typeof reply.author === 'object' && reply.author.username === currentUser.username) ||
                     (typeof reply.author === 'string' && reply.author === currentUser.username);
    
    if (!canDelete) {
        showToast('您只能删除自己的回复', 'error');
        closeDeleteReplyDialog();
        return;
    }
    
    // 删除回复
    post.replies.splice(replyIndex, 1);
    
    // 保存更新后的数据
    localStorage.setItem(POSTS_STORAGE_KEY, JSON.stringify(posts));
    
    // 关闭对话框
    closeDeleteReplyDialog();
    
    // 刷新当前分类的帖子显示
    if (currentCategory) {
        loadCategoryPosts(currentCategory);
    }
    
    showToast('回复删除成功！', 'success');
}

// 创建回复区域HTML
function createRepliesSection(replies, postId) {
    const currentUser = getCurrentUser();
    const repliesHtml = replies.map(reply => {
        const date = new Date(reply.createdAt);
        const formattedDate = `${date.getMonth() + 1}-${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2, '0')}`;
        
        // 获取回复作者信息
        let authorName = '';
        if (typeof reply.author === 'object' && reply.author !== null) {
            authorName = reply.author.username || 'Unknown';
        } else if (typeof reply.author === 'string') {
            authorName = reply.author;
        } else {
            authorName = 'Unknown';
        }
        
        const authorAvatar = getUserAvatar(authorName);
        
        // 检查当前用户是否可以删除这个回复
        const canDelete = currentUser && 
                         ((typeof reply.author === 'object' && reply.author.username === currentUser.username) ||
                          (typeof reply.author === 'string' && reply.author === currentUser.username));
        
        const deleteButton = canDelete ? 
            `<button class="reply-delete-btn" onclick="showDeleteReplyConfirmDialog(${postId}, ${reply.id}, '${authorName}的回复')" title="删除回复">
                <i class="fas fa-trash-alt"></i>
            </button>` : '';
        
        return `
            <div class="reply-item">
                <div class="reply-author">
                    <img src="${authorAvatar}" alt="${authorName}" class="reply-avatar">
                    <div class="reply-author-info">
                        <div class="reply-author-name">${authorName}</div>
                        <div class="reply-date">${formattedDate}</div>
                    </div>
                    ${deleteButton}
                </div>
                <div class="reply-content">
                    <p>${formatPostContent(reply.content)}</p>
                </div>
            </div>
        `;
    }).join('');
    
    return `
        <div class="replies-section">
            <div class="replies-header">
                <h4>回复 (${replies.length})</h4>
            </div>
            <div class="replies-list">
                ${repliesHtml}
            </div>
        </div>
    `;
}


// 显示提示消息
function showToast(message, type = 'info') {
    const toastMessage = document.getElementById('toast-message');
    if (!toastMessage) return;
    
    // 先隐藏当前消息，避免消息重叠
    toastMessage.classList.remove('show');
    
    // 短暂延迟后显示新消息
    setTimeout(() => {
        // 设置消息内容和类型
        toastMessage.textContent = message;
        toastMessage.className = 'toast';
        toastMessage.classList.add(type);
        
        // 显示提示消息
        toastMessage.classList.add('show');
        
        // 3秒后隐藏提示消息
        setTimeout(() => {
            toastMessage.classList.remove('show');
        }, 3000);
    }, 100);
}

// 页面加载完成后初始化论坛
document.addEventListener('DOMContentLoaded', initForum);