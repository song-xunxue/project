// main.js - 实现主题切换功能和目录跳转
document.addEventListener('DOMContentLoaded', function () {
    // 获取主题切换按钮（桌面端和移动端）
    const themeToggle = document.getElementById('theme-toggle');
    const mobileThemeToggle = document.getElementById('mobile-theme-toggle');

    // 检查本地存储中的主题偏好
    const currentTheme = localStorage.getItem('theme') || 'light';
    if (currentTheme === 'dark') {
        enableDarkMode();
        if (themeToggle) themeToggle.classList.add('dark-active');
        if (mobileThemeToggle) mobileThemeToggle.classList.add('dark-active');
    }

    // 主题切换功能
    function toggleTheme() {
        if (document.body.classList.contains('dark-theme')) {
            disableDarkMode();
            if (themeToggle) themeToggle.classList.remove('dark-active');
            if (mobileThemeToggle) mobileThemeToggle.classList.remove('dark-active');
        } else {
            enableDarkMode();
            if (themeToggle) themeToggle.classList.add('dark-active');
            if (mobileThemeToggle) mobileThemeToggle.classList.add('dark-active');
        }
    }

    // 桌面端主题切换按钮点击事件
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }

    // 移动端主题切换按钮点击事件
    if (mobileThemeToggle) {
        mobileThemeToggle.addEventListener('click', toggleTheme);
    }

    // 移动端菜单切换功能
    const burger = document.querySelector('.burger');
    const navLinks = document.querySelector('.nav-links');

    if (burger && navLinks) {
        // 打开/关闭菜单的函数
        function toggleMobileMenu() {
            navLinks.classList.toggle('nav-active');

            // 导航链接立即显示，无渐进式动画
            const navItems = document.querySelectorAll('.nav-links li');
            if (navLinks.classList.contains('nav-active')) {
                navItems.forEach((link, index) => {
                    // 移除动画，立即设置为可见
                    link.style.animation = '';
                    link.style.opacity = '1';
                });
                // 添加点击外部关闭的事件监听器
                setTimeout(() => {
                    document.addEventListener('click', closeMobileMenuOnClickOutside);
                }, 100);
            } else {
                navItems.forEach(link => {
                    link.style.animation = '';
                    link.style.opacity = '';
                });
                // 移除点击外部关闭的事件监听器
                document.removeEventListener('click', closeMobileMenuOnClickOutside);
            }

            // 汉堡菜单动画
            burger.classList.toggle('toggle');
        }

        // 关闭移动端菜单的函数
        function closeMobileMenu() {
            if (navLinks.classList.contains('nav-active')) {
                navLinks.classList.remove('nav-active');
                burger.classList.remove('toggle');
                
                // 关闭所有打开的下拉菜单
                document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                    menu.classList.remove('show');
                });
                
                // 重置动画
                const navItems = document.querySelectorAll('.nav-links li');
                navItems.forEach(link => {
                    link.style.animation = '';
                });
                
                // 移除点击外部关闭的事件监听器
                document.removeEventListener('click', closeMobileMenuOnClickOutside);
            }
        }

        // 点击外部关闭菜单的处理函数
        function closeMobileMenuOnClickOutside(e) {
            // 检查点击的元素是否在菜单内部或汉堡按钮上
            if (!navLinks.contains(e.target) && !burger.contains(e.target)) {
                // 关闭所有下拉菜单
                document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                    menu.classList.remove('show');
                });
                closeMobileMenu();
            }
        }

        // 汉堡菜单按钮点击事件
        burger.addEventListener('click', function (e) {
            e.stopPropagation(); // 防止事件冒泡
            toggleMobileMenu();
        });

        // 菜单链接点击后关闭菜单，但排除账户下拉菜单
        const navLinksItems = navLinks.querySelectorAll('a');
        navLinksItems.forEach(link => {
            link.addEventListener('click', function(e) {
                // 如果点击的是账户下拉菜单切换按钮，不关闭菜单
                if (link.classList.contains('dropdown-toggle')) {
                    e.preventDefault(); // 阻止默认的链接跳转
                    // 切换下拉菜单的显示状态
                    const dropdown = link.closest('.dropdown');
                    const dropdownMenu = dropdown.querySelector('.dropdown-menu');
                    
                    // 关闭其他可能打开的下拉菜单
                    document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                        if (menu !== dropdownMenu) {
                            menu.classList.remove('show');
                        }
                    });
                    
                    // 切换当前下拉菜单
                    dropdownMenu.classList.toggle('show');
                    return;
                }
                
                // 如果点击的是下拉菜单内的链接，关闭菜单
                if (link.closest('.dropdown-menu')) {
                    closeMobileMenu();
                    return;
                }
                
                // 其他普通链接点击后关闭菜单
                closeMobileMenu();
            });
        });
    }

    // 先检查登录状态
    checkLoginStatus();
    
    // 先加载模态框，然后再设置模态框功能
    loadModals()
        .then(() => {
            setupModals();
        })
        .catch(error => {
            console.error('Failed to initialize modals:', error);
            // 如果模态框加载失败，尝试使用备用方案 - 直接在页面上创建模态框
            createModalsFallback();
            setupModals();
        });

    // 添加CSS动画关键帧和深色主题样式
    addDarkThemeStyles();

    // 修复about页面的图片显示问题
    fixAboutPageImages();
    
    // 实现目录点击平滑跳转
    setupSmoothScroll();
    
    // 监听窗口大小变化，重新调整菜单宽度
    window.addEventListener('resize', function() {
        const currentUser = JSON.parse(localStorage.getItem('currentUser'));
        if (currentUser) {
            adjustMobileMenuWidth(currentUser.username);
        } else {
            adjustMobileMenuWidth('账户');
        }
    });
});

// 更新登录状态
function updateLoginStatus() {
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    const dropdownToggle = document.querySelector('.dropdown-toggle');
    const dropdownMenu = document.querySelector('.dropdown-menu');
    
    if (currentUser) {
        // 用户已登录
        dropdownToggle.innerHTML = `欢迎，${currentUser.username} <i class="fas fa-chevron-down"></i>`;
        dropdownMenu.innerHTML = `
            <li><a href="#" id="profile-link">个人资料</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a href="#" id="logout-link">退出登录</a></li>
        `;
        
        // 根据用户名长度动态调整移动端菜单宽度
        adjustMobileMenuWidth(currentUser.username);
        
        // 添加个人资料事件
        document.getElementById('profile-link').addEventListener('click', function(e) {
            e.preventDefault();
            openProfileModal();
        });
        
        // 添加退出登录事件
        document.getElementById('logout-link').addEventListener('click', function(e) {
            e.preventDefault();
            logout();
        });
    } else {
        // 用户未登录
        dropdownToggle.innerHTML = `账户 <i class="fas fa-chevron-down"></i>`;
        dropdownMenu.innerHTML = `
            <li><a href="#login-modal">登录</a></li>
            <li><a href="#register-modal">注册</a></li>
        `;
        
        // 重置为默认宽度
        adjustMobileMenuWidth('账户');
        
        // 重新绑定登录和注册链接的事件监听器
        setTimeout(() => {
            bindModalLinksEvents();
        }, 10);
    }
}

