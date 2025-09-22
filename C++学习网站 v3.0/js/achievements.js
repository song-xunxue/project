// 成就系统管理模块
// 为C++学习网站提供完整的成就系统

// 成就定义
const ACHIEVEMENTS = {
    'basic-master': {
        id: 'basic-master',
        name: '初出茅庐',
        description: '完成基础语法部分所有题目并全部答对',
        icon: '🌱',
        requirement: {
            section: 'basic',
            score: 8,
            total: 8
        },
        unlocked: false,
        unlockedAt: null
    },
    'oop-expert': {
        id: 'oop-expert', 
        name: '牛刀小试',
        description: '完成面向对象部分所有题目并全部答对',
        icon: '🔧',
        requirement: {
            section: 'oop',
            score: 8,
            total: 8
        },
        unlocked: false,
        unlockedAt: null
    },
    'advanced-guru': {
        id: 'advanced-guru',
        name: '登堂入室', 
        description: '完成高级特性部分所有题目并全部答对',
        icon: '🏛️',
        requirement: {
            section: 'advanced',
            score: 8,
            total: 8
        },
        unlocked: false,
        unlockedAt: null
    },
    'effective-master': {
        id: 'effective-master',
        name: '精益求精',
        description: '完成Effective C++部分所有题目并全部答对',
        icon: '💎',
        requirement: {
            section: 'effective',
            score: 8,
            total: 8
        },
        unlocked: false,
        unlockedAt: null
    },
    'stl-legend': {
        id: 'stl-legend',
        name: '登峰造极',
        description: '完成STL源码解析部分所有题目并全部答对',
        icon: '👑',
        requirement: {
            section: 'stl',
            score: 8,
            total: 8
        },
        unlocked: false,
        unlockedAt: null
    }
};

// 成就系统核心类
class AchievementSystem {
    constructor() {
        this.achievements = { ...ACHIEVEMENTS };
        this.loadUserAchievements();
    }

    // 加载用户成就数据
    loadUserAchievements() {
        const currentUser = this.getCurrentUser();
        if (!currentUser) {
            // 用户未登录，重置所有成就状态
            Object.keys(this.achievements).forEach(key => {
                this.achievements[key].unlocked = false;
                this.achievements[key].unlockedAt = null;
            });
            console.log('用户未登录，已重置成就状态');
            return;
        }

        // 从localStorage加载用户成就数据
        const achievementKey = `achievements_${currentUser.username}`;
        const savedAchievements = localStorage.getItem(achievementKey);
        
        // 首先重置所有成就状态
        Object.keys(this.achievements).forEach(key => {
            this.achievements[key].unlocked = false;
            this.achievements[key].unlockedAt = null;
        });
        
        if (savedAchievements) {
            try {
                const parsed = JSON.parse(savedAchievements);
                Object.keys(parsed).forEach(key => {
                    if (this.achievements[key]) {
                        this.achievements[key].unlocked = parsed[key].unlocked || false;
                        this.achievements[key].unlockedAt = parsed[key].unlockedAt || null;
                    }
                });
                console.log(`已为用户 ${currentUser.username} 加载成就数据`);
            } catch (error) {
                console.error('加载成就数据失败:', error);
            }
        } else {
            console.log(`用户 ${currentUser.username} 暂无成就数据`);
        }
    }

    // 保存用户成就数据
    saveUserAchievements() {
        const currentUser = this.getCurrentUser();
        if (!currentUser) {
            console.warn('用户未登录，无法保存成就数据');
            return false;
        }

        const achievementKey = `achievements_${currentUser.username}`;
        const achievementData = {};
        
        Object.keys(this.achievements).forEach(key => {
            achievementData[key] = {
                unlocked: this.achievements[key].unlocked,
                unlockedAt: this.achievements[key].unlockedAt
            };
        });

        try {
            localStorage.setItem(achievementKey, JSON.stringify(achievementData));
            return true;
        } catch (error) {
            console.error('保存成就数据失败:', error);
            return false;
        }
    }

    // 获取当前登录用户
    getCurrentUser() {
        if (window.DataStorage && typeof window.DataStorage.loadCurrentUser === 'function') {
            return window.DataStorage.loadCurrentUser();
        } else {
            const currentUserStr = localStorage.getItem('currentUser');
            return currentUserStr ? JSON.parse(currentUserStr) : null;
        }
    }

