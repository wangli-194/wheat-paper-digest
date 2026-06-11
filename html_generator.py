"""
HTML Generator - 小麦抗病·植物免疫论文日报
卡片式布局，浏览器直接打开
"""
from __future__ import annotations
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from analyzer import PaperAnalysis
from config import OUTPUT_DIR

logger = logging.getLogger(__name__)

def _esc(s: str) -> str:
    return (s or "").replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

def _score_class(score: int) -> str:
    if score >= 8: return "hi"
    if score >= 6: return "mid"
    return "lo"

def _score_label(score: int) -> str:
    if score >= 8: return "🌾 小麦直接相关"
    if score >= 6: return "🌿 植物抗病相关"
    return "📄 低相关"

def _card(idx: int, a: PaperAnalysis) -> str:
    p = a.paper
    score = a.relevance_score
    sc = _score_class(score)
    journal = _esc(getattr(p, 'source', '') or '')
    pub_date = str(p.published_date) if p.published_date else ''
    doi = getattr(p, 'doi', '') or ''
    url = getattr(p, 'url', '') or doi and f"https://doi.org/{doi}" or ''
    authors = _esc((getattr(p, 'author_str', '') or '') [:120])

    def section(icon, label, content):
        if not content or not content.strip(): return ''
        lines = [f"<li>{_esc(l.lstrip('-•· '))}</li>" for l in content.strip().splitlines() if l.strip()]
        body = "<ul>" + "".join(lines) + "</ul>" if lines else ""
        return f"""
        <div class="sec">
          <div class="sec-title">{icon} {label}</div>
          <div class="sec-body">{body}</div>
        </div>"""

    link_btn = f'<a class="btn" href="{_esc(url)}" target="_blank">🔗 原文</a>' if url else ''

    return f"""
<div class="card {sc}">
  <div class="card-header">
    <div class="card-num">{idx:02d}</div>
    <div class="card-meta">
      <div class="card-title">{_esc(p.title)}</div>
      <div class="card-sub">
        <span class="tag journal">{journal}</span>
        <span class="tag date">📅 {pub_date}</span>
        <span class="tag score {sc}">★ {score}/10 &nbsp;{_score_label(score)}</span>
      </div>
      {f'<div class="authors">👤 {authors}</div>' if authors else ''}
    </div>
  </div>
  <div class="card-body">
    <div class="cols">
      <div class="col">
        {section("🏛", "研究单位", a.affiliation)}
        {section("🔬", "研究背景", a.background)}
        {section("🧪", "研究方法", a.methods)}
      </div>
      <div class="col">
        {section("📊", "实验结果", a.results)}
        {section("💬", "讨论", a.discussion)}
        {section("⭐", "创新点", a.innovations)}
        {section("🌾", "与小麦抗病的关联", a.relevance_note)}
      </div>
    </div>
  </div>
  <div class="card-footer">
    {link_btn}
    {f'<span class="doi">DOI: {_esc(doi)}</span>' if doi else ''}
  </div>
</div>"""


