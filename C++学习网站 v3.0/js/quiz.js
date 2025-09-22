// quiz.js - 题库功能实现

document.addEventListener('DOMContentLoaded', function() {
    // 题目答案数据 - 全新的5个部分，每部分8道题
    const quizAnswers = {
        // 基础语法部分
        'basic_q1': 'C',
        'basic_q2': 'A', 
        'basic_q3': 'B',
        'basic_q4': 'B',
        'basic_q5': 'C',
        'basic_q6': 'B',
        'basic_q7': 'C',
        'basic_q8': 'A',
        
        // 面向对象部分
        'oop_q1': 'C',
        'oop_q2': 'A',
        'oop_q3': 'B',
        'oop_q4': 'B',
        'oop_q5': 'C',
        'oop_q6': 'A',
        'oop_q7': 'B',
        'oop_q8': 'A',
        
        // 高级特性部分
        'advanced_q1': 'A',
        'advanced_q2': 'B',
        'advanced_q3': 'B',
        'advanced_q4': 'B',
        'advanced_q5': 'B',
        'advanced_q6': 'A',
        'advanced_q7': 'B',
        'advanced_q8': 'B',
        
        // Effective C++部分
        'effective_q1': 'B',
        'effective_q2': 'C',
        'effective_q3': 'C',
        'effective_q4': 'B',
        'effective_q5': 'B',
        'effective_q6': 'B',
        'effective_q7': 'C',
        'effective_q8': 'C',
        
        // STL源码解析部分
        'stl_q1': 'B',
        'stl_q2': 'B',
        'stl_q3': 'B',
        'stl_q4': 'B',
        'stl_q5': 'B',
        'stl_q6': 'C',
        'stl_q7': 'D',
        'stl_q8': 'B'
    };

    // 每个部分的题目配置
    const sectionConfig = {
        'basic': { name: '基础语法', totalQuestions: 8 },
        'oop': { name: '面向对象', totalQuestions: 8 },
        'advanced': { name: '高级特性', totalQuestions: 8 },
        'effective': { name: 'Effective C++', totalQuestions: 8 },
        'stl': { name: 'STL源码解析', totalQuestions: 8 }
    };

    // 用户答题数据 - 按部分存储
    let sectionResults = {
        'basic': { userAnswers: {}, score: 0, completed: false },
        'oop': { userAnswers: {}, score: 0, completed: false },
        'advanced': { userAnswers: {}, score: 0, completed: false },
        'effective': { userAnswers: {}, score: 0, completed: false },
        'stl': { userAnswers: {}, score: 0, completed: false }
    };

    // 初始化题库功能
    initQuiz();

    // 初始化函数
    function initQuiz() {
        // 加载保存的答题数据
        loadQuizData();

        // 更新学习统计
        updateQuizStats();

        // 添加分部分提交按钮事件
        document.querySelectorAll('.submit-section').forEach(button => {
            button.addEventListener('click', function() {
                const section = this.dataset.section;
                submitSection(section);
            });
        });

        // 添加题目选项点击事件（用于实时更新选择状态）
        document.querySelectorAll('.quiz-item input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', function() {
                const quizItem = this.closest('.quiz-item');
                updateQuestionVisualState(quizItem);
            });
        });

        // 平滑滚动功能
        setupSmoothScroll();
        
        // 设置登录状态监听器
        setupLoginStateListener();
        
        // 添加清空答题记录按钮事件
        const clearDataBtn = document.getElementById('clear-quiz-data');
        if (clearDataBtn) {
            clearDataBtn.addEventListener('click', function() {
                clearQuizData();
            });
        }

        // 初始化AI助手按钮
        initAIAssistantButtons();
    }
    
    // 分部分提交功能
    function submitSection(sectionName) {
        const sectionElement = document.querySelector(`[data-section="${sectionName}"]`);
        const quizItems = sectionElement.querySelectorAll('.quiz-item');
        
        // 检查该部分的所有题目是否已回答
        let allAnswered = true;
        const sectionAnswers = {};
        
        quizItems.forEach(quizItem => {
            const quizId = quizItem.dataset.id;
            const selectedOption = quizItem.querySelector(`input[name="${quizId}"]:checked`);
            
            if (!selectedOption) {
                allAnswered = false;
                return;
            }
            
            sectionAnswers[quizId] = selectedOption.value;
        });
        
        if (!allAnswered) {
            showToast(`请完成${sectionConfig[sectionName].name}部分的所有题目`, 'warning');
            return;
        }
        
        // 计算该部分得分
        let correctCount = 0;
        quizItems.forEach(quizItem => {
            const quizId = quizItem.dataset.id;
            const userAnswer = sectionAnswers[quizId];
            const correctAnswer = quizAnswers[quizId];
            const isCorrect = userAnswer === correctAnswer;
            
            if (isCorrect) {
                correctCount++;
                quizItem.classList.add('correct');
                quizItem.classList.remove('incorrect');
            } else {
                quizItem.classList.add('incorrect');
                quizItem.classList.remove('correct');
            }
            
            // 显示解析
            const explanation = quizItem.querySelector('.quiz-explanation');
            if (explanation) {
                explanation.classList.remove('hidden');
            }
            
            // 禁用该题目的选项
            const radioButtons = quizItem.querySelectorAll('input[type="radio"]');
            radioButtons.forEach(radio => {
                radio.disabled = true;
            });
        });
        
        // 更新部分结果
        sectionResults[sectionName] = {
            userAnswers: sectionAnswers,
            score: correctCount,
            completed: true
        };
        
        // 显示该部分结果
        displaySectionResult(sectionName, correctCount, sectionConfig[sectionName].totalQuestions);
        
        // 禁用提交按钮
        const submitBtn = sectionElement.querySelector('.submit-section');
        submitBtn.disabled = true;
        submitBtn.textContent = '已提交';
        submitBtn.classList.add('submitted');
        
        // 保存数据
        saveQuizData();
        
        // 更新统计
        updateQuizStats();
        
        // 检查成就
        checkAchievements(sectionName, correctCount);
        
        // 显示提示
        const percentage = Math.round((correctCount / sectionConfig[sectionName].totalQuestions) * 100);
        showToast(`${sectionConfig[sectionName].name}部分已提交！得分：${correctCount}/${sectionConfig[sectionName].totalQuestions} (${percentage}%)`, 'success');
    }
    
    // 显示部分结果
    function displaySectionResult(sectionName, score, total) {
        const resultElement = document.getElementById(`${sectionName}-result`);
        if (resultElement) {
            const percentage = Math.round((score / total) * 100);
            let resultClass = 'result-excellent';
            let resultText = '优秀';
            
            if (percentage < 60) {
                resultClass = 'result-poor';
                resultText = '需要提高';
            } else if (percentage < 80) {
                resultClass = 'result-good';
                resultText = '良好';
            }
            
            resultElement.innerHTML = `
                <div class="section-score ${resultClass}">
                    <span class="score-text">得分：${score}/${total}</span>
                    <span class="score-percentage">${percentage}%</span>
                    <span class="score-level">${resultText}</span>
                </div>
            `;
            resultElement.classList.remove('hidden');
        }
    }
    
    // 更新题目视觉状态（用户选择后的视觉反馈）
    function updateQuestionVisualState(quizItem) {
        // 给已选择的题目添加视觉标识
        quizItem.classList.add('answered');
    }
    
    // 清空答题记录函数
    function clearQuizData() {
        // 显示确认对话框
        if (confirm('确定要清空所有答题记录吗？此操作不可撤销。')) {
            // 获取当前用户
            const currentUser = getCurrentUser();
            
            // 清除本地存储中的答题数据
            if (currentUser) {
                localStorage.removeItem(`quizData_${currentUser}`);
            }
            
            // 重置当前答题数据
            sectionResults = {
                'basic': { userAnswers: {}, score: 0, completed: false },
                'oop': { userAnswers: {}, score: 0, completed: false },
                'advanced': { userAnswers: {}, score: 0, completed: false },
                'effective': { userAnswers: {}, score: 0, completed: false },
                'stl': { userAnswers: {}, score: 0, completed: false }
            };
            
            // 清空所有题目的状态
            document.querySelectorAll('.quiz-item').forEach(quizItem => {
                quizItem.classList.remove('correct', 'incorrect', 'answered');
                
                // 重置选择题的选择状态
                const radioButtons = quizItem.querySelectorAll('input[type="radio"]');
                radioButtons.forEach(radio => {
                    radio.checked = false;
                    radio.disabled = false;
                });
                
                // 隐藏解析
                const explanation = quizItem.querySelector('.quiz-explanation');
                if (explanation) {
                    explanation.classList.add('hidden');
                }
            });
            
            // 重置提交按钮
            document.querySelectorAll('.submit-section').forEach(btn => {
                btn.disabled = false;
                btn.classList.remove('submitted');
                const section = btn.dataset.section;
                btn.textContent = `提交${sectionConfig[section].name}部分`;
            });
            
            // 隐藏结果显示
            document.querySelectorAll('.section-result').forEach(result => {
                result.classList.add('hidden');
            });
            
            // 更新统计显示
            updateQuizStats();
            
            // 显示提示
            showToast('答题记录已清空', 'success');
        }
    }

    // 更新学习统计 - 新的统计逻辑
    function updateQuizStats() {
        // 更新各部分的得分显示
        Object.keys(sectionConfig).forEach(sectionName => {
            const scoreElement = document.getElementById(`${sectionName}-score`);
            if (scoreElement) {
                const sectionData = sectionResults[sectionName];
                if (sectionData.completed) {
                    scoreElement.textContent = `${sectionData.score}/8`;
                    scoreElement.classList.add('completed');
                } else {
                    scoreElement.textContent = '0/8';
                    scoreElement.classList.remove('completed');
                }
            }
        });

        // 更新总体进度
        const overallProgressElem = document.getElementById('overall-progress');
        if (overallProgressElem) {
            let totalCompleted = 0;
            let totalQuestions = 0;
            
            Object.keys(sectionConfig).forEach(sectionName => {
                totalQuestions += sectionConfig[sectionName].totalQuestions;
                if (sectionResults[sectionName].completed) {
                    totalCompleted += sectionResults[sectionName].score;
                }
            });
            
            overallProgressElem.textContent = `${totalCompleted}/${totalQuestions}`;
            
            // 计算完成的部分数量
            const completedSections = Object.values(sectionResults).filter(section => section.completed).length;
            overallProgressElem.setAttribute('data-sections', `${completedSections}/5`);
        }
    }

    // 获取当前登录用户
    function getCurrentUser() {
        let currentUser;
        
        // 优先使用DataStorage模块
        if (window.DataStorage && typeof window.DataStorage.loadCurrentUser === 'function') {
            currentUser = window.DataStorage.loadCurrentUser();
        } else {
            // 降级方案：直接使用localStorage
            const currentUserStr = localStorage.getItem('currentUser');
            currentUser = currentUserStr ? JSON.parse(currentUserStr) : null;
        }
        
        return currentUser ? currentUser.username : null;
    }

    // 保存答题数据到本地存储，与用户账号绑定
    function saveQuizData() {
        const currentUser = getCurrentUser();
        
        // 只有在有用户登录时才保存答题数据
        if (currentUser) {
            const storageKey = `quizData_${currentUser}`;
            
            const quizData = {
                sectionResults: sectionResults,
                timestamp: Date.now()
            };
            
            // 优先使用DataStorage模块
            if (window.DataStorage && typeof window.DataStorage.saveData === 'function') {
                window.DataStorage.saveData(storageKey, quizData);
            } else {
                // 降级方案：直接使用localStorage
                localStorage.setItem(storageKey, JSON.stringify(quizData));
            }
        }
    }

    // 从本地存储加载答题数据，根据当前登录用户加载对应数据
    function loadQuizData() {
        // 重置当前答题数据
        sectionResults = {
            'basic': { userAnswers: {}, score: 0, completed: false },
            'oop': { userAnswers: {}, score: 0, completed: false },
            'advanced': { userAnswers: {}, score: 0, completed: false },
            'effective': { userAnswers: {}, score: 0, completed: false },
            'stl': { userAnswers: {}, score: 0, completed: false }
        };
        
        // 获取当前用户
        const currentUser = getCurrentUser();
        
        // 只有在有用户登录时才加载答题数据
        if (currentUser) {
            const storageKey = `quizData_${currentUser}`;
            
            // 优先使用DataStorage模块
            let savedData;
            if (window.DataStorage && typeof window.DataStorage.loadData === 'function') {
                savedData = window.DataStorage.loadData(storageKey);
            } else {
                // 降级方案：直接使用localStorage
                const savedDataStr = localStorage.getItem(storageKey);
                if (savedDataStr) {
                    savedData = JSON.parse(savedDataStr);
                }
            }
            
            if (savedData && savedData.sectionResults) {
                sectionResults = savedData.sectionResults;
            }
        }
        
        // 恢复界面状态
        restoreQuizState();
        
        // 更新统计显示
        updateQuizStats();
    }
    
    // 恢复题库界面状态
    function restoreQuizState() {
        Object.keys(sectionResults).forEach(sectionName => {
            const sectionData = sectionResults[sectionName];
            if (sectionData.completed) {
                const sectionElement = document.querySelector(`[data-section="${sectionName}"]`);
                if (sectionElement) {
                    const quizItems = sectionElement.querySelectorAll('.quiz-item');
                    
                    // 恢复每道题的状态
                    quizItems.forEach(quizItem => {
                        const quizId = quizItem.dataset.id;
                        const userAnswer = sectionData.userAnswers[quizId];
                        
                        if (userAnswer) {
                            // 恢复选择状态
                            const radioButton = quizItem.querySelector(`input[value="${userAnswer}"]`);
                            if (radioButton) {
                                radioButton.checked = true;
                                radioButton.disabled = true;
                            }
                            
                            // 恢复正确/错误状态
                            const correctAnswer = quizAnswers[quizId];
                            const isCorrect = userAnswer === correctAnswer;
                            
                            if (isCorrect) {
                                quizItem.classList.add('correct');
                            } else {
                                quizItem.classList.add('incorrect');
                            }
                            
                            quizItem.classList.add('answered');
                            
                            // 显示解析
                            const explanation = quizItem.querySelector('.quiz-explanation');
                            if (explanation) {
                                explanation.classList.remove('hidden');
                            }
                            
                            // 禁用所有选项
                            const allRadios = quizItem.querySelectorAll('input[type="radio"]');
                            allRadios.forEach(radio => {
                                radio.disabled = true;
                            });
                        }
                    });
                    
                    // 恢复提交按钮状态
                    const submitBtn = sectionElement.querySelector('.submit-section');
                    if (submitBtn) {
                        submitBtn.disabled = true;
                        submitBtn.textContent = '已提交';
                        submitBtn.classList.add('submitted');
                    }
                    
                    // 显示部分结果
                    displaySectionResult(sectionName, sectionData.score, sectionConfig[sectionName].totalQuestions);
                }
            }
        });
    }

    // 监听用户登录状态变化，重新加载答题数据
    function setupLoginStateListener() {
        // 创建一个自定义事件监听器
        window.addEventListener('userLoginStateChanged', loadQuizData);
        
        // 检查main2.js是否已加载，如果已加载，手动触发一次登录状态检查
        if (window.updateLoginStatus && typeof window.updateLoginStatus === 'function') {
            // 为了确保登录状态正确，立即重新加载一次
            setTimeout(loadQuizData, 100);
        }
    }

    // 显示提示消息
    function showToast(message, type = 'info') {
        const toast = document.getElementById('toast-message');
        if (!toast) return;

        // 设置消息内容和类型
        toast.textContent = message;
        toast.className = 'toast'; // 重置类
        toast.classList.add(type);

        // 显示提示
        toast.style.display = 'block';

        // 3秒后隐藏
        setTimeout(() => {
            toast.style.display = 'none';
        }, 3000);
    }

    // 平滑滚动功能
    function setupSmoothScroll() {
        // 为目录中的所有链接添加点击事件
        const navLinks = document.querySelectorAll('.tutorial-nav a');

        navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault(); // 阻止默认的跳转行为

                // 获取目标元素的id
                const targetId = this.getAttribute('href');
                const targetElement = document.querySelector(targetId);

                if (targetElement) {
                    // 计算滚动位置（考虑页面头部高度）
                    const headerHeight = document.querySelector('header')?.offsetHeight || 0;
                    const targetPosition = targetElement.getBoundingClientRect().top + window.pageYOffset - headerHeight - 20;

                    // 平滑滚动到目标位置
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });
    }
    
    // 成就检查函数
    function checkAchievements(sectionName, score) {
        // 检查成就系统是否可用
        if (!window.AchievementSystem) {
            console.warn('成就系统未加载');
            return;
        }
        
        // 映射section名称到成就系统中的名称
        const sectionMapping = {
            'basic': 'basic',
            'oop': 'oop', 
            'advanced': 'advanced',
            'effective': 'effective',
            'stl': 'stl'
        };
        
        // 获取当前所有部分的得分
        const sectionScores = {};
        Object.keys(sectionMapping).forEach(section => {
            if (sectionResults[section] && sectionResults[section].completed) {
                sectionScores[sectionMapping[section]] = sectionResults[section].score;
            }
        });
        
        // 添加当前提交的部分得分
        sectionScores[sectionMapping[sectionName]] = score;
        
        // 调试信息
        console.log('检查成就 - 当前部分:', sectionName, '得分:', score);
        console.log('传递给成就系统的得分:', sectionScores);
        
        // 检查成就
        const result = window.AchievementSystem.checkAchievement(sectionScores);
        
        if (!result.success) {
            // 用户未登录，显示成就提示
            setTimeout(() => {
                showToast(result.message, 'warning');
            }, 1500);
            return;
        }
        
        // 显示新解锁的成就
        if (result.newAchievements.length > 0) {
            setTimeout(() => {
                result.newAchievements.forEach((achievement, index) => {
                    setTimeout(() => {
                        window.AchievementSystem.showAchievementNotification(achievement);
                    }, index * 1000); // 每个成就通知间隔1秒
                });
            }, 2000); // 延迟2秒显示，让用户先看到提交结果
        }
    }

    // 初始化AI助手按钮
    function initAIAssistantButtons() {
        // 为每个题目添加AI助手按钮
        const quizItems = document.querySelectorAll('.quiz-item');
        
        quizItems.forEach(item => {
            const questionDiv = item.querySelector('.quiz-question');
            if (questionDiv && !questionDiv.querySelector('.ai-assistant-btn')) {
                // 重新组织题目结构以确保正确的布局
                reorganizeQuestionLayout(questionDiv);
                
                // 创建AI助手按钮
                const aiButton = document.createElement('button');
                aiButton.className = 'ai-assistant-btn';
                aiButton.innerHTML = '<i class="fas fa-robot"></i> 问问AI助手';
                aiButton.title = '点击向AI助手询问这道题目';
                
                // 添加点击事件
                aiButton.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // 获取题目内容
                    const questionText = getQuestionContent(item);
                    
                    // 检查AI助手是否存在
                    if (window.aiAssistant) {
                        // 构建发送给AI的消息
                        const aiMessage = `请帮我分析这道C++题目：\n\n${questionText}\n\n请详细解释这道题的知识点，并说明正确答案的原因。`;
                        
                        // 打开AI助手并预设消息
                        window.aiAssistant.openWithPresetMessage(aiMessage);
                    } else {
                        alert('AI助手未加载，请刷新页面后重试。');
                    }
                });
                
                // 将按钮添加到题目标题旁边
                questionDiv.appendChild(aiButton);
            }
        });
    }
    
    // 重新组织题目布局
    function reorganizeQuestionLayout(questionDiv) {
        // 如果已经重组过，就不再处理
        if (questionDiv.querySelector('.question-text')) {
            return;
        }
        
        const questionNumber = questionDiv.querySelector('.question-number');
        const textNodes = Array.from(questionDiv.childNodes).filter(node => 
            node.nodeType === Node.TEXT_NODE && node.textContent.trim()
        );
        
        if (textNodes.length > 0) {
            // 创建题目文本容器
            const questionTextSpan = document.createElement('span');
            questionTextSpan.className = 'question-text';
            questionTextSpan.textContent = textNodes[0].textContent.trim();
            
            // 移除原来的文本节点
            textNodes.forEach(node => node.remove());
            
            // 重新插入结构化的内容
            if (questionNumber) {
                questionDiv.insertBefore(questionTextSpan, questionNumber.nextSibling);
            } else {
                questionDiv.insertBefore(questionTextSpan, questionDiv.firstChild);
            }
        }
    }


    // 获取题目完整内容
    function getQuestionContent(quizItem) {
        const questionDiv = quizItem.querySelector('.quiz-question');
        const optionsDiv = quizItem.querySelector('.quiz-options');
        
        // 获取题目文本（移除按钮文本）
        const questionNumber = questionDiv.querySelector('.question-number')?.textContent || '';
        const questionTextNode = Array.from(questionDiv.childNodes)
            .find(node => node.nodeType === Node.TEXT_NODE && node.textContent.trim());
        let questionText = questionTextNode ? questionTextNode.textContent.trim() : 
            questionDiv.textContent.replace(questionNumber, '').replace('问问AI助手', '').trim();
        
        
        // 获取选项文本
        const options = Array.from(optionsDiv.querySelectorAll('.option'))
            .map(option => {
                // 获取选项的innerHTML并移除input标签
                let innerHTML = option.innerHTML.replace(/<input[^>]*>/g, '');
                
                // 创建临时元素来解码HTML实体
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = innerHTML;
                
                // 获取纯文本并清理
                return (tempDiv.textContent || tempDiv.innerText || '').trim();
            })
            .join('\n');
        
        return `${questionNumber} ${questionText}\n\n选项：\n${options}`;
    }
});