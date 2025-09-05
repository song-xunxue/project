// 夜间模式切换
const darkModeToggle = document.getElementById('darkModeToggle');
const html = document.documentElement;

// 检查本地存储中的模式设置
if (localStorage.getItem('darkMode') === 'true') {
    html.classList.add('dark-mode');
}

darkModeToggle.addEventListener('click', () => {
    html.classList.toggle('dark-mode');
    // 保存用户偏好
    localStorage.setItem('darkMode', html.classList.contains('dark-mode'));
});