// 根据用户名长度动态调整移动端菜单宽度
// 功能说明：
// - 基础宽度：40% (适合短用户名如"账户")
// - 最大宽度：60% (防止菜单占用过多屏幕空间)
// - 动态计算：根据实际用户名文本宽度自动调整
// - 响应式：窗口大小变化时自动重新计算
function adjustMobileMenuWidth(username) {
    // 创建临时元素来测量文本宽度
    const tempElement = document.createElement('span');
    tempElement.style.visibility = 'hidden';
    tempElement.style.position = 'absolute';
    tempElement.style.fontSize = '1rem';
    tempElement.style.fontFamily = getComputedStyle(document.body).fontFamily;
    tempElement.textContent = `欢迎，${username}`;
    document.body.appendChild(tempElement);
    
    // 获取文本宽度
    const textWidth = tempElement.offsetWidth;
    document.body.removeChild(tempElement);
    
    // 计算所需的菜单宽度
    // 基础宽度: 40% (约320px在800px屏幕上)
    // 最大宽度: 60% (约480px在800px屏幕上)
    // 考虑菜单项的padding和其他元素
    const baseWidth = 40; // 基础宽度百分比
    const maxWidth = 60;  // 最大宽度百分比
    const minRequiredWidth = 200; // 最小需要的像素宽度
    const extraPadding = 100; // 额外的padding和图标空间
    
    // 根据文本宽度计算所需宽度百分比
    const viewportWidth = window.innerWidth;
    const requiredPixelWidth = Math.max(textWidth + extraPadding, minRequiredWidth);
    const requiredPercentage = (requiredPixelWidth / viewportWidth) * 100;
    
    // 限制在基础宽度和最大宽度之间
    const finalWidth = Math.min(Math.max(baseWidth, requiredPercentage), maxWidth);
    
    // 应用动态宽度
    const style = document.getElementById('dynamic-menu-style') || document.createElement('style');
    style.id = 'dynamic-menu-style';
    style.textContent = `
        @media screen and (max-width: 768px) {
            .nav-links {
                width: ${finalWidth}% !important;
                max-width: ${Math.min(480, requiredPixelWidth + 50)}px !important;
            }
        }
    `;
    
    if (!document.getElementById('dynamic-menu-style')) {
        document.head.appendChild(style);
    }
}

// 检查登录状态
function checkLoginStatus() {
    const currentUser = localStorage.getItem('currentUser');
    if (currentUser) {
        updateLoginStatus();
    }
}

// 绑定模态框链接的事件监听器
function bindModalLinksEvents() {
    // 获取模态框元素
    const loginModal = document.getElementById('login-modal');
    const registerModal = document.getElementById('register-modal');
    
    // 获取下拉菜单元素
    const dropdownMenu = document.querySelector('.dropdown-menu');
    if (!dropdownMenu) return;
    
    // 获取下拉菜单中的登录和注册链接
    const loginLinks = dropdownMenu.querySelectorAll('a[href="#login-modal"]');
    const registerLinks = dropdownMenu.querySelectorAll('a[href="#register-modal"]');
    
    // 为登录链接绑定事件
    loginLinks.forEach(link => {
        // 移除旧的事件监听器
        const newLink = link.cloneNode(true);
        link.parentNode.replaceChild(newLink, link);
        
        // 添加新的事件监听器
        newLink.addEventListener('click', function(e) {
            e.preventDefault();
            closeAllModals();
            if (loginModal) {
                loginModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            }
        });
    });
    
    // 为注册链接绑定事件
    registerLinks.forEach(link => {
        // 移除旧的事件监听器
        const newLink = link.cloneNode(true);
        link.parentNode.replaceChild(newLink, link);
        
        // 添加新的事件监听器
        newLink.addEventListener('click', function(e) {
            e.preventDefault();
            closeAllModals();
            if (registerModal) {
                registerModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            }
        });
    });
}

// 退出登录
function logout() {
    localStorage.removeItem('currentUser');
    showToast('已退出登录', 'info');
    updateLoginStatus();
    
    // 触发登录状态变化事件，让其他组件（如答题系统）知道用户已退出
    const event = new CustomEvent('userLoginStateChanged', {
        detail: {
            user: null
        }
    });
    document.dispatchEvent(event);
}

// 备用方案：直接创建模态框
function createModalsFallback() {
    
    // 登录模态框HTML - 使用与其他页面一致的样式类
    const loginModalHtml = `
    <div id="login-modal" class="modal">
        <div class="modal-content">
            <span class="close-button">&times;</span>
            <h2>用户登录</h2>
            <form id="login-form">
                <div class="form-group">
                    <label for="login-username">用户名</label>
                    <input type="text" id="login-username" name="username" required placeholder="请输入用户名">
                </div>
                <div class="form-group">
                    <label for="login-password">密码</label>
                    <input type="password" id="login-password" name="password" required placeholder="请输入密码">
                </div>
                <div class="form-options">
                    <label class="checkbox-label">
                        <input type="checkbox" id="remember-me" name="remember"> 记住我
                    </label>
                    <a href="#forgot-password-modal" class="forgot-password">忘记密码?</a>
                </div>
                <button type="submit" class="modal-btn">登录</button>
                <p class="register-link">还没有账号? <a href="#register-modal">立即注册</a></p>
            </form>
        </div>
    </div>
    `;
    
    // 注册模态框HTML - 使用与其他页面一致的样式类
    const registerModalHtml = `
    <div id="register-modal" class="modal">
        <div class="modal-content">
            <span class="close-button">&times;</span>
            <h2>用户注册</h2>
            <form id="register-form">
                <div class="form-group">
                    <label for="register-username">用户名</label>
                    <input type="text" id="register-username" name="username" required placeholder="请输入用户名">
                </div>
                <div class="form-group">
                    <label for="register-email">邮箱</label>
                    <input type="email" id="register-email" name="email" required placeholder="请输入邮箱">
                </div>
                <div class="form-group">
                    <label for="register-password">密码</label>
                    <input type="password" id="register-password" name="password" required placeholder="请输入密码">
                </div>
                <div class="form-group">
                    <label for="register-confirm-password">确认密码</label>
                    <input type="password" id="register-confirm-password" name="confirm-password" required placeholder="请确认密码">
                </div>
                <div class="form-options">
                    <label class="checkbox-label">
                        <input type="checkbox" id="agree-terms" name="agree-terms" required> 我同意<a href="#" class="terms-link">用户协议</a>和<a href="#" class="privacy-link">隐私政策</a>
                    </label>
                </div>
                <button type="submit" class="modal-btn">注册</button>
                <p class="login-link">已有账号? <a href="#login-modal">立即登录</a></p>
            </form>
        </div>
    </div>
    `;
    
    // 忘记密码模态框HTML - 使用与其他页面一致的样式类
    const forgotPasswordModalHtml = `
    <div id="forgot-password-modal" class="modal">
        <div class="modal-content">
            <span class="close-button">&times;</span>
            <h2>重置密码</h2>
            <form id="forgot-password-form">
                <div class="form-group">
                    <label for="forgot-email">邮箱</label>
                    <input type="email" id="forgot-email" name="email" required placeholder="请输入注册邮箱">
                </div>
                <div class="form-group">
                    <label for="forgot-new-password">新密码</label>
                    <input type="password" id="forgot-new-password" name="new-password" required placeholder="请输入新密码">
                </div>
                <div class="form-group">
                    <label for="forgot-confirm-password">确认新密码</label>
                    <input type="password" id="forgot-confirm-password" name="confirm-password" required placeholder="请确认新密码">
                </div>
                <button type="submit" class="modal-btn">重置密码</button>
                <p class="login-link">想起密码了? <a href="#login-modal">立即登录</a></p>
            </form>
        </div>
    </div>
    `;
    
    // 将模态框添加到页面
    document.body.insertAdjacentHTML('beforeend', loginModalHtml);
    document.body.insertAdjacentHTML('beforeend', registerModalHtml);
    document.body.insertAdjacentHTML('beforeend', forgotPasswordModalHtml);
    
}

