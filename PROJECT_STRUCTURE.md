# 🏗️ Dance项目重构结构说明

## 📁 **清理后的项目结构**

```
dance/
├── 📁 src/                          # 源代码目录
│   ├── 📁 core/                     # 核心模块
│   │   ├── __init__.py
│   │   └── task_database.py         # 任务数据库管理
│   ├── 📁 automation/               # 自动化模块
│   │   ├── __init__.py
│   │   ├── viggle_automation.py     # Viggle自动化
│   │   ├── google_oauth_auth.py     # Google OAuth认证
│   │   ├── oauth_demo.py           # OAuth演示
│   │   └── oauth_server.py         # OAuth服务器
│   ├── 📁 processing/               # 视频处理模块
│   │   ├── __init__.py
│   │   ├── background_generator.py  # 背景生成器
│   │   ├── background_replacement.py # 背景替换器
│   │   └── rtx3060_pipeline.py      # RTX3060 GPU Pipeline
│   ├── 📁 utils/                    # 工具模块
│   │   └── __init__.py
│   ├── 📁 config/                   # 配置模块
│   │   ├── config_example.json
│   │   ├── config_multi_account_example.json
│   │   ├── requirements.txt
│   │   └── requirements_playwright.txt
│   └── __init__.py                  # 主包初始化
├── 📁 tests/                        # 测试目录
│   ├── 📁 unit/                     # 单元测试
│   │   ├── test_background_pipeline.py
│   │   ├── test_database.py
│   │   ├── test_pw_module.py
│   │   ├── test_system.py
│   │   └── test_cross_platform_paths.py
│   ├── 📁 integration/              # 集成测试
│   │   ├── demo_background_flow.py
│   │   └── check_viggle_audio.py
│   ├── 📁 e2e/                      # 端到端测试
│   │   └── (待添加)
│   └── __init__.py
├── 📁 tools/                        # 工具脚本
│   ├── check_environment.py         # 环境检查
│   ├── create_backgrounds.py        # 背景创建
│   ├── task_monitor.py              # 任务监控
│   ├── setup_directories.py         # 目录设置
│   ├── setup_playwright.py          # Playwright设置
│   └── login_once.py                # 一次性登录
├── 📁 scripts/                      # 脚本目录
│   ├── 📁 legacy/                   # 旧版本脚本
│   │   ├── viggle_playwright_optimized.py
│   │   ├── viggle_playwright_loguru.py
│   │   ├── viggle_playwright_multi_account.py
│   │   ├── viggle_auto_processor.py
│   │   └── loguru_logger_enhanced.py
│   └── (其他脚本)
├── 📁 docs/                         # 文档目录
│   ├── requirements_and_setup_guide.md
│   ├── technology_stack.md
│   ├── tech_stack_summary.md
│   └── (其他文档)
├── 📁 apps/                         # 应用目录
│   ├── 📁 mobile/                   # 移动应用
│   │   └── README.md
│   └── 📁 web/                      # Web应用
│       └── README.md
├── 📁 config/                       # 配置文件
├── 📁 backgrounds/                  # 背景素材
├── 📁 input/                        # 输入素材
│   ├── 📁 people/                   # 人物图片
│   ├── 📁 music/                    # 音乐文件
│   └── 📁 videos/                   # 视频文件
├── 📁 tasks_in/                     # 输入视频
├── 📁 downloads/                    # Viggle输出
├── 📁 final_output/                 # 最终输出
├── 📁 temp_backgrounds/             # 临时背景
├── 📁 temp_gpu/                     # GPU临时文件
├── 📁 logs/                         # 日志文件
├── 📁 tasks/                        # 任务数据
├── 📁 preprocessing_reports/        # 预处理报告
├── 📁 quarantine_videos/            # 隔离视频
├── main.py                          # 新主入口
├── dance_main.py                    # 旧主入口(保留)
├── setup_viggle.py                  # Viggle设置脚本
├── README.md                        # 项目说明
├── CHECKLIST.md                     # 检查清单
├── README_VIGGLE.md                 # Viggle说明
├── README_MODULES.md                # 模块说明
├── QUICK_START.md                   # 快速开始
├── CROSS_PLATFORM_COMPATIBILITY.md  # 跨平台兼容性
└── PROJECT_STRUCTURE.md             # 本文档
```

## 🔄 **重构变更说明**

### **1. 代码组织优化**
- **src/**: 所有源代码集中管理
- **core/**: 核心功能模块
- **automation/**: 自动化相关功能
- **processing/**: 视频处理功能
- **utils/**: 通用工具函数
- **config/**: 配置文件管理

### **2. 测试结构优化**
- **tests/unit/**: 单元测试
- **tests/integration/**: 集成测试
- **tests/e2e/**: 端到端测试

### **3. 工具脚本优化**
- **tools/**: 实用工具脚本
- **scripts/legacy/**: 旧版本脚本保留

### **4. 入口文件更新**
- **main.py**: 新的主入口文件
- **dance_main.py**: 旧入口文件保留

### **5. 目录清理优化**
- **删除重复模块**: 移除旧的 `modules/` 目录
- **合并重复目录**: 统一输入输出目录结构
- **删除空目录**: 清理无用的空目录
- **简化应用结构**: 保留核心的 mobile 和 web 应用

## 🚀 **使用新结构**

### **运行主程序**
```bash
# 新方式
python main.py status
python main.py full --test-mode
python main.py background --background dance --effects zoom

# 旧方式(仍然可用)
python dance_main.py status
```

### **运行测试**
```bash
# 单元测试
python -m pytest tests/unit/

# 集成测试
python tests/integration/demo_background_flow.py
python tests/integration/check_viggle_audio.py

# 环境检查
python tools/check_environment.py
```

### **导入模块**
```python
# 新方式
from src.core import task_database
from src.automation import viggle_automation
from src.processing import background_generator

# 旧方式(仍然可用)
from scripts import task_database
```

## 📋 **迁移检查清单**

### **已完成**
- [x] 创建新的目录结构
- [x] 移动核心模块到src/
- [x] 移动测试文件到tests/
- [x] 移动工具脚本到tools/
- [x] 创建包初始化文件
- [x] 创建新的主入口文件
- [x] 删除重复的旧模块
- [x] 合并重复目录
- [x] 清理空目录

### **待完成**
- [ ] 更新导入路径
- [ ] 修复模块依赖
- [ ] 更新配置文件路径
- [ ] 测试新结构功能
- [ ] 更新文档引用

## 💡 **优势**

### **1. 清晰的结构**
- 按功能分类组织代码
- 便于维护和扩展
- 符合Python项目标准

### **2. 更好的测试**
- 分离单元测试和集成测试
- 便于自动化测试
- 提高代码质量

### **3. 工具集中管理**
- 实用工具统一管理
- 便于查找和使用
- 减少重复代码

### **4. 向后兼容**
- 保留旧入口文件
- 渐进式迁移
- 降低迁移风险

### **5. 目录精简**
- 删除重复和空目录
- 减少项目复杂度
- 提高维护效率

## 🔧 **下一步**

1. **修复导入路径**: 更新所有模块的导入语句
2. **测试功能**: 验证新结构下的功能正常
3. **更新文档**: 更新所有文档中的路径引用
4. **性能优化**: 优化模块加载和依赖管理
5. **CI/CD集成**: 更新持续集成配置

这个重构使项目结构更加清晰和专业，便于团队协作和长期维护！🎉
