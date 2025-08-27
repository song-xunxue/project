document.addEventListener('DOMContentLoaded', () => {
    const toggleMode = document.querySelector('#toggleMode');

    // 检查是否已经处于夜间模式，如果是则添加相应的 class
    if (localStorage.getItem('darkMode') === 'enabled') {
        // 暂时移除 transition 属性
        document.body.style.transition = 'none';
        document.querySelector('nav').style.transition = 'none';
        document.querySelector('footer').style.transition = 'none';

        // 添加夜间模式的类
        document.body.classList.add('dark-mode');
        document.querySelector('nav').classList.add('dark-mode');
        document.querySelector('footer').classList.add('dark-mode');

        // 强制重绘，使得 transition 的移除生效
        document.body.offsetHeight;

        // 恢复 transition 属性
        document.body.style.transition = '';
        document.querySelector('nav').style.transition = '';
        document.querySelector('footer').style.transition = '';
    }

    toggleMode.addEventListener('click', () => {
        document.body.classList.toggle('dark-mode');
        document.querySelector('nav').classList.toggle('dark-mode');
        document.querySelector('footer').classList.toggle('dark-mode');

        // 存储夜间模式状态
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('darkMode', 'enabled');
        } else {
            localStorage.removeItem('darkMode');
        }
    });
});
