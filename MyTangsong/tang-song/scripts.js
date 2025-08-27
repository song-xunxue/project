document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('nav a');

    // 添加平滑滚动效果
    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                event.preventDefault();
                window.scrollTo({
                    top: target.offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });

    // 高亮当前导航项
    navLinks.forEach(link => {
        if (link.href === window.location.href) {
            link.style.color = '#35495e'; // 设置为深色以示高亮
        }
    });
});