// 实现平滑滚动功能
function setupSmoothScroll() {
    // 为目录中的所有链接添加点击事件
    const navLinks = document.querySelectorAll('.tutorial-nav a');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault(); // 阻止默认的跳转行为
            
            // 获取目标元素的id
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                // 计算滚动位置（考虑页面头部高度）
                const headerHeight = document.querySelector('header')?.offsetHeight || 0;
                const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerHeight - 20;
                
                // 平滑滚动到目标位置
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// 启用深色主题
function enableDarkMode() {
    document.body.classList.add('dark-theme');
    localStorage.setItem('theme', 'dark');

    // 修复导航栏颜色
    const header = document.querySelector('header');
    if (header) {
        header.style.backgroundColor = '#2d3748';
    }

    // 修复其他区块颜色
    fixDarkModeElements();
}

// 禁用深色主题
function disableDarkMode() {
    document.body.classList.remove('dark-theme');
    localStorage.setItem('theme', 'light');

    // 恢复导航栏颜色
    const header = document.querySelector('header');
    if (header) {
        header.style.backgroundColor = '';
    }

    // 恢复其他区块颜色
    restoreLightModeElements();
}

// 添加深色主题样式 - 此函数已移除，现在使用第二个更完整的版本（第1720行附近）

// 修复深色模式下的元素显示
function fixDarkModeElements() {
    // 修复导航栏颜色
    const header = document.querySelector('header');
    if (header) {
        header.style.backgroundColor = '#2d3748';
    }

    // 修复特性区域
    const features = document.querySelector('.features');
    if (features) {
        features.style.backgroundColor = '#2d3748';
    }

    // 修复学习反馈区域
    const testimonials = document.querySelector('.testimonials');
    if (testimonials) {
        testimonials.style.backgroundColor = '#1a202c';
    }

    // 修复页脚
    const footer = document.querySelector('footer');
    if (footer) {
        footer.style.backgroundColor = '#2d3748';
        footer.style.color = '#e2e8f0';
    }
}

// 恢复浅色模式下的元素显示
function restoreLightModeElements() {
    // 恢复导航栏颜色
    const header = document.querySelector('header');
    if (header) {
        header.style.backgroundColor = '';
    }

    // 恢复特性区域
    const features = document.querySelector('.features');
    if (features) {
        features.style.backgroundColor = '';
    }

    // 恢复学习反馈区域
    const testimonials = document.querySelector('.testimonials');
    if (testimonials) {
        testimonials.style.backgroundColor = '';
    }

    // 恢复页脚
    const footer = document.querySelector('footer');
    if (footer) {
        footer.style.backgroundColor = '';
        footer.style.color = '';
    }
}


// 8.31 测试 修复about页面的图片显示问题
function fixAboutPageImages() {
    // 检查当前页面是否为about页面
    if (window.location.pathname.includes('about.html')) {
        // 添加about页面特定的深色模式样式
        const aboutStyle = document.createElement('style');
        aboutStyle.textContent = `
            body.dark-theme .about-content {
                color: #e2e8f0;
            }
            
            body.dark-theme .about-section {
                background-color: #2d3748;
            }
            
            /* 确保图片在深色模式下仍然可见 */
            body.dark-theme img {
                filter: brightness(0.8);
            }
        `;
        document.head.appendChild(aboutStyle);
    }
}

// 9.1添加功能

// 页面加载动画
// 页面加载动画
window.addEventListener('load', function () {
    const loader = document.getElementById('loader');
    if (loader) {
        setTimeout(function () {
            loader.style.opacity = '0';
            setTimeout(function () {
                loader.style.display = 'none';
            }, 500);
        }, 1500);
    }

    // 北京时间显示器 - 仅在元素存在时执行
    function setupBeijingTimeDisplay() {
        const counterElement = document.getElementById('learning-counter');
        const dateElement = document.getElementById('learning-date');
        
        // 只有在元素存在时才设置时间显示
        if (counterElement && dateElement) {
            function updateBeijingTime() {
                const now = new Date();

                // 转换为北京时间 (UTC+8)
                const utc = now.getTime() + (now.getTimezoneOffset() * 60000);
                const beijingTime = new Date(utc + (3600000 * 8));

                // 格式化时间
                const hours = beijingTime.getHours().toString().padStart(2, '0');
                const minutes = beijingTime.getMinutes().toString().padStart(2, '0');
                const seconds = beijingTime.getSeconds().toString().padStart(2, '0');

                // 格式化日期
                const year = beijingTime.getFullYear();
                const month = (beijingTime.getMonth() + 1).toString().padStart(2, '0');
                const day = beijingTime.getDate().toString().padStart(2, '0');
                const weekdays = ["日", "一", "二", "三", "四", "五", "六"];
                const weekday = weekdays[beijingTime.getDay()];

                // 更新显示
                counterElement.innerHTML = `${hours}:${minutes}:${seconds}`;
                dateElement.innerHTML = `${year}-${month}-${day} 星期${weekday}`;
            }

            // 初始更新并设置定时器
            updateBeijingTime();
            setInterval(updateBeijingTime, 1000);
        }
    }

    // 设置北京时间显示
    setupBeijingTimeDisplay();

    // 先加载模态框，然后再设置模态框功能
    loadModals()
        .then(() => {
            setupModals();
            checkLoginStatus();
        })
        .catch(error => {
            console.error('Failed to initialize modals:', error);
        });
});

// 动态加载模态框
function loadModals() {
    return new Promise((resolve, reject) => {
        // 检查是否在file://协议下运行
        const isFileProtocol = window.location.protocol === 'file:';
        
        // 如果是file://协议，直接使用备用方案创建模态框，避免CORS问题
        if (isFileProtocol) {
            createEmergencyFallbackModals();
            resolve();
            return;
        }
        
        // 获取当前页面的基础路径，确保相对路径正确
        const currentPath = window.location.pathname;
        let modalsPath;
        
        // 判断当前是否在content目录下
        if (currentPath.includes('/content/')) {
            // 在content目录下，直接使用modals.html
            modalsPath = 'modals.html';
        } else {
            // 在根目录或其他目录，使用content/modals.html
            modalsPath = 'content/modals.html';
        }
        
        
        // 方法1: 使用fetch异步加载
        fetch(modalsPath, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'text/html'
            }
        })
            .then(response => {
                if (!response.ok) {
                    console.warn('Fetch failed, trying fallback method');
                    throw new Error(`Failed to load modals.html: ${response.status} ${response.statusText}`);
                }
                return response.text();
            })
            .then(html => {
                processModalHtml(html, resolve, reject);
            })
            .catch(error => {
                console.error('Error loading modals with fetch:', error);
                // 方法2: 备用同步加载方式
                try {
                    const xhr = new XMLHttpRequest();
                    xhr.open('GET', modalsPath, false); // 同步请求
                    xhr.send();
                    
                    if (xhr.status === 200) {
                        processModalHtml(xhr.responseText, resolve, reject);
                    } else {
                        throw new Error(`Sync XHR failed: ${xhr.status} ${xhr.statusText}`);
                    }
                } catch (syncError) {
                    console.error('Both loading methods failed:', syncError);
                    // 方法3: 最后的备用方案 - 直接在页面上创建必要的模态框
                    createEmergencyFallbackModals();
                    resolve();
                }
            });
    });
}

