# 🌾 小麦抗病·植物免疫 论文日报

自动从 PubMed、bioRxiv、Nature Plants 等期刊检索小麦抗病和植物免疫方向的最新论文，使用 DeepSeek AI 进行相关性筛选和结构化分析，每天生成一份卡片式 HTML 简报。

## 效果预览

每篇论文以卡片形式展示，包含：
- 🌾 相关性评分（小麦直接相关 / 植物抗病相关）
- 🏛 研究单位
- 🔬 研究背景
- 🧪 研究方法
- 📊 实验结果
- 💬 讨论
- ⭐ 创新点
- 🌾 与小麦抗病育种的关联

## 数据来源

| 数据源 | 说明 |
|--------|------|
| PubMed | NCBI 文献数据库，覆盖所有主流期刊 |
| bioRxiv | 生物学预印本 |
| Nature Plants | 植物学顶刊 |
| Molecular Plant | 植物分子生物学顶刊 |
| The Plant Cell | 植物细胞生物学权威期刊 |
| New Phytologist | 植物生态与生理 |
| Molecular Plant Pathology | 植物病理专业期刊 |
| Plant Disease / Phytopathology | APS 旗舰期刊 |
| Frontiers in Plant Science | 开放获取，发文量大 |
| ... | 共 20+ 个数据源 |

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/你的用户名/wheat-paper-digest.git
cd wheat-paper-digest
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API Key

复制示例文件并填入你的密钥：

```bash
copy .env.example .env
```

用记事本打开 `.env`，填入：

```
DEEPSEEK_API_KEY=你的DeepSeek API Key
PUBMED_EMAIL=你的邮箱（PubMed要求，随便填一个）
```

DeepSeek API Key 在 [platform.deepseek.com](https://platform.deepseek.com) 注册后获取，费用极低（约¥1可分析500篇论文）。

## 使用方法

### 立即运行一次

```bash
python main.py
```

生成的 HTML 简报在 `output/` 文件夹，用浏览器打开即可。

### 每天定时运行（Windows 任务计划）

1. 按 `Win+R`，输入 `taskschd.msc`
2. 创建基本任务，每天 08:00 执行
3. 程序：`python.exe` 的完整路径
4. 参数：`main.py`
5. 起始位置：本项目文件夹路径

### 守护进程模式

```bash
python main.py --schedule 08:00
```

### 常用参数

```bash
python main.py --lookback 7      # 检索最近7天（默认7天）
python main.py --lookback 3      # 检索最近3天
```

## 筛选逻辑

采用两阶段 AI 筛选：

1. **快速评分**：DeepSeek 对每篇论文打相关性分数（0-10分）
   - 9-10分：直接研究小麦抗病（锈病/白粉病/赤霉病等）
   - 7-8分：植物抗病机制，对小麦研究有参考价值
   - 5-6分：植物免疫信号通路，间接相关
   - 低于5分：过滤不收录

2. **深度分析**：对高分论文进行结构化分析，生成各维度摘要

每期收录约 6-8 篇最相关论文。

## 配置说明

编辑 `config.py` 可调整：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `LOOKBACK_DAYS` | 7 | 检索回溯天数 |
| `TARGET_PAPERS` | 8 | 每期目标篇数 |
| `RELEVANCE_THRESHOLD` | 5 | 相关性最低分数 |
| `MAX_PAPERS_TO_ANALYZE` | 30 | 最多送 AI 分析篇数 |

## 项目结构

```
wheat-paper-digest/
├── main.py              # 主程序入口
├── config.py            # 配置文件（关键词、期刊、参数）
├── analyzer.py          # DeepSeek AI 分析模块
├── html_generator.py    # HTML 简报生成器
├── fetchers/            # 各期刊数据抓取模块
│   ├── pubmed.py        # PubMed / NCBI
│   ├── biorxiv.py       # bioRxiv
│   ├── nature.py        # Nature 系列
│   ├── cell.py          # Cell / Molecular Plant 等
│   └── wiley.py         # Wiley 系列
├── notifier.py          # 邮件通知模块
├── .env.example         # 环境变量示例
├── requirements.txt     # Python 依赖
└── output/              # 生成的简报（不含在仓库中）
```

## 作者

作物遗传育种 / 小麦抗病方向研究者开发，欢迎同领域研究者使用和改进。

## License

MIT License
