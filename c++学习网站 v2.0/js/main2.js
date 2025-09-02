// main.js - 实现主题切换功能
document.addEventListener('DOMContentLoaded', function () {
    // 创建主题切换按钮
    const themeToggle = document.createElement('button');
    themeToggle.id = 'theme-toggle';
    themeToggle.innerHTML = '🌙 夜间模式';
    themeToggle.style.cssText = `
        background: var(--color-primary);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        cursor: pointer;
        font-family: var(--font-sans);
        margin-left: 1rem;
        transition: all 0.3s ease;
    `;

    // 将主题切换按钮添加到导航栏
    const nav = document.querySelector('nav');
    if (nav) {
        // 检查是否已存在主题切换按钮
        if (!document.getElementById('theme-toggle')) {
            nav.appendChild(themeToggle);
        }
    }

    // 检查本地存储中的主题偏好
    const currentTheme = localStorage.getItem('theme') || 'light';
    if (currentTheme === 'dark') {
        enableDarkMode();
        themeToggle.innerHTML = '☀️ 日间模式';
    }

    // 主题切换按钮点击事件
    themeToggle.addEventListener('click', function () {
        if (document.body.classList.contains('dark-theme')) {
            disableDarkMode();
            themeToggle.innerHTML = '🌙 夜间模式';
        } else {
            enableDarkMode();
            themeToggle.innerHTML = '☀️ 日间模式';
        }
    });

    // 移动端菜单切换功能
    const burger = document.querySelector('.burger');
    const navLinks = document.querySelector('.nav-links');

    if (burger && navLinks) {
        burger.addEventListener('click', function () {
            navLinks.classList.toggle('nav-active');

            // 导航链接动画
            const navItems = document.querySelectorAll('.nav-links li');
            if (navLinks.classList.contains('nav-active')) {
                navItems.forEach((link, index) => {
                    link.style.animation = `navLinkFade 0.5s ease forwards ${index / 7 + 0.3}s`;
                });
            } else {
                navItems.forEach(link => {
                    link.style.animation = '';
                });
            }

            // 汉堡菜单动画
            burger.classList.toggle('toggle');
        });
    }

    // 添加CSS动画关键帧和深色主题样式
    addDarkThemeStyles();

    // 修复about页面的图片显示问题
    fixAboutPageImages();
});

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

// 添加深色主题样式
function addDarkThemeStyles() {
    const styleId = 'dark-theme-styles';
    if (document.getElementById(styleId)) return;

    const style = document.createElement('style');
    style.id = styleId;
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
        
        //9.1修复 这两段，有bug 
        // body.dark-theme .nav-links {
        //     background-color: var(--color-dark);
        // }
        
        // body.dark-theme .nav-links a {
        //     color: var(--color-text);
        // }
        
        body.dark-theme .nav-links a:hover,
        body.dark-theme .nav-links a.active {
            color: var(--color-secondary);
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
    `;

    document.head.appendChild(style);
}

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
    setTimeout(function () {
        loader.style.opacity = '0';
        setTimeout(function () {
            loader.style.display = 'none';
        }, 500);
    }, 1500);

    // 北京时间显示器
    const counterElement = document.getElementById('learning-counter');
    const dateElement = document.getElementById('learning-date');

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
});