// 处理模态框HTML内容
function processModalHtml(html, resolve, reject) {
    try {
        if (!html || html.trim() === '') {
            throw new Error('modals.html is empty');
        }
        
        // 提取<body>标签内的内容
        const bodyStart = html.indexOf('<body>') + 6;
        const bodyEnd = html.lastIndexOf('</body>');
        
        // 如果找不到body标签，就使用整个HTML内容
        let bodyContent;
        if (bodyStart === -1 || bodyEnd === -1 || bodyStart >= bodyEnd) {
            console.warn('No valid body tag found, using entire HTML content');
            bodyContent = html;
        } else {
            bodyContent = html.substring(bodyStart, bodyEnd);
        }
        
        if (!bodyContent || bodyContent.trim() === '') {
            throw new Error('Body content is empty');
        }
        

        // 将模态框添加到当前页面的body末尾
        document.body.insertAdjacentHTML('beforeend', bodyContent);
        resolve();
    } catch (error) {
        console.error('Error processing modal HTML:', error);
        reject(error);
    }
}

// 紧急备用方案：直接创建必要的模态框
function createEmergencyFallbackModals() {
    
    // 检查是否已存在模态框
    if (document.getElementById('login-modal') && document.getElementById('register-modal')) {
        return;
    }
    
    // 登录模态框HTML - 使用与其他页面一致的样式类
    const loginModalHtml = `
    <div id="login-modal" class="modal">
        <div class="modal-content">
            <span class="close-button">&times;</span>
            <h2>用户登录</h2>
            <form id="login-form">
                <div class="form-group">
                    <label for="login-username">用户名</label>
                    <input type="text" id="login-username" name="username" required placeholder="请输入用户名">
                </div>
                <div class="form-group">
                    <label for="login-password">密码</label>
                    <input type="password" id="login-password" name="password" required placeholder="请输入密码">
                </div>
                <div class="form-options">
                    <label class="checkbox-label">
                        <input type="checkbox" id="remember-me" name="remember"> 记住我
                    </label>
                    <a href="#forgot-password-modal" class="forgot-password">忘记密码?</a>
                </div>
                <button type="submit" class="modal-btn">登录</button>
                <p class="register-link">还没有账号? <a href="#register-modal">立即注册</a></p>
            </form>
        </div>
    </div>`;
    
    // 注册模态框HTML - 使用与其他页面一致的样式类
    const registerModalHtml = `
    <div id="register-modal" class="modal">
        <div class="modal-content">
            <span class="close-button">&times;</span>
            <h2>用户注册</h2>
            <form id="register-form">
                <div class="form-group">
                    <label for="register-username">用户名</label>
                    <input type="text" id="register-username" name="username" required placeholder="请输入用户名">
                </div>
                <div class="form-group">
                    <label for="register-email">邮箱</label>
                    <input type="email" id="register-email" name="email" required placeholder="请输入邮箱">
                </div>
                <div class="form-group">
                    <label for="register-password">密码</label>
                    <input type="password" id="register-password" name="password" required placeholder="请输入密码">
                </div>
                <div class="form-group">
                    <label for="register-confirm-password">确认密码</label>
                    <input type="password" id="register-confirm-password" name="confirm-password" required placeholder="请确认密码">
                </div>
                <div class="form-options">
                    <label class="checkbox-label">
                        <input type="checkbox" id="agree-terms" name="agree-terms" required> 我同意<a href="#" class="terms-link">用户协议</a>和<a href="#" class="privacy-link">隐私政策</a>
                    </label>
                </div>
                <button type="submit" class="modal-btn">注册</button>
                <p class="login-link">已有账号? <a href="#login-modal">立即登录</a></p>
            </form>
        </div>
    </div>`;
    
    // 忘记密码模态框HTML - 使用与其他页面一致的样式类
    const forgotPasswordModalHtml = `
    <div id="forgot-password-modal" class="modal">
        <div class="modal-content">
            <span class="close-button">&times;</span>
            <h2>忘记密码</h2>
            <form id="forgot-password-form">
                <div class="form-group">
                    <label for="forgot-email">邮箱</label>
                    <input type="email" id="forgot-email" name="email" required placeholder="请输入注册邮箱">
                </div>
                <button type="submit" class="modal-btn">重置密码</button>
                <p class="login-link">想起密码了? <a href="#login-modal">立即登录</a></p>
            </form>
        </div>
    </div>`;
    
    // 添加提示消息元素
    if (!document.getElementById('toast-message')) {
        const toastHtml = `<div id="toast-message" class="toast"></div>`;
        document.body.insertAdjacentHTML('beforeend', toastHtml);
    }
    
    // 将模态框添加到页面
    document.body.insertAdjacentHTML('beforeend', loginModalHtml);
    document.body.insertAdjacentHTML('beforeend', registerModalHtml);
    document.body.insertAdjacentHTML('beforeend', forgotPasswordModalHtml);
    
}

// 初始化数据存储系统（异步）
if (window.DataStorage && typeof window.DataStorage.initDataStorage === 'function') {
    window.DataStorage.initDataStorage()
        .then(() => {
            console.log('数据存储系统初始化成功');
        })
        .catch(error => {
            console.error('数据存储系统初始化失败:', error);
        });
} else {
    // 如果DataStorage模块不可用，等待一段时间后再尝试
    setTimeout(() => {
        if (window.DataStorage && typeof window.DataStorage.initDataStorage === 'function') {
            window.DataStorage.initDataStorage()
                .then(() => {
                    console.log('数据存储系统延迟初始化成功');
                })
                .catch(error => {
                    console.error('数据存储系统延迟初始化失败:', error);
                });
        }
    }, 1000);
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

// 关闭所有模态框
function closeAllModals() {
    const modals = ['login-modal', 'register-modal', 'forgot-password-modal', 'terms-modal', 'privacy-modal'];
    modals.forEach(modalId => {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.style.display = 'none';
        }
    });
    // 恢复背景滚动
    document.body.style.overflow = '';
    
    // 重置全局注册状态
    if (isRegistering) {
        isRegistering = false;
    }
}