class HtmlGenerator:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or OUTPUT_DIR

    def generate(self, analyses: list[PaperAnalysis], fetch_date: Optional[date] = None) -> Path:
        fetch_date = fetch_date or date.today()
        valid   = [a for a in analyses if a.is_valid()]
        invalid = [a for a in analyses if not a.is_valid()]
        hi  = [a for a in valid if a.relevance_score >= 8]
        mid = [a for a in valid if 6 <= a.relevance_score < 8]

        cards_html = "\n".join(_card(i+1, a) for i, a in enumerate(valid))

        # 附录（低相关/失败）
        appendix = ""
        if invalid:
            rows = ""
            for a in invalid:
                p = a.paper
                rows += f"<tr><td>{_esc(p.title)}</td><td>{_esc(getattr(p,'source',''))}</td><td>{p.published_date or ''}</td><td>{a.relevance_score}/10</td></tr>"
            appendix = f"""
<div class="appendix">
  <h2>📋 附录：低相关论文（{len(invalid)} 篇）</h2>
  <table><thead><tr><th>标题</th><th>期刊</th><th>日期</th><th>评分</th></tr></thead>
  <tbody>{rows}</tbody></table>
</div>"""

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🌾 小麦抗病论文日报 {fetch_date.strftime('%Y-%m-%d')}</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:"Microsoft YaHei",Arial,sans-serif;background:#f0f4f0;color:#222;font-size:14px;line-height:1.6}}
a{{color:#1a6b2f;text-decoration:none}}
a:hover{{text-decoration:underline}}

/* ── 顶栏 ── */
.topbar{{background:linear-gradient(135deg,#1a6b2f 0%,#2e7d50 60%,#c89620 100%);
  color:#fff;padding:24px 32px 20px;position:sticky;top:0;z-index:100;
  box-shadow:0 2px 12px rgba(0,0,0,.25)}}
.topbar h1{{font-size:22px;font-weight:700;letter-spacing:1px}}
.topbar .sub{{font-size:12px;opacity:.85;margin-top:4px}}
.stats{{display:flex;gap:24px;margin-top:14px;flex-wrap:wrap}}
.stat-box{{background:rgba(255,255,255,.15);border-radius:8px;padding:8px 18px;text-align:center;min-width:80px}}
.stat-box .num{{font-size:26px;font-weight:700}}
.stat-box .lbl{{font-size:11px;opacity:.8}}

/* ── 主体 ── */
.main{{max-width:1300px;margin:24px auto;padding:0 16px}}

/* ── 卡片 ── */
.card{{background:#fff;border-radius:12px;margin-bottom:20px;
  box-shadow:0 2px 8px rgba(0,0,0,.08);overflow:hidden;
  border-left:5px solid #ccc;transition:box-shadow .2s}}
.card:hover{{box-shadow:0 4px 20px rgba(0,0,0,.14)}}
.card.hi{{border-left-color:#c89620}}
.card.mid{{border-left-color:#1a6b2f}}
.card.lo{{border-left-color:#aaa}}

.card-header{{padding:16px 20px 12px;display:flex;gap:14px;align-items:flex-start;
  background:#fafafa;border-bottom:1px solid #eee}}
.card-num{{font-size:28px;font-weight:700;color:#ddd;min-width:40px;line-height:1}}
.card-meta{{flex:1}}
.card-title{{font-size:15px;font-weight:700;color:#1a3a2a;line-height:1.45;margin-bottom:8px}}
.card-sub{{display:flex;flex-wrap:wrap;gap:6px;align-items:center}}
.tag{{display:inline-block;padding:2px 10px;border-radius:20px;font-size:11px;font-weight:600}}
.tag.journal{{background:#e8f5e9;color:#1a6b2f}}
.tag.date{{background:#f3f3f3;color:#666}}
.tag.score.hi{{background:#fff3cd;color:#b85c00}}
.tag.score.mid{{background:#e8f5e9;color:#1a6b2f}}
.tag.score.lo{{background:#f5f5f5;color:#999}}
.authors{{font-size:11px;color:#888;margin-top:6px}}

.card-body{{padding:16px 20px}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
@media(max-width:800px){{.cols{{grid-template-columns:1fr}}}}

.sec{{margin-bottom:12px}}
.sec-title{{font-size:12px;font-weight:700;color:#2e7d50;margin-bottom:4px;
  border-bottom:1px solid #e8f5e9;padding-bottom:3px}}
.sec-body{{font-size:13px;color:#333}}
.sec-body ul{{padding-left:16px}}
.sec-body li{{margin-bottom:3px}}

.card-footer{{padding:10px 20px;background:#fafafa;border-top:1px solid #eee;
  display:flex;align-items:center;gap:12px}}
.btn{{display:inline-block;padding:5px 16px;background:#1a6b2f;color:#fff!important;
  border-radius:6px;font-size:12px;font-weight:600}}
.btn:hover{{background:#145523;text-decoration:none!important}}
.doi{{font-size:11px;color:#aaa}}

/* ── 附录 ── */
.appendix{{background:#fff;border-radius:12px;padding:20px;margin-top:24px;
  box-shadow:0 2px 8px rgba(0,0,0,.06)}}
.appendix h2{{font-size:14px;color:#888;margin-bottom:12px}}
.appendix table{{width:100%;border-collapse:collapse;font-size:12px}}
.appendix th{{background:#f5f5f5;padding:8px;text-align:left;font-weight:600;color:#555}}
.appendix td{{padding:7px 8px;border-bottom:1px solid #f0f0f0;color:#666}}

/* ── 页脚 ── */
.footer{{text-align:center;padding:28px;color:#aaa;font-size:11px;margin-top:16px}}
</style>
</head>
<body>

<div class="topbar">
  <h1>🌾 小麦抗病 · 植物免疫  论文日报</h1>
  <div class="sub">
    {fetch_date.strftime('%Y年%m月%d日')} &nbsp;·&nbsp;
    数据来源：PubMed · bioRxiv · Nature Plants · Molecular Plant · Plant Cell 等 &nbsp;·&nbsp;
    生成时间：{datetime.now().strftime('%H:%M')}
  </div>
  <div class="stats">
    <div class="stat-box"><div class="num">{len(valid)}</div><div class="lbl">本期论文</div></div>
    <div class="stat-box"><div class="num">{len(hi)}</div><div class="lbl">🌾 小麦直接相关</div></div>
    <div class="stat-box"><div class="num">{len(mid)}</div><div class="lbl">🌿 植物抗病相关</div></div>
    <div class="stat-box"><div class="num">7</div><div class="lbl">回溯天数</div></div>
  </div>
</div>

<div class="main">
  {cards_html}
  {appendix}
</div>

<div class="footer">
  本简报由 Paper Digest Bot 自动生成 · DeepSeek AI 分析 · 内容仅供参考，请结合原文判断
</div>

</body>
</html>"""

        self.output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"小麦抗病论文日报_{fetch_date.strftime('%Y%m%d')}.html"
        filepath = self.output_dir / filename
        filepath.write_text(html, encoding="utf-8")
        logger.info("HTML saved: %s", filepath)
        return filepath
