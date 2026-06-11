/* ========== 动画系统 ========== */

document.addEventListener('DOMContentLoaded', () => {
  // 通用 fade-in / fade-in-left / fade-in-right / scale-in
  const animClasses = ['.fade-in', '.fade-in-left', '.fade-in-right', '.scale-in'];
  animClasses.forEach(cls => {
    document.querySelectorAll(cls).forEach(el => {
      const obs = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible');
            obs.unobserve(entry.target);
          }
        });
      }, { threshold: 0.12, rootMargin: '0px 0px -30px 0px' });
      obs.observe(el);
    });
  });

  // 时间线节点逐个浮入
  document.querySelectorAll('.timeline-item').forEach((item, i) => {
    item.style.transitionDelay = (i * 0.12) + 's';
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    obs.observe(item);
  });

  // 投资决策流程动画
  const flow = document.getElementById('decisionFlow');
  if (flow) {
    const obs = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        flow.querySelectorAll('.decision-step').forEach((step, i) => {
          setTimeout(() => step.classList.add('visible'), i * 300);
        });
        obs.unobserve(flow);
      }
    }, { threshold: 0.15 });
    obs.observe(flow);
  }

  // 总结行浮入
  const summary = document.getElementById('summaryLines');
  if (summary) {
    const obs = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        summary.querySelectorAll('.summary-line').forEach((line, i) => {
          setTimeout(() => line.classList.add('visible'), i * 350);
        });
        obs.unobserve(summary);
      }
    }, { threshold: 0.15 });
    obs.observe(summary);
  }

  // 问题列表卡片逐个浮入
  document.querySelectorAll('.question-card').forEach((card, i) => {
    card.style.opacity = '0';
    card.style.transform = 'translateX(-20px)';
    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    card.style.transitionDelay = (i * 0.1) + 's';
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateX(0)';
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.2 });
    obs.observe(card);
  });
});