// 关闭指定模态框
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = 'none';
        // 恢复背景滚动
        document.body.style.overflow = '';
        
        // 重置全局注册状态
        if (isRegistering) {
            isRegistering = false;
        }
    }
}

// 显示指定模态框
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        // 先关闭所有模态框
        closeAllModals();
        // 显示指定模态框
        modal.style.display = 'block';
        // 禁止背景滚动
        document.body.style.overflow = 'hidden';
    }
}

// 防止重复初始化的标志
let modalsInitialized = false;
// 全局注册状态标志，防止重复提交
let isRegistering = false;

// 模态框功能实现
function setupModals() {
    // 防止重复初始化
    if (modalsInitialized) {
        return;
    }
    
    // 获取模态框元素
    const loginModal = document.getElementById('login-modal');
    const registerModal = document.getElementById('register-modal');
    
    // 如果模态框不存在，退出初始化
    if (!loginModal || !registerModal) {
        return;
    }
    
    // 标记为已初始化
    modalsInitialized = true;
    
    // 获取模态框相关的按钮和链接
    const loginLinks = document.querySelectorAll('a[href="#login-modal"]');
    const registerLinks = document.querySelectorAll('a[href="#register-modal"]');
    const closeButtons = document.querySelectorAll('.close-button');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const forgotPasswordLinks = document.querySelectorAll('.forgot-password');
    
    // 设置用户协议和隐私政策链接
    setupPolicyLinks();
    
    // 检查用户是否已登录
    checkLoginStatus();
    
    // 打开登录模态框
    loginLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            closeAllModals();
            loginModal.style.display = 'block';
            // 禁止背景滚动
            document.body.style.overflow = 'hidden';
        });
    });
    
    // 打开注册模态框
    registerLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            closeAllModals();
            registerModal.style.display = 'block';
            // 禁止背景滚动
            document.body.style.overflow = 'hidden';
        });
    });
    
    // 关闭模态框
    closeButtons.forEach(button => {
        button.addEventListener('click', function() {
            closeAllModals();
        });
    });
    
    // 点击模态框外部关闭
    window.addEventListener('click', function(e) {
        const forgotPasswordModal = document.getElementById('forgot-password-modal');
        if (e.target === loginModal || e.target === registerModal || e.target === forgotPasswordModal) {
            closeAllModals();
        }
    });
    
    // 按ESC键关闭模态框
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeAllModals();
        }
    });
    
    // 登录表单提交
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 如果正在注册过程中，忽略登录验证
            if (isRegistering) {
                return;
            }
            
            // 获取表单数据
            const username = document.getElementById('login-username').value.trim();
            const password = document.getElementById('login-password').value;
            
            // 登录表单验证
            if (!username) {
                showToast('请输入用户名', 'error');
                return;
            }
            
            if (!password) {
                showToast('请输入密码', 'error');
                return;
            }
            
            // 从数据存储系统获取用户数据
            let users = [];
            if (window.DataStorage && typeof window.DataStorage.loadUsersFromLocalStorage === 'function') {
                users = window.DataStorage.loadUsersFromLocalStorage();
            } else {
                // 降级方案：直接从localStorage获取
                users = JSON.parse(localStorage.getItem('users')) || [];
            }
            
            // 查找用户并验证密码
            const user = users.find(u => u.username === username);
            if (!user) {
                showToast('用户名不存在', 'error');
                return;
            }
            
            if (user.password !== password) {
                showToast('密码错误', 'error');
                return;
            }
            
            // 登录成功，保存用户信息到本地存储（保留用户的头像和标语）
            localStorage.setItem('currentUser', JSON.stringify({
                username: user.username,
                email: user.email,
                avatar: user.avatar || '', // 保留用户已上传的头像
                motto: user.motto || ''     // 保留用户设置的个人标语
            }));
            
            showToast('登录成功，欢迎回来！', 'success');
            
            // 更新登录状态
            updateLoginStatus();
            
            // 触发登录状态变化事件，让其他组件（如答题系统）知道用户已登录
            setTimeout(() => {
                const event = new CustomEvent('userLoginStateChanged', {
                    detail: {
                        user: JSON.parse(localStorage.getItem('currentUser'))
                    }
                });
                document.dispatchEvent(event);
            }, 50);
            
            // 1秒后关闭模态框
            setTimeout(() => {
                closeAllModals();
            }, 1000);
        });
    }
    
    // 注册表单提交
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 防止重复提交
            if (isRegistering) {
                return;
            }
            
            // 设置注册标志
            isRegistering = true;
            
            // 获取表单数据 - 优先从当前表单上下文中获取
            const currentForm = e.target;
            const username = (currentForm.querySelector('#register-username') || document.getElementById('register-username')).value.trim();
            const email = (currentForm.querySelector('#register-email') || document.getElementById('register-email')).value.trim();
            const password = (currentForm.querySelector('#register-password') || document.getElementById('register-password')).value;
            const confirmPassword = (currentForm.querySelector('#register-confirm-password') || document.getElementById('register-confirm-password')).value;
            const agreeTermsElement = currentForm.querySelector('#agree-terms') || document.getElementById('agree-terms');
            const agreeTerms = agreeTermsElement ? agreeTermsElement.checked : true;
            
            // 表单验证
            
            // 1. 检查用户名重复
            if (!username) {
                showToast('请输入用户名', 'error');
                isRegistering = false;
                return;
            }
            
            // 2. 检查邮箱重复
            if (!email) {
                showToast('请输入邮箱', 'error');
                isRegistering = false;
                return;
            }
            
            // 3. 检查密码强度（6-20位，必须包含字母和数字）
            if (!password) {
                showToast('请输入密码', 'error');
                isRegistering = false;
                return;
            }
            
            if (password.length < 6 || password.length > 20) {
                showToast('密码长度必须为6-20位', 'error');
                isRegistering = false;
                return;
            }
            
            const hasLetter = /[a-zA-Z]/.test(password);
            const hasNumber = /\d/.test(password);
            
            if (!hasLetter || !hasNumber) {
                showToast('密码必须同时包含英文字母和数字', 'error');
                isRegistering = false;
                return;
            }
            
            // 4. 检查密码确认
            if (password !== confirmPassword) {
                showToast('两次输入的密码不一致', 'error');
                isRegistering = false;
                return;
            }
            
            // 5. 检查是否同意隐私政策
            if (!agreeTerms) {
                showToast('请阅读并同意隐私政策', 'error');
                isRegistering = false;
                return;
            }
            
            // 从数据存储系统获取用户数据
            let users = [];
            if (window.DataStorage && typeof window.DataStorage.loadUsersFromLocalStorage === 'function') {
                users = window.DataStorage.loadUsersFromLocalStorage();
            } else {
                // 降级方案：直接从localStorage获取
                users = JSON.parse(localStorage.getItem('users')) || [];
            }
            
            // 检查用户名是否已存在
            const existingUsername = users.find(user => user.username === username);
            if (existingUsername) {
                showToast('用户名已存在，请选择其他用户名', 'error');
                isRegistering = false;
                return;
            }
            
            // 检查邮箱是否已存在
            const existingEmail = users.find(user => user.email === email);
            if (existingEmail) {
                showToast('邮箱已被注册，请使用其他邮箱', 'error');
                isRegistering = false;
                return;
            }
            
            // 添加新用户
            users.push({
                username: username,
                email: email,
                password: password
            });
            
            // 保存到数据存储系统
            let saveSuccess = false;
            if (window.DataStorage && typeof window.DataStorage.saveUsersToLocalStorage === 'function') {
                saveSuccess = window.DataStorage.saveUsersToLocalStorage(users);
            } else {
                // 降级方案：直接保存到localStorage
                try {
                    localStorage.setItem('users', JSON.stringify(users));
                    saveSuccess = true;
                } catch (error) {
                    console.error('保存用户数据失败:', error);
                    saveSuccess = false;
                }
            }
            
            if (!saveSuccess) {
                showToast('保存用户数据失败，请重试', 'error');
                isRegistering = false;
                return;
            }
            
            // 立即显示成功消息
            showToast('注册成功，请登录！', 'success');
            
            // 延迟清空表单，避免干扰成功消息
            setTimeout(() => {
                registerForm.reset();
            }, 200);
            
            // 1.5秒后关闭注册模态框并打开登录模态框
            setTimeout(() => {
                closeAllModals();
                // 确保模态框完全关闭后再打开登录模态框
                setTimeout(() => {
                    loginModal.style.display = 'block';
                    // 禁止背景滚动
                    document.body.style.overflow = 'hidden';
                    
                    // 自动填充用户名
                    const loginUsernameInput = document.getElementById('login-username');
                    if (loginUsernameInput) {
                        loginUsernameInput.value = username;
                    }
                    
                    // 重置注册标志，允许正常的登录操作
                    isRegistering = false;
                }, 100);
            }, 1500);
            
            // 延迟触发登录状态变化事件，避免与模态框操作冲突
            setTimeout(() => {
                const event = new CustomEvent('userLoginStateChanged', {
                    detail: {
                        user: null
                    }
                });
                document.dispatchEvent(event);
            }, 2000);
        });
    }
    
    // 忘记密码链接点击事件
    forgotPasswordLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // 显示忘记密码模态框（已从modals.html加载）
            const forgotPasswordModal = document.getElementById('forgot-password-modal');
            if (forgotPasswordModal) {
                closeAllModals();
                forgotPasswordModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            } else {
                console.error('忘记密码模态框未找到');
            }
        });
    });
    
    // 忘记密码表单提交处理
    const forgotPasswordForm = document.getElementById('forgot-password-form');
    if (forgotPasswordForm) {
        forgotPasswordForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // 获取邮箱输入
            const email = document.getElementById('forgot-email').value.trim();
            
            // 邮箱验证
            if (!email) {
                showToast('请输入邮箱地址', 'error');
                return;
            }
            
            // 邮箱格式验证
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email)) {
                showToast('请输入有效的邮箱格式', 'error');
                return;
            }
            
            // 检查邮箱是否在系统中注册
            let users = [];
            if (window.DataStorage && typeof window.DataStorage.loadUsersFromLocalStorage === 'function') {
                users = window.DataStorage.loadUsersFromLocalStorage();
            } else {
                // 降级方案：直接从localStorage获取
                users = JSON.parse(localStorage.getItem('users')) || [];
            }
            
            const user = users.find(u => u.email === email);
            if (!user) {
                showToast('该邮箱未注册，请先注册账户', 'error');
                return;
            }
            
            // 获取新密码输入
            const newPassword = document.getElementById('forgot-new-password').value.trim();
            const confirmPassword = document.getElementById('forgot-confirm-password').value.trim();
            
            // 新密码验证
            if (!newPassword) {
                showToast('请输入新密码', 'error');
                return;
            }
            
            if (newPassword.length < 6) {
                showToast('密码长度不能少于6位', 'error');
                return;
            }
            
            if (!confirmPassword) {
                showToast('请确认新密码', 'error');
                return;
            }
            
            if (newPassword !== confirmPassword) {
                showToast('两次输入的密码不一致', 'error');
                return;
            }
            
            // 更新用户密码
            user.password = newPassword;
            
            // 保存更新后的用户数据
            if (window.DataStorage && typeof window.DataStorage.saveUsersToLocalStorage === 'function') {
                window.DataStorage.saveUsersToLocalStorage(users);
            } else {
                // 降级方案：直接保存到localStorage
                localStorage.setItem('users', JSON.stringify(users));
            }
            
            // 密码重置成功提示
            showToast('密码重置成功！请返回登录页面', 'success');
            
            // 控制台输出重置信息
            console.log(`密码重置成功：用户名: ${user.username}, 邮箱: ${email}`);
            
            // 清空表单
            forgotPasswordForm.reset();
            
            // 1.5秒后关闭模态框并打开登录模态框
            setTimeout(() => {
                closeAllModals();
                setTimeout(() => {
                    const loginModal = document.getElementById('login-modal');
                    if (loginModal) {
                        loginModal.style.display = 'block';
                        document.body.style.overflow = 'hidden';
                    }
                }, 100);
            }, 1500);
        });
    }
    
    // 处理忘记密码模态框中"立即登录"链接的点击事件
    const forgotPasswordModal = document.getElementById('forgot-password-modal');
    if (forgotPasswordModal) {
        const forgotLoginLink = forgotPasswordModal.querySelector('a[href="#login-modal"]');
        if (forgotLoginLink) {
            forgotLoginLink.addEventListener('click', function(e) {
                e.preventDefault();
                closeAllModals();
                const loginModal = document.getElementById('login-modal');
                if (loginModal) {
                    loginModal.style.display = 'block';
                    document.body.style.overflow = 'hidden';
                }
            });
        }
    }

    
    // 这些函数已在文件开头定义，此处保留用于参考
    // function updateLoginStatus() {}
    // function checkLoginStatus() {}
    // function logout() {}
}

