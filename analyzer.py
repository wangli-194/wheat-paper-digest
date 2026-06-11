"""
Paper Analyzer - DeepSeek API
专注于小麦抗病 / 植物免疫方向的论文筛选与分析
"""

import json
import logging
import urllib.request
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from fetchers.base import PaperMetadata

logger = logging.getLogger(__name__)


@dataclass
class PaperAnalysis:
    """论文分析结果"""
    paper: PaperMetadata
    analysis_timestamp: str = field(default_factory=lambda: date.today().isoformat())
    # 相关性
    relevance_score: int = 0        # 0-10，AI打分
    relevance_note: str = ""        # AI对相关性的简要说明
    # 正文各节
    publication_info: str = ""
    affiliation: str = ""
    background: str = ""
    methods: str = ""
    results: str = ""
    discussion: str = ""
    innovations: str = ""
    conclusion: str = ""
    # 兼容字段
    summary: str = ""
    innovation: str = ""
    analysis_error: str = ""

    def is_valid(self) -> bool:
        return bool(self.background or self.summary) and not self.analysis_error


class PaperAnalyzer:
    """使用 DeepSeek 进行论文相关性筛选与深度分析"""

    API_URL = "https://api.deepseek.com/v1/chat/completions"
    MODEL   = "deepseek-chat"

    def __init__(self, api_key: Optional[str] = None):
        import os
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY", "")
        if not self.api_key:
            raise ValueError("未提供 DEEPSEEK_API_KEY，请在 .env 中设置")

    # ── 内部工具 ────────────────────────────────────────────────────────────

    def _call(self, messages: list, max_tokens: int = 100) -> str:
        payload = json.dumps({
            "model": self.MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }).encode("utf-8")
        req = urllib.request.Request(
            self.API_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

    # ── Step 1：相关性快速打分 ───────────────────────────────────────────────

    def _score_relevance(self, paper: PaperMetadata) -> tuple[int, str]:
        """
        返回 (score: int 0-10, reason: str)
        10 = 直接研究小麦抗病/抗锈/白粉病等
         7 = 植物抗病机制，有借鉴价值
         4 = 植物生物学，相关性较弱
         1 = 无关
        """
        prompt = f"""你是小麦遗传育种与抗病领域专家。请判断以下论文与【小麦抗病育种/植物抗病机制】的相关程度。

标题：{paper.title}
摘要：{(paper.abstract or '')[:600]}

评分规则（0-10整数）：
- 9-10：直接研究小麦抗病（抗锈病、白粉病、赤霉病、条纹花叶病等）或小麦抗病基因（R基因、NLR等）
- 7-8：植物（水稻、大麦、拟南芥等）抗病机制，对小麦抗病研究有直接参考价值
- 5-6：植物免疫/防御信号通路（SA、JA、ETI、PTI等），间接相关
- 2-4：植物生物学但与抗病无关
- 0-1：非植物领域或完全无关

请只输出JSON，格式：{{"score": 整数, "reason": "一句话说明"}}"""

        try:
            text = self._call([{"role": "user", "content": prompt}], max_tokens=80)
            # 清理可能的markdown代码块
            text = text.strip().strip('`').replace('json', '', 1).strip()
            obj = json.loads(text)
            return int(obj.get("score", 0)), str(obj.get("reason", ""))
        except Exception as e:
            logger.warning(f"评分解析失败: {e}, 原始: {text if 'text' in dir() else '无'}")
            return 0, "评分失败"

    # ── Step 2：深度分析 ─────────────────────────────────────────────────────

    def _deep_analyze(self, paper: PaperMetadata, score: int) -> Dict[str, str]:
        journal   = getattr(paper, 'journal', None) or getattr(paper, 'source', '未知')
        pub_date  = paper.published_date.isoformat() if paper.published_date else "未知"
        authors   = getattr(paper, 'author_str', '') or ''

        prompt = f"""你是小麦遗传育种与抗病领域专家。请对以下论文进行结构化分析，输出供研究人员快速阅读的简报。

【论文信息】
标题：{paper.title}
期刊：{journal}
日期：{pub_date}
作者：{authors[:200]}
摘要：{paper.abstract or '（无摘要）'}

请严格按以下格式输出（每个##标题单独一行，内容紧跟其后）：

## 发表信息
期刊名称、发表日期、DOI（如有）

## 研究单位
第一作者/通讯作者单位（国家/机构）

## 研究背景
研究的科学问题是什么？针对哪种病害或生物学过程？

## 研究方法
核心实验技术（遗传学、组学、生化、显微等）

## 实验结果
主要发现：关键基因/QTL/表型/机制（分条列出）

## 讨论
抗病机制解读或育种应用价值

## 创新点
与已有研究相比，最突出的新发现或新方法

## 与小麦抗病的关联
对小麦抗病育种研究的参考意义（相关性评分：{score}/10）
"""
        try:
            text = self._call([{"role": "user", "content": prompt}], max_tokens=1200)
            return self._parse(text, journal, pub_date)
        except Exception as e:
            raise RuntimeError(f"深度分析失败: {e}")

    def _parse(self, text: str, journal: str, pub_date: str) -> Dict[str, str]:
        sections = {
            "## 发表信息":        "publication_info",
            "## 研究单位":        "affiliation",
            "## 研究背景":        "background",
            "## 研究方法":        "methods",
            "## 实验结果":        "results",
            "## 讨论":            "discussion",
            "## 创新点":          "innovations",
            "## 与小麦抗病的关联": "relevance_note",
        }
        result = {v: "" for v in sections.values()}
        result["summary"] = text

        current = None
        for line in text.split('\n'):
            matched = False
            for header, key in sections.items():
                if line.strip().startswith(header):
                    current = key
                    matched = True
                    break
            if not matched and current and line.strip():
                result[current] += line.strip() + "\n"

        # 兜底：发表信息若为空则用原始数据填充
        if not result["publication_info"]:
            result["publication_info"] = f"{journal}  |  {pub_date}"

        return result

    # ── 公开接口 ────────────────────────────────────────────────────────────

    def analyze_paper(self, paper: PaperMetadata) -> PaperAnalysis:
        try:
            score, reason = self._score_relevance(paper)
        except Exception as e:
            logger.warning(f"相关性评分异常 ({paper.title[:40]}): {e}")
            score, reason = 0, str(e)

        try:
            parsed = self._deep_analyze(paper, score)
            return PaperAnalysis(
                paper=paper,
                relevance_score=score,
                relevance_note=parsed.get("relevance_note", reason),
                publication_info=parsed.get("publication_info", ""),
                affiliation=parsed.get("affiliation", ""),
                background=parsed.get("background", ""),
                methods=parsed.get("methods", ""),
                results=parsed.get("results", ""),
                discussion=parsed.get("discussion", ""),
                innovations=parsed.get("innovations", ""),
                summary=parsed.get("summary", ""),
                innovation=parsed.get("innovations", ""),
                analysis_error="",
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"分析失败 ({paper.title[:50]}): {error_msg}")
            return PaperAnalysis(
                paper=paper,
                relevance_score=score,
                relevance_note=reason,
                summary=f"分析失败: {error_msg}",
                analysis_error=error_msg,
            )

    def analyze_papers(
        self,
        papers: List[PaperMetadata],
        relevance_threshold: int = 6,
        target_count: int = 6,
        max_to_analyze: int = 20,
    ) -> List[PaperAnalysis]:
        """
        两阶段流程：
        1. 快速打分，过滤低相关论文
        2. 对高分论文做深度分析，取最多 target_count 篇
        """
        from config import RELEVANCE_THRESHOLD, TARGET_PAPERS, MAX_PAPERS_TO_ANALYZE
        relevance_threshold = relevance_threshold or RELEVANCE_THRESHOLD
        target_count        = target_count        or TARGET_PAPERS
        max_to_analyze      = max_to_analyze      or MAX_PAPERS_TO_ANALYZE

        # ── 阶段1：快速评分 ──────────────────────────────────────────────────
        logger.info(f"阶段1：对 {len(papers)} 篇论文进行相关性评分...")
        scored = []
        for i, paper in enumerate(papers):
            logger.info(f"  评分 {i+1}/{len(papers)}: {paper.title[:50]}...")
            try:
                score, reason = self._score_relevance(paper)
            except Exception as e:
                score, reason = 0, str(e)
            scored.append((score, reason, paper))
            logger.info(f"    → 评分: {score}/10  {reason}")

        # 按分数降序，取高于阈值的前 max_to_analyze 篇
        scored.sort(key=lambda x: x[0], reverse=True)
        candidates = [(s, r, p) for s, r, p in scored if s >= relevance_threshold]
        candidates = candidates[:max_to_analyze]

        if not candidates:
            logger.warning(f"今日没有论文达到相关性阈值（{relevance_threshold}/10），本期无相关内容。")
            return []  # 不凑数，直接返回空

        logger.info(f"阶段1完成：{len(candidates)} 篇进入深度分析")

        # ── 阶段2：深度分析 ──────────────────────────────────────────────────
        logger.info(f"阶段2：深度分析 {len(candidates)} 篇...")
        results = []
        for i, (score, reason, paper) in enumerate(candidates):
            logger.info(f"  分析 {i+1}/{len(candidates)}: {paper.title[:50]}...")
            analysis = self.analyze_paper(paper)
            if analysis.relevance_score == 0:
                analysis.relevance_score = score
            if not analysis.relevance_note:
                analysis.relevance_note = reason
            results.append(analysis)

        # 按相关性分数排序，最相关在前，最多返回 target_count 篇
        results.sort(key=lambda a: a.relevance_score, reverse=True)
        return results[:target_count]
