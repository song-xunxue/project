/**
 * 鼠标交互背景效果
 * 包含粒子系统、光晕效果、波纹效果和星空背景
 */

class InteractiveBackground {
    constructor() {
        this.mouseX = 0;
        this.mouseY = 0;
        this.particles = [];
        this.stars = [];
        this.lastParticleTime = 0;
        this.lastTrailTime = 0;
        this.isInitialized = false;
        
        // 配置参数
        this.config = {
            particles: {
                maxCount: 50,
                spawnRate: 100, // 毫秒
                trailRate: 50   // 毫秒
            },
            stars: {
                count: 80,
                interactionDistance: 100
            },
            performance: {
                enableParticles: true,
                enableStars: true,
                enableGlow: true,
                enableRipples: true
            }
        };

        this.init();
    }

    init() {
        // 检查是否为移动设备，减少效果以提升性能
        this.isMobile = window.innerWidth <= 768;
        if (this.isMobile) {
            this.config.particles.maxCount = 20;
            this.config.stars.count = 30;
            this.config.particles.spawnRate = 200;
        }

        this.setupElements();
        this.createStars();
        this.bindEvents();
        this.startAnimationLoop();
        this.isInitialized = true;
        
        console.log('🎨 Interactive Background initialized');
    }

    setupElements() {
        this.interactiveBg = document.getElementById('interactive-bg');
        this.particlesContainer = document.getElementById('particles-container');
        this.mouseGlow = document.getElementById('mouse-glow');
        this.rippleContainer = document.getElementById('ripple-container');
        this.starfield = document.getElementById('starfield');

        if (!this.interactiveBg) {
            console.warn('Interactive background elements not found');
            return;
        }

        // 初始隐藏光晕效果
        if (this.mouseGlow) {
            this.mouseGlow.style.opacity = '0';
        }
    }

    createStars() {
        if (!this.starfield || !this.config.performance.enableStars) return;

        const starCount = this.config.stars.count;
        
        for (let i = 0; i < starCount; i++) {
            const star = document.createElement('div');
            star.className = 'star';
            
            // 随机大小
            const size = Math.random();
            if (size > 0.8) {
                star.classList.add('large');
            } else if (size > 0.5) {
                star.classList.add('medium');
            } else {
                star.classList.add('small');
            }

            // 随机位置
            const x = Math.random() * 100;
            const y = Math.random() * 100;
            star.style.left = x + '%';
            star.style.top = y + '%';

            // 随机动画延迟
            star.style.animationDelay = Math.random() * 2 + 's';
            star.style.animationDuration = (1.5 + Math.random() * 2) + 's';

            this.starfield.appendChild(star);
            this.stars.push({
                element: star,
                x: x,
                y: y,
                originalDelay: star.style.animationDelay
            });
        }
    }

