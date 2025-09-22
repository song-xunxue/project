// 默认配置数据 - JavaScript版本
// 此文件用于解决file://协议下无法加载JSON文件的问题
window.DEFAULT_CONFIG = {
  "users": [
    {
      "username": "admin",
      "email": "admin@cplusplus-learning.com",
      "password": "admin123",
      "avatar": "images/admin头像.png",
      "motto": "C++学习网站管理员 | 欢迎大家交流学习"
    },
    {
      "username": "助教小C",
      "email": "assistant@cplusplus-learning.com", 
      "password": "assistant123",
      "avatar": "images/助教小C头像.png",
      "motto": "C++学习助教 | 随时为大家答疑解惑"
    }
  ],
  "forumPosts": [
    {
      "id": 1000000001,
      "title": "欢迎来到C++学习论坛！",
      "category": "other",
      "content": "欢迎大家来到C++学习论坛！\n\n这里是一个专门为C++学习者建立的交流平台，无论你是初学者还是有经验的程序员，都可以在这里：\n\n• 提出学习中遇到的问题\n• 分享编程经验和技巧\n• 讨论C++最新动态和技术\n• 互相帮助，共同进步\n\n论坛规则：\n1. 请保持友善和尊重的交流氛围\n2. 发帖前请选择合适的分类\n3. 提问时请尽量提供详细的问题描述和代码\n4. 鼓励大家积极回复和帮助他人\n\n让我们一起在C++的学习路上互相支持，共同成长！",
      "author": {
        "username": "admin",
        "email": "admin@cplusplus-learning.com"
      },
      "createdAt": "2025-09-13T08:00:00.000Z",
      "likes": [],
      "replies": [
        {
          "id": 2000000001,
          "content": "感谢管理员的欢迎！作为助教，我会经常在论坛里为大家答疑解惑。有任何C++学习问题都可以随时提出哦！",
          "author": {
            "username": "助教小C",
            "email": "assistant@cplusplus-learning.com"
          },
          "createdAt": "2025-09-13T08:30:00.000Z"
        }
      ]
    },
    {
      "id": 1000000002,
      "title": "C++基础语法学习路线推荐",
      "category": "basic",
      "content": "很多初学者问如何系统地学习C++基础语法，这里给大家推荐一个学习路线：\n\n**第一阶段：入门基础**\n• 变量和数据类型\n• 运算符和表达式\n• 控制流（if/else, while, for）\n• 数组和字符串\n\n**第二阶段：函数和作用域**\n• 函数定义和调用\n• 参数传递（值传递、引用传递、指针传递）\n• 变量作用域和生命周期\n• 递归函数\n\n**第三阶段：指针和内存管理**\n• 指针的概念和使用\n• 动态内存分配（new/delete）\n• 指针与数组、函数的关系\n• 智能指针简介\n\n建议大家按这个顺序循序渐进地学习，每个知识点都要多写代码练习！",
      "author": {
        "username": "助教小C",
        "email": "assistant@cplusplus-learning.com"
      },
      "createdAt": "2025-09-13T09:15:00.000Z",
      "likes": [],
      "replies": [
        {
          "id": 2000000002,
          "content": "助教小C总结得很全面！我特别赞同循序渐进的学习方法。补充一点：在学习指针之前，建议先熟练掌握引用的概念，这样理解指针会更容易一些。",
          "author": {
            "username": "admin",
            "email": "admin@cplusplus-learning.com"
          },
          "createdAt": "2025-09-13T09:45:00.000Z"
        }
      ]
    },
    {
      "id": 1000000003,
      "title": "面向对象编程核心概念解析",
      "category": "oop",
      "content": "面向对象编程是C++的核心特性之一，这里为大家总结OOP的四大核心概念：\n\n**1. 封装（Encapsulation）**\n• 将数据和操作数据的方法绑定在一起\n• 使用访问控制符（public, private, protected）隐藏内部实现\n• 提供统一的接口供外部使用\n\n**2. 继承（Inheritance）**\n• 子类可以继承父类的属性和方法\n• 实现代码复用和层次化设计\n• 支持单继承和多继承\n\n**3. 多态（Polymorphism）**\n• 同一接口可以有不同的实现\n• 虚函数和动态绑定\n• 运行时决定调用哪个函数\n\n**4. 抽象（Abstraction）**\n• 抽象类和纯虚函数\n• 定义接口规范\n• 隐藏具体实现细节\n\n理解这些概念是掌握C++面向对象编程的关键！",
      "author": {
        "username": "admin",
        "email": "admin@cplusplus-learning.com"
      },
      "createdAt": "2025-09-13T10:30:00.000Z",
      "likes": [],
      "replies": [
        {
          "id": 2000000003,
          "content": "管理员讲解得很清楚！对于初学者，我建议先从封装开始理解，因为这是最容易上手的。可以先写几个简单的类，体验一下public和private的区别。",
          "author": {
            "username": "助教小C",
            "email": "assistant@cplusplus-learning.com"
          },
          "createdAt": "2025-09-13T11:00:00.000Z"
        }
      ]
    },
    {
      "id": 1000000004,
      "title": "STL容器选择指南",
      "category": "stl",
      "content": "STL提供了丰富的容器类，选择合适的容器对程序性能很重要：\n\n**序列容器：**\n• **vector**: 动态数组，支持随机访问，尾部插入删除效率高\n• **deque**: 双端队列，两端插入删除都很高效\n• **list**: 双向链表，任意位置插入删除高效，但不支持随机访问\n\n**关联容器：**\n• **set/multiset**: 有序集合，自动排序，查找效率O(log n)\n• **map/multimap**: 键值对容器，按键有序存储\n\n**无序容器（C++11）：**\n• **unordered_set**: 哈希集合，平均查找O(1)\n• **unordered_map**: 哈希映射，键值对存储\n\n**选择建议：**\n• 需要频繁随机访问 → vector\n• 需要频繁插入删除 → list\n• 需要有序存储和快速查找 → set/map\n• 需要最快的查找速度 → unordered_set/map",
      "author": {
        "username": "助教小C",
        "email": "assistant@cplusplus-learning.com"
      },
      "createdAt": "2025-09-13T11:45:00.000Z",
      "likes": [],
      "replies": [
        {
          "id": 2000000004,
          "content": "这个容器选择指南太实用了！我想补充一个性能测试的建议：如果不确定用哪个容器，可以写个小测试比较一下插入、删除、查找的性能，数据会告诉你答案。",
          "author": {
            "username": "admin",
            "email": "admin@cplusplus-learning.com"
          },
          "createdAt": "2025-09-13T12:15:00.000Z"
        }
      ]
    },
    {
      "id": 1000000005,
      "title": "常见编程错误和调试技巧",
      "category": "debug",
      "content": "总结一些C++初学者常犯的错误和调试方法：\n\n**常见错误：**\n1. **内存泄漏**: 忘记delete动态分配的内存\n2. **数组越界**: 访问超出数组范围的元素\n3. **空指针解引用**: 使用nullptr或未初始化的指针\n4. **对象生命周期**: 使用已销毁对象的引用或指针\n5. **拷贝构造**: 浅拷贝导致的问题\n\n**调试技巧：**\n• 使用IDE的调试器设置断点\n• 添加cout输出查看变量值\n• 使用assert断言检查条件\n• 启用编译器警告（-Wall）\n• 使用静态分析工具\n• 使用内存检查工具（如Valgrind）\n\n**预防措施：**\n• 使用智能指针代替原始指针\n• 初始化所有变量\n• 遵循RAII原则\n• 编写单元测试\n\n记住：好的编程习惯比事后调试更重要！",
      "author": {
        "username": "admin",
        "email": "admin@cplusplus-learning.com"
      },
      "createdAt": "2025-09-13T13:20:00.000Z",
      "likes": [],
      "replies": [
        {
          "id": 2000000005,
          "content": "管理员总结的调试技巧很全面！我想特别强调一下RAII原则的重要性，很多内存问题都可以通过正确使用智能指针和RAII来避免。初学者可以从unique_ptr开始练习。",
          "author": {
            "username": "助教小C",
            "email": "assistant@cplusplus-learning.com"
          },
          "createdAt": "2025-09-13T13:50:00.000Z"
        }
      ]
    },
    {
      "id": 1000000006,
      "title": "C++现代特性简介（C++11/14/17）",
      "category": "advanced",
      "content": "现代C++引入了许多实用的新特性，这里介绍几个重要的：\n\n**C++11核心特性：**\n• **auto关键字**: 自动类型推导\n• **range-based for**: 范围for循环\n• **智能指针**: unique_ptr, shared_ptr, weak_ptr\n• **移动语义**: 右值引用和移动构造函数\n• **lambda表达式**: 匿名函数\n\n**C++14改进：**\n• **泛型lambda**: lambda可以使用auto参数\n• **变量模板**: 模板变量\n• **返回类型推导**: 函数返回类型auto\n\n**C++17新特性：**\n• **结构化绑定**: auto [a, b] = std::make_pair(1, 2)\n• **if constexpr**: 编译时条件分支\n• **std::optional**: 可选值类型\n• **std::variant**: 联合类型\n\n**使用建议：**\n• 优先使用现代C++特性\n• 合理使用auto，但不要过度依赖\n• 用智能指针管理内存\n• 学会使用lambda简化代码\n\n现代C++让代码更安全、更简洁、更易维护！",
      "author": {
        "username": "助教小C",
        "email": "assistant@cplusplus-learning.com"
      },
      "createdAt": "2025-09-13T14:50:00.000Z",
      "likes": [],
      "replies": [
        {
          "id": 2000000006,
          "content": "现代C++特性的介绍很详细！我特别推荐大家尝试使用auto和range-based for，这两个特性能让代码更简洁。不过要注意auto的使用场合，有时明确的类型声明更利于代码理解。",
          "author": {
            "username": "admin",
            "email": "admin@cplusplus-learning.com"
          },
          "createdAt": "2025-09-13T15:20:00.000Z"
        }
      ]
    }
  ],
  "userQuizData": {},
  "userAchievements": {},
  "exportTime": "2025-09-13T00:00:00.000Z",
  "version": "2.6"
};