    // 检查并解锁成就
    checkAchievement(sectionScores) {
        const currentUser = this.getCurrentUser();
        if (!currentUser) {
            return {
                success: false,
                message: '请先登录账户以获得成就！',
                newAchievements: []
            };
        }

        console.log('成就系统：检查成就开始，当前用户:', currentUser.username);
        console.log('成就系统：收到的得分数据:', sectionScores);

        const newAchievements = [];

        Object.keys(this.achievements).forEach(achievementId => {
            const achievement = this.achievements[achievementId];
            const requirement = achievement.requirement;
            
            console.log(`检查成就 ${achievement.name}:`, {
                achievementId,
                requirement,
                unlocked: achievement.unlocked,
                sectionScore: sectionScores[requirement.section]
            });
            
            // 如果成就已解锁，跳过
            if (achievement.unlocked) {
                console.log(`成就 ${achievement.name} 已解锁，跳过`);
                return;
            }

            // 检查是否满足成就条件
            const sectionScore = sectionScores[requirement.section];
            if (sectionScore && sectionScore >= requirement.score) {
                // 解锁成就
                achievement.unlocked = true;
                achievement.unlockedAt = new Date().toISOString();
                newAchievements.push(achievement);
                console.log(`🎉 解锁新成就: ${achievement.name}`);
            } else {
                console.log(`成就 ${achievement.name} 条件未满足: 需要 ${requirement.score}，当前 ${sectionScore || 0}`);
            }
        });

        // 保存成就数据
        if (newAchievements.length > 0) {
            this.saveUserAchievements();
        }

        return {
            success: true,
            message: newAchievements.length > 0 ? `恭喜获得${newAchievements.length}个新成就！` : '',
            newAchievements: newAchievements
        };
    }

    // 获取所有成就
    getAllAchievements() {
        return Object.values(this.achievements);
    }

    // 获取已解锁的成就
    getUnlockedAchievements() {
        return Object.values(this.achievements).filter(achievement => achievement.unlocked);
    }

    // 获取成就进度统计
    getAchievementStats() {
        const total = Object.keys(this.achievements).length;
        const unlocked = this.getUnlockedAchievements().length;
        const progress = total > 0 ? Math.round((unlocked / total) * 100) : 0;

        return {
            total,
            unlocked,
            locked: total - unlocked,
            progress
        };
    }

    // 显示成就通知
    showAchievementNotification(achievement) {
        // 创建成就通知元素
        const notification = document.createElement('div');
        notification.className = 'achievement-notification';
        notification.innerHTML = `
            <div class="achievement-notification-content">
                <div class="achievement-icon">${achievement.icon}</div>
                <div class="achievement-text">
                    <h4>成就解锁！</h4>
                    <p><strong>${achievement.name}</strong></p>
                    <p>${achievement.description}</p>
                </div>
            </div>
        `;

        // 添加样式
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            z-index: 10000;
            max-width: 350px;
            animation: slideInRight 0.5s ease-out;
            border: 2px solid #ffd700;
        `;

        // 添加动画样式
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            .achievement-notification-content {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            .achievement-icon {
                font-size: 2rem;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .achievement-text h4 {
                margin: 0 0 5px 0;
                font-size: 1.1rem;
                color: #ffd700;
            }
            .achievement-text p {
                margin: 2px 0;
                font-size: 0.9rem;
                line-height: 1.3;
            }
        `;
        document.head.appendChild(style);

        // 添加到页面
        document.body.appendChild(notification);

        // 3秒后自动移除
        setTimeout(() => {
            notification.style.animation = 'slideInRight 0.5s ease-out reverse';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 500);
        }, 3000);

        // 点击关闭
        notification.addEventListener('click', () => {
            notification.style.animation = 'slideInRight 0.5s ease-out reverse';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 500);
        });
    }

    // 刷新用户成就数据（当用户状态变化时调用）
    refreshUserData() {
        console.log('刷新成就系统用户数据');
        this.loadUserAchievements();
    }

    // 重置用户成就（用于测试或账户切换）
    resetUserAchievements() {
        const currentUser = this.getCurrentUser();
        if (!currentUser) {
            return false;
        }

        const achievementKey = `achievements_${currentUser.username}`;
        localStorage.removeItem(achievementKey);
        
        // 重置内存中的成就状态
        Object.keys(this.achievements).forEach(key => {
            this.achievements[key].unlocked = false;
            this.achievements[key].unlockedAt = null;
        });

        return true;
    }
}

// 全局成就系统实例
window.AchievementSystem = new AchievementSystem();

// 导出相关函数供其他模块使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        AchievementSystem,
        ACHIEVEMENTS
    };
}
