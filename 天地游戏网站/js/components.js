/* 轮播 */
export class Carousel{
  constructor(selector,{autoPlay=true,interval=4000}={}){
    this.carousel=document.querySelector(selector);
    this.items=this.carousel.querySelectorAll('.carousel-item');
    this.idx=0;this.autoPlay=autoPlay;this.interval=interval;this.timer=null;
    this.init();
  }
  init(){
    this.show();
    if(this.autoPlay){this.play();}
    this.addTouch();
  }
  show(){this.items.forEach((el,i)=>el.style.display=i===this.idx?'block':'none');}
  next(){this.idx=(this.idx+1)%this.items.length;this.show();}
  prev(){this.idx=(this.idx-1+this.items.length)%this.items.length;this.show();}
  play(){this.timer=setInterval(()=>this.next(),this.interval);}
  stop(){clearInterval(this.timer);}
  addTouch(){
    let startX=0;
    this.carousel.addEventListener('touchstart',e=>{startX=e.touches[0].clientX;this.stop();});
    this.carousel.addEventListener('touchend',e=>{
      const endX=e.changedTouches[0].clientX;
      if(Math.abs(startX-endX)>50){startX>endX?this.next():this.prev();}
      if(this.autoPlay){this.play();}
    });
  }
}

/* 折叠面板 */
export function initAccordions(){
  document.querySelectorAll('.accordion-header').forEach(btn=>{
    btn.addEventListener('click',()=>{
      const content=btn.nextElementSibling;
      const isOpen=content.classList.contains('active');
      document.querySelectorAll('.accordion-content').forEach(c=>c.classList.remove('active'));
      if(!isOpen){content.classList.add('active');}
    });
  });
}

/* 技能切换 */
export function initSkills(){
  document.querySelectorAll('.skill-icon').forEach(icon=>{
    icon.addEventListener('click',()=>{
      const group=icon.closest('.skill-icons');
      const contents=group.nextElementSibling.querySelectorAll('.skill-content');
      const idx=Array.from(group.children).indexOf(icon);
      group.querySelectorAll('.skill-icon').forEach(i=>i.classList.remove('active'));
      contents.forEach(c=>c.classList.remove('active'));
      icon.classList.add('active');
      contents[idx].classList.add('active');
    });
  });
}

/* 筛选按钮 */
export function initFilters(filterSelector,itemSelector){
  document.querySelectorAll(filterSelector).forEach(btn=>{
    btn.addEventListener('click',()=>{
      const role=btn.dataset.filter||btn.dataset.cat||btn.dataset.role;
      document.querySelectorAll(itemSelector).forEach(card=>{
        card.style.display=!role||role==='all'||card.dataset.filter===role?'':'none';
      });
      document.querySelectorAll(filterSelector).forEach(b=>b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
}

/* 回到顶部 */
export function initBackToTop(){
  const btn=document.createElement('div');btn.className='back-to-top';btn.innerHTML='↑';
  document.body.appendChild(btn);
  window.addEventListener('scroll',()=>{
    btn.classList.toggle('visible',window.scrollY>300);
  });
  btn.addEventListener('click',()=>window.scrollTo({top:0,behavior:'smooth'}));
}

/* 移动端菜单 */
export function initMobileNav(){
  const toggle=document.querySelector('.nav-toggle');
  const menu=document.querySelector('.nav-menu');
  if(!toggle||!menu)return;
  toggle.addEventListener('click',()=>menu.classList.toggle('active'));
  document.querySelectorAll('.nav-menu a').forEach(a=>a.addEventListener('click',()=>menu.classList.remove('active')));
}