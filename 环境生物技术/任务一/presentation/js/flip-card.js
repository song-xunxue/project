/* ========== 卡片翻转组件 ========== */
/* 第一次点击：翻转查看失败模式；之后任意点击：跳转到下一题 */
/* 总结反思：点击即跳转下一节 */

document.addEventListener('DOMContentLoaded', () => {
  // 页面跳转映射
  const pageMap = {
    'q1-scale.html': 'q2-enzyme.html',
    'q2-enzyme.html': 'q3-pentose.html',
    'q3-pentose.html': 'q4-mesp.html',
    'q4-mesp.html': 'q5-supply.html',
    'q5-supply.html': 'decision.html',
    'decision.html': 'summary.html',
    'summary.html': 'references.html',
  };
  const current = window.location.pathname.split('/').pop();
  const nextPage = pageMap[current] || null;

  // 翻转卡片逻辑
  document.querySelectorAll('.flip-card').forEach(card => {
    card.addEventListener('click', () => {
      if (!card.classList.contains('flipped')) {
        card.classList.add('flipped');
        const qIdx = card.dataset.question;
        if (qIdx) {
          const dot = document.getElementById('qdot-' + qIdx);
          if (dot) { dot.classList.add('done'); dot.classList.remove('active'); }
        }
      } else if (nextPage) {
        window.location.href = nextPage;
      }
    });
  });

  // 总结/决策/参考文献：点击页面主体区域跳转下一节
  const clickToNext = document.querySelector('.click-to-next');
  if (clickToNext && nextPage) {
    clickToNext.addEventListener('click', () => {
      window.location.href = nextPage;
    });
  }
});
