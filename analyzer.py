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
    relevance_score: int = 0
    relevance_note: str = ""
    publication_info: str = ""
    affiliation: str = ""
    background: str = ""
    methods: str = ""
    results: str = ""
    discussion: str = ""
    innovations: str = ""
    conclusion: str = ""
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

    def _score_relevance(self, paper: PaperMetadata) -> tuple:
        prompt = f"""你是小麦遗传育种与抗病领域专家。请判断以下论文与【小麦抗病育种/植物抗病机制】的相关程度。

标题：{paper.title}
摘要：{(paper.abstract or '')[:600]}

评分规则（0-10整数）：
- 9-10：直接研究小麦抗病（抗锈病、白粉病、赤霉病等）或小麦抗病基因
- 7-8：植物抗病机制，对小麦抗病研究有直接参考价值
- 5-6：植物免疫/防御信号通路，间接相关
- 2-4：植物生物学但与抗病无关
- 0-1：非植物领域或完全无关

请只输出JSON，格式：{{"score": 整数, "reason": "一句话说明"}}"""

        try:
            text = self._call([{"role": "user", "content": prompt}], max_tokens=80)
            text = text.strip().strip('`').replace('json', '', 1).strip()
            obj = json.loads(text)
            return int(obj.get("score", 0)), str(obj.get("reason", ""))
        except Exception as e:
            logger.warning(f"评分解析失败: {e}")
            return 0, "评分失败"

    def _deep_analyze(self, paper: PaperMetadata, score: int) -> Dict[str, str]:
        journal  = getattr(paper, 'journal', None) or getattr(paper, 'source', '未知')
        pub_date = paper.published_date.isoformat() if paper.published_date else '未知'
        authors  = ', '.join(getattr(paper, 'authors', [])[:5] or [])

        prompt = f"""你是小麦遗传育种与抗病领域专家。请基于以下论文信息进行结构化分析。

【重要原则】严格只根据下方摘要内容分析，不得推测或补充摘要中没有的信息。若摘要未提及某项内容，直接写"摘要未提及"。

标题：{paper.title}
期刊：{journal} | 日期：{pub_date}
作者：{authors}
摘要：{paper.abstract or "（无摘要，仅凭标题简要分析）"}

请按以下格式输出（每个##标题单独一行，内容2-4句）：

## 发表信息
期刊和日期

## 研究单位
作者所在机构（仅填写摘要/作者信息中明确出现的，否则写"未提供"）

## 研究背景
针对什么病害或科学问题

## 研究方法
核心实验技术（无则写"摘要未提及"）

## 实验结果
主要发现（基因/QTL/表型/机制）

## 讨论
育种应用价值或抗病机制（无则写"摘要未提及"）

## 创新点
与已有研究相比最突出的新发现

## 与小麦抗病的关联
对小麦抗病育种的参考意义，相关性评分：{score}/10
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

        if not result["publication_info"]:
            result["publication_info"] = f"{journal}  |  {pub_date}"

        return result

    def analyze_paper(self, paper: PaperMetadata) -> PaperAnalysis:
        try:
            score, reason = self._score_relevance(paper)
        except Exception as e:
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
        relevance_threshold: int = 5,
        target_count: int = 8,
        max_to_analyze: int = 30,
    ) -> List[PaperAnalysis]:
        """两阶段：先评分过滤，再深度分析"""
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

        scored.sort(key=lambda x: x[0], reverse=True)
        candidates = [(s, r, p) for s, r, p in scored if s >= relevance_threshold]
        candidates = candidates[:max_to_analyze]

        if not candidates:
            logger.warning(f"今日没有论文达到相关性阈值（{relevance_threshold}/10），本期无相关内容。")
            return []

        logger.info(f"阶段1完成：{len(candidates)} 篇进入深度分析")
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

        results.sort(key=lambda a: a.relevance_score, reverse=True)
        return results[:target_count]
