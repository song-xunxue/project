/* ========== 导航逻辑 ========== */

// 高亮当前页面对应的导航链接
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  const links = document.querySelectorAll('.nav-link');

  links.forEach(link => {
    link.classList.remove('active');
    const href = link.getAttribute('href') || link.dataset.href;
    if (!href) return;

    if (path.includes(href)) {
      link.classList.add('active');
    }
  });

  // 根据路径自动判断当前区域
  if (path.includes('/timeline/')) {
    highlightNav('timeline');
  } else if (path.includes('/simulation/')) {
    highlightNav('simulation');
  } else {
    highlightNav('home');
  }
});

function highlightNav(section) {
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  const target = document.querySelector(`.nav-link[data-section="${section}"]`);
  if (target) target.classList.add('active');
}