// 创建个人资料模态框
function createProfileModal() {
    // 检查模态框是否已存在
    if (document.getElementById('profile-modal')) return;
    
    // 创建模态框HTML
    const modalHtml = `
    <div id="profile-modal" class="modal">
        <div class="modal-content">
            <span class="close-button">&times;</span>
            <h2>个人资料</h2>
            <div class="profile-container">
                <div class="profile-avatar-section">
                    <div class="avatar-preview">
                        <img id="avatar-preview-img" src="" alt="用户头像">
                        <div class="avatar-placeholder">
                            <i class="fas fa-user"></i>
                        </div>
                    </div>
                    <div class="avatar-upload">
                        <input type="file" id="avatar-upload-input" accept="image/*" style="display: none;">
                        <button id="avatar-upload-btn" class="btn">上传头像</button>
                        <p class="upload-hint">支持 JPG、PNG 格式，建议尺寸 200x200</p>
                    </div>
                </div>
                <div class="profile-info-section">
                    <form id="profile-form">
                        <div class="form-group">
                            <label>用户名</label>
                            <input type="text" id="profile-username" readonly>
                        </div>
                        <div class="form-group">
                            <label>邮箱</label>
                            <input type="email" id="profile-email" readonly>
                        </div>
                        <div class="form-group">
                            <label for="profile-motto">个人标语</label>
                            <textarea id="profile-motto" rows="3" placeholder="写下你的个人标语..."></textarea>
                        </div>
                        <button type="submit" class="btn submit-btn">保存修改</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    `;
    
    // 添加样式
    const styleHtml = `
    <style>
        .profile-container {
            display: flex;
            gap: 30px;
            margin-top: 20px;
        }
        
        .profile-avatar-section {
            flex: 0 0 200px;
            text-align: center;
        }
        
        .avatar-preview {
            width: 200px;
            height: 200px;
            border-radius: 50%;
            overflow: hidden;
            margin: 0 auto 20px;
            background-color: #f0f0f0;
            position: relative;
        }
        
        .avatar-preview img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: none;
        }
        
        .avatar-preview img.show {
            display: block;
        }
        
        .avatar-placeholder {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 80px;
            color: #ccc;
        }
        
        .avatar-preview img.show + .avatar-placeholder {
            display: none;
        }
        
        .avatar-upload {
            margin-top: 15px;
        }
        
        .upload-hint {
            font-size: 12px;
            color: #666;
            margin-top: 10px;
        }
        
        .profile-info-section {
            flex: 1;
        }
        
        #profile-form .form-group {
            margin-bottom: 20px;
        }
        
        #profile-form label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
        }
        
        #profile-form input[readonly] {
            background-color: #f5f5f5;
            cursor: not-allowed;
        }
        
        #profile-form textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            resize: vertical;
            font-family: inherit;
        }
        
        /* 深色主题适配 */
        body.dark-theme .avatar-preview {
            background-color: #2d3748;
        }
        
        body.dark-theme .upload-hint {
            color: #a0aec0;
        }
        
        body.dark-theme #profile-form input[readonly] {
            background-color: #1a202c;
            color: #e2e8f0;
        }
        
        body.dark-theme #profile-form textarea {
            background-color: #1a202c;
            color: #e2e8f0;
            border-color: #4a5568;
        }
    </style>
    `;
    
    // 添加到页面
    document.head.insertAdjacentHTML('beforeend', styleHtml);
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // 设置事件处理器
    setupProfileModalEvents();
}

