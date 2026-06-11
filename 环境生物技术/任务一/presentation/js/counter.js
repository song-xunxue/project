/* ========== 数字翻滚动画 ========== */

function animateCounter(elementId, start, end, step, interval) {
  const el = document.getElementById(elementId);
  if (!el) return;
  let val = start;
  const timer = setInterval(() => {
    val += step;
    if (val >= end) { val = end; clearInterval(timer); }
    el.textContent = '$' + val.toFixed(2);
  }, interval);
}

function observeCounter(elementId, start, end, step, interval) {
  const el = document.getElementById(elementId);
  if (!el) return;
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(elementId, start, end, step, interval);
        obs.unobserve(el);
      }
    });
  }, { threshold: 0.5 });
  obs.observe(el);
}