    bindEvents() {
        // 鼠标移动事件
        document.addEventListener('mousemove', (e) => {
            this.mouseX = e.clientX;
            this.mouseY = e.clientY;
            this.updateMouseGlow();
            this.updateStarInteraction();
        });

        // 鼠标进入页面
        document.addEventListener('mouseenter', () => {
            if (this.mouseGlow && this.config.performance.enableGlow) {
                this.mouseGlow.style.opacity = '1';
            }
        });

        // 鼠标离开页面
        document.addEventListener('mouseleave', () => {
            if (this.mouseGlow) {
                this.mouseGlow.style.opacity = '0';
            }
            this.resetStars();
        });

        // 点击创建波纹
        document.addEventListener('click', (e) => {
            if (this.config.performance.enableRipples) {
                this.createRipple(e.clientX, e.clientY);
            }
        });

        // 窗口大小变化
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // 页面可见性变化（性能优化）
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseAnimations();
            } else {
                this.resumeAnimations();
            }
        });
    }

    updateMouseGlow() {
        if (!this.mouseGlow || !this.config.performance.enableGlow) return;

        this.mouseGlow.style.left = this.mouseX + 'px';
        this.mouseGlow.style.top = this.mouseY + 'px';
    }

    updateStarInteraction() {
        if (!this.config.performance.enableStars) return;

        const interactionDistance = this.config.stars.interactionDistance;
        const windowWidth = window.innerWidth;
        const windowHeight = window.innerHeight;

        this.stars.forEach(star => {
            const starX = (star.x / 100) * windowWidth;
            const starY = (star.y / 100) * windowHeight;
            
            const distance = Math.sqrt(
                Math.pow(this.mouseX - starX, 2) + 
                Math.pow(this.mouseY - starY, 2)
            );

            if (distance < interactionDistance) {
                star.element.classList.add('mouse-near');
            } else {
                star.element.classList.remove('mouse-near');
            }
        });
    }

    createParticle() {
        if (!this.particlesContainer || !this.config.performance.enableParticles) return;
        
        if (this.particles.length >= this.config.particles.maxCount) {
            return;
        }

        const particle = document.createElement('div');
        particle.className = 'particle';
        
        // 在鼠标位置创建粒子
        particle.style.left = this.mouseX + 'px';
        particle.style.top = this.mouseY + 'px';

        // 随机移动方向
        const angle = Math.random() * Math.PI * 2;
        const distance = 50 + Math.random() * 100;
        const randomX = Math.cos(angle) * distance;
        const randomY = Math.sin(angle) * distance;

        particle.style.setProperty('--random-x', randomX + 'px');
        particle.style.setProperty('--random-y', randomY + 'px');

        this.particlesContainer.appendChild(particle);
        this.particles.push(particle);

        // 3秒后移除粒子
        setTimeout(() => {
            if (particle.parentNode) {
                particle.parentNode.removeChild(particle);
            }
            const index = this.particles.indexOf(particle);
            if (index > -1) {
                this.particles.splice(index, 1);
            }
        }, 3000);
    }

    createTrail() {
        if (!this.particlesContainer || !this.config.performance.enableParticles) return;

        const trail = document.createElement('div');
        trail.className = 'particle-trail';
        
        trail.style.left = this.mouseX + 'px';
        trail.style.top = this.mouseY + 'px';

        this.particlesContainer.appendChild(trail);

        // 1秒后移除轨迹
        setTimeout(() => {
            if (trail.parentNode) {
                trail.parentNode.removeChild(trail);
            }
        }, 1000);
    }

    createRipple(x, y) {
        if (!this.rippleContainer) return;

        const ripple = document.createElement('div');
        ripple.className = 'ripple';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';

        this.rippleContainer.appendChild(ripple);

        // 1秒后移除波纹
        setTimeout(() => {
            if (ripple.parentNode) {
                ripple.parentNode.removeChild(ripple);
            }
        }, 1000);
    }

    resetStars() {
        this.stars.forEach(star => {
            star.element.classList.remove('mouse-near');
        });
    }

    startAnimationLoop() {
        const animate = (currentTime) => {
            if (document.hidden) {
                requestAnimationFrame(animate);
                return;
            }

            // 创建粒子
            if (currentTime - this.lastParticleTime > this.config.particles.spawnRate) {
                this.createParticle();
                this.lastParticleTime = currentTime;
            }

            // 创建轨迹
            if (currentTime - this.lastTrailTime > this.config.particles.trailRate) {
                this.createTrail();
                this.lastTrailTime = currentTime;
            }

            requestAnimationFrame(animate);
        };

        requestAnimationFrame(animate);
    }

    handleResize() {
        const wasMobile = this.isMobile;
        this.isMobile = window.innerWidth <= 768;
        
        // 如果设备类型改变，重新配置
        if (wasMobile !== this.isMobile) {
            if (this.isMobile) {
                this.config.particles.maxCount = 20;
                this.config.stars.count = 30;
                this.config.particles.spawnRate = 200;
            } else {
                this.config.particles.maxCount = 50;
                this.config.stars.count = 80;
                this.config.particles.spawnRate = 100;
            }
        }
    }

    pauseAnimations() {
        // 暂停所有动画以节省性能
        if (this.interactiveBg) {
            this.interactiveBg.style.animationPlayState = 'paused';
        }
    }

    resumeAnimations() {
        // 恢复动画
        if (this.interactiveBg) {
            this.interactiveBg.style.animationPlayState = 'running';
        }
    }

    // 公共方法：切换效果
    toggleEffect(effectName, enabled) {
        if (this.config.performance[effectName] !== undefined) {
            this.config.performance[effectName] = enabled;
            console.log(`${effectName} ${enabled ? 'enabled' : 'disabled'}`);
        }
    }

    // 公共方法：获取性能信息
    getPerformanceInfo() {
        return {
            particles: this.particles.length,
            stars: this.stars.length,
            isMobile: this.isMobile,
            config: this.config
        };
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    // 延迟初始化以确保所有元素都已加载
    setTimeout(() => {
        window.interactiveBackground = new InteractiveBackground();
    }, 100);
});

// 导出类以供其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = InteractiveBackground;
}