// 设置个人资料模态框事件
function setupProfileModalEvents() {
    const modal = document.getElementById('profile-modal');
    const closeButton = modal.querySelector('.close-button');
    const avatarUploadBtn = document.getElementById('avatar-upload-btn');
    const avatarUploadInput = document.getElementById('avatar-upload-input');
    const profileForm = document.getElementById('profile-form');
    
    // 关闭模态框
    closeButton.addEventListener('click', () => {
        modal.style.display = 'none';
        document.body.style.overflow = '';
    });
    
    // 点击外部关闭
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
            document.body.style.overflow = '';
        }
    });
    
    // 上传头像按钮
    avatarUploadBtn.addEventListener('click', () => {
        avatarUploadInput.click();
    });
    
    // 处理头像上传
    avatarUploadInput.addEventListener('change', handleAvatarUpload);
    
    // 提交表单
    profileForm.addEventListener('submit', handleProfileSubmit);
}

// 处理头像上传
function handleAvatarUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // 文件验证已移除 - 允许上传任何文件
    
    // 读取并显示图片
    const reader = new FileReader();
    reader.onload = function(e) {
        const avatarImg = document.getElementById('avatar-preview-img');
        avatarImg.src = e.target.result;
        avatarImg.classList.add('show');
        
        // 保存到用户数据
        const currentUser = JSON.parse(localStorage.getItem('currentUser'));
        if (currentUser) {
            currentUser.avatar = e.target.result;
            localStorage.setItem('currentUser', JSON.stringify(currentUser));
            
            // 同时更新users数组中的数据
            const users = JSON.parse(localStorage.getItem('users') || '[]');
            const userIndex = users.findIndex(u => u.username === currentUser.username);
            if (userIndex !== -1) {
                users[userIndex].avatar = e.target.result;
                localStorage.setItem('users', JSON.stringify(users));
            }
            
            showToast('头像上传成功', 'success');
            updateNavbarAvatar();
        }
    };
    reader.readAsDataURL(file);
}

// 处理个人资料表单提交
function handleProfileSubmit(e) {
    e.preventDefault();
    
    const motto = document.getElementById('profile-motto').value.trim();
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    
    if (currentUser) {
        currentUser.motto = motto;
        localStorage.setItem('currentUser', JSON.stringify(currentUser));
        
        // 同时更新users数组中的数据
        const users = JSON.parse(localStorage.getItem('users') || '[]');
        const userIndex = users.findIndex(u => u.username === currentUser.username);
        if (userIndex !== -1) {
            users[userIndex].motto = motto;
            localStorage.setItem('users', JSON.stringify(users));
        }
        
        showToast('个人资料已保存', 'success');
    }
}

// 打开个人资料模态框
function openProfileModal() {
    // 确保模态框已创建
    createProfileModal();
    
    const modal = document.getElementById('profile-modal');
    const currentUser = JSON.parse(localStorage.getItem('currentUser'));
    
    // 登录状态检查已移除 - 允许未登录用户访问个人资料
    if (!currentUser) {
        // 创建默认用户信息
        const defaultUser = {
            username: 'Guest_' + Date.now(),
            email: 'guest@example.com',
            avatar: '',
            motto: ''
        };
        localStorage.setItem('currentUser', JSON.stringify(defaultUser));
    }
    
    // 重新获取用户信息（可能刚刚创建了默认用户）
    const updatedUser = JSON.parse(localStorage.getItem('currentUser'));
    
    // 填充用户信息
    document.getElementById('profile-username').value = updatedUser.username || '';
    document.getElementById('profile-email').value = updatedUser.email || '';
    document.getElementById('profile-motto').value = updatedUser.motto || '';
    
    // 显示头像
    const avatarImg = document.getElementById('avatar-preview-img');
    if (updatedUser.avatar) {
        avatarImg.src = updatedUser.avatar;
        avatarImg.classList.add('show');
    } else {
        avatarImg.classList.remove('show');
    }
    
    // 显示模态框
    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
}

// 更新导航栏头像（如果需要显示的话）
function updateNavbarAvatar() {
    // 这个函数可以用于在导航栏显示用户头像
    // 目前暂时不实现，可以在后续需要时扩展
}

// 将openProfileModal函数暴露到全局
window.openProfileModal = openProfileModal;

// 为深色主题添加模态框样式适配
function addDarkThemeStyles() {
    const styleId = 'dark-theme-styles';
    let style = document.getElementById(styleId);
    
    if (!style) {
        style = document.createElement('style');
        style.id = styleId;
        document.head.appendChild(style);
    }
    
    // 原有的深色主题样式
    style.textContent = `
        @keyframes navLinkFade {
            from {
                opacity: 0;
                transform: translateX(50px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        /* 深色主题样式 */
        body.dark-theme {
            --color-light: #1a202c;
            --color-dark: #f7fafc;
            --color-text: #e2e8f0;
            --color-text-light: #a0aec0;
            --color-background: #2d3748;
            --color-code-bg: #1a202c;
            --color-code-text: #81e6d9;
            --color-border: #4a5568;
            background-color: var(--color-background);
            color: var(--color-text);
        }
        
        body.dark-theme .tutorial-sidebar,
        body.dark-theme .tutorial-content,
        body.dark-theme .feature-box,
        body.dark-theme .testimonial-box {
            background-color: #2d3748;
            color: var(--color-text);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        }
        
        body.dark-theme .tutorial-sidebar h3,
        body.dark-theme .tutorial-content h1,
        body.dark-theme .section h2,
        body.dark-theme .section h3 {
            color: var(--color-text);
        }
        
        body.dark-theme .intro {
            background-color: #4a5568;
            border-left: 4px solid var(--color-primary);
            color: var(--color-text);
        }
        
        body.dark-theme table {
            background: #2d3748;
        }
        
        body.dark-theme th {
            background-color: var(--color-primary);
        }
        
        body.dark-theme tr:hover {
            background-color: #4a5568;
        }
        
        body.dark-theme .code-block {
            background-color: var(--color-code-bg);
            color: var(--color-code-text);
        }
        
        /* 移动端菜单深色主题样式 - 仅在移动端生效 */
        @media (max-width: 768px) {
            body.dark-theme .nav-links {
                background-color: #1a202c !important;
                color: #e2e8f0 !important;
            }
            
            body.dark-theme .nav-links a {
                color: #e2e8f0 !important;
            }
            
            body.dark-theme .nav-links a:hover,
            body.dark-theme .nav-links a.active {
                color: var(--color-secondary) !important;
            }
        }
        
        /* 桌面端保持原有样式 */
        @media (min-width: 769px) {
            body.dark-theme .nav-links a:hover,
            body.dark-theme .nav-links a.active {
                color: var(--color-secondary);
            }
        }
        
        /* 移动端深色主题下拉菜单样式 */
        @media (max-width: 768px) {
            body.dark-theme .nav-links .dropdown-menu {
                background-color: rgba(26, 32, 44, 0.95) !important;
            }
            
            body.dark-theme .nav-links .dropdown-menu a {
                color: #e2e8f0 !important;
            }
            
            body.dark-theme .nav-links .dropdown-menu a:hover {
                background-color: rgba(74, 85, 104, 0.8) !important;
                color: var(--color-secondary) !important;
            }
        }
        
        body.dark-theme header {
            background-color: #2d3748 !important;
        }
        
        body.dark-theme .features {
            background-color: #2d3748;
        }
        
        body.dark-theme .testimonials {
            background-color: #1a202c;
        }
        
        body.dark-theme footer {
            background-color: #2d3748;
            color: var(--color-text);
        }
        
        /* 响应式设计调整 */
        @media screen and (max-width: 768px) {
            #theme-toggle {
                position: absolute;
                top: 1rem;
                right: 4rem;
                margin-left: 0;
            }
        }
        
        /* 深色主题下的模态框样式 */
        body.dark-theme .modal-content {
            background-color: #2d3748;
            color: var(--color-text);
        }
        
        body.dark-theme .modal-content h2 {
            color: var(--color-text);
        }
        
        body.dark-theme .form-group input {
            background-color: #1a202c;
            color: var(--color-text);
            border-color: #4a5568;
        }
        
        body.dark-theme .form-group input:focus {
            border-color: var(--color-primary);
            box-shadow: 0 0 0 3px rgba(80, 116, 151, 0.3);
        }
        
        body.dark-theme .checkbox-label,
        body.dark-theme .register-link,
        body.dark-theme .login-link {
            color: var(--color-text);
        }
        
        body.dark-theme .close-button {
            color: var(--color-text-light);
        }
        
        body.dark-theme .close-button:hover {
            color: var(--color-text);
        }
    `;
}

// 设置用户协议和隐私政策链接
function setupPolicyLinks() {
    // 处理用户协议链接
    const termsLinks = document.querySelectorAll('.terms-link, a[href="#terms"], a[href="#terms-modal"], a[href="#"]');
    termsLinks.forEach(link => {
        // 只处理包含"用户协议"文本的链接
        if (link.textContent.includes('用户协议')) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                openTermsModal();
            });
        }
    });

    // 处理隐私政策链接
    const privacyLinks = document.querySelectorAll('.privacy-link, a[href="#privacy"], a[href="#privacy-modal"], a[href="#"]');
    privacyLinks.forEach(link => {
        // 只处理包含"隐私政策"文本的链接
        if (link.textContent.includes('隐私政策')) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                openPrivacyModal();
            });
        }
    });

    // 处理模态框内的同意按钮
    const termsAgreeBtn = document.querySelector('#terms-modal .agree-btn');
    const privacyAgreeBtn = document.querySelector('#privacy-modal .agree-btn');
    const termsCancelBtn = document.querySelector('#terms-modal .cancel-btn');
    const privacyCancelBtn = document.querySelector('#privacy-modal .cancel-btn');

    if (termsAgreeBtn) {
        termsAgreeBtn.addEventListener('click', function() {
            const agreeCheckbox = document.getElementById('agree-terms');
            if (agreeCheckbox) {
                agreeCheckbox.checked = true;
            }
            closeAllModals();
            showToast('已同意用户协议', 'success');
        });
    }

    if (privacyAgreeBtn) {
        privacyAgreeBtn.addEventListener('click', function() {
            const agreeCheckbox = document.getElementById('agree-terms');
            if (agreeCheckbox) {
                agreeCheckbox.checked = true;
            }
            closeAllModals();
            showToast('已同意隐私政策', 'success');
        });
    }

    if (termsCancelBtn) {
        termsCancelBtn.addEventListener('click', function() {
            closeAllModals();
        });
    }

    if (privacyCancelBtn) {
        privacyCancelBtn.addEventListener('click', function() {
            closeAllModals();
        });
    }
}

// 打开用户协议模态框
function openTermsModal() {
    const modal = document.getElementById('terms-modal');
    if (modal) {
        closeAllModals();
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    } else {
        // 如果模态框不存在，显示提示信息
        showToast('正在加载用户协议...', 'info');
        // 尝试重新加载模态框
        setTimeout(() => {
            const retryModal = document.getElementById('terms-modal');
            if (retryModal) {
                retryModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            } else {
                showToast('用户协议加载失败，请刷新页面重试', 'error');
            }
        }, 500);
    }
}

// 打开隐私政策模态框
function openPrivacyModal() {
    const modal = document.getElementById('privacy-modal');
    if (modal) {
        closeAllModals();
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    } else {
        // 如果模态框不存在，显示提示信息
        showToast('正在加载隐私政策...', 'info');
        // 尝试重新加载模态框
        setTimeout(() => {
            const retryModal = document.getElementById('privacy-modal');
            if (retryModal) {
                retryModal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            } else {
                showToast('隐私政策加载失败，请刷新页面重试', 'error');
            }
        }, 500);
    }
}