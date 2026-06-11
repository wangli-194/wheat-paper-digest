#!/usr/bin/env python3
"""
Paper Digest - 小麦抗病·植物免疫论文日报
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import date, datetime
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel

from config import (
    JOURNAL_SOURCES,
    PLANT_KEYWORDS,
    LOOKBACK_DAYS,
    OUTPUT_DIR,
    LOG_DIR,
)
from fetchers import get_fetcher, PaperMetadata
from analyzer import PaperAnalyzer, PaperAnalysis
from html_generator import HtmlGenerator
from notifier import EmailNotifier, LocalNotifier

# ── Logging ──────────────────────────────────────────────────────────────────
LOG_FILE = LOG_DIR / f"paper_digest_{date.today().strftime('%Y%m%d')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RichHandler(rich_tracebacks=True, console=Console(width=120)),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger("paper_digest")
console = Console(width=120)


# ── 1. 检索论文 ───────────────────────────────────────────────────────────────

def fetch_all_papers(keywords: list[str], lookback_days: int) -> list[PaperMetadata]:
    all_papers: dict[str, PaperMetadata] = {}

    console.print(Panel.fit(
        f"[bold green]📚 开始检索论文[/bold green]\n"
        f"数据源: {len(JOURNAL_SOURCES)} 个\n"
        f"关键词: {len(keywords)} 个\n"
        f"回溯天数: {lookback_days} 天",
        border_style="green",
    ))

    for source_config in JOURNAL_SOURCES:
        source_name  = source_config["name"]
        fetcher_name = source_config["fetcher"]
        console.print(f"  🔍 检索 [bold]{source_name}[/bold]...", end=" ")
        try:
            fetcher = get_fetcher(
                fetcher_name,
                source_name=source_name,
                **{k: v for k, v in source_config.items() if k not in ("name", "fetcher")},
            )
            papers = fetcher.fetch(keywords, lookback_days)
        except Exception as e:
            logger.error("Fetcher '%s' failed: %s", source_name, e)
            console.print(f"[red]✗ 失败: {e}[/red]")
            continue

        new_count = 0
        for paper in papers:
            if paper.unique_id not in all_papers:
                all_papers[paper.unique_id] = paper
                new_count += 1
        console.print(f"[green]✓ 获取 {len(papers)} 篇 (新增 {new_count} 篇)[/green]")

    papers_list = list(all_papers.values())
    papers_list.sort(key=lambda p: p.published_date or date.min, reverse=True)

    console.print()
    table = Table(title="📊 检索结果汇总", border_style="green")
    table.add_column("指标", style="cyan")
    table.add_column("数值", style="green")
    table.add_row("总检索论文数 (去重后)", str(len(papers_list)))
    table.add_row("数据源数量", str(len(JOURNAL_SOURCES)))
    table.add_row("检索关键词数", str(len(keywords)))
    from collections import Counter
    for src, count in Counter(p.source for p in papers_list).most_common():
        table.add_row(f"  └ {src}", str(count))
    console.print(table)
    console.print()

    return papers_list


# ── 2. AI 分析 ────────────────────────────────────────────────────────────────

def analyze_papers(papers: list[PaperMetadata]) -> list[PaperAnalysis]:
    from config import DEEPSEEK_API_KEY

    if not DEEPSEEK_API_KEY:
        console.print(
            "[bold red]⚠ DEEPSEEK_API_KEY 未设置！[/bold red]\n"
            "请在 .env 文件中配置 DEEPSEEK_API_KEY。\n"
            "将跳过 AI 分析，仅生成论文元数据摘要。"
        )
        return []

    console.print(Panel.fit(
        f"[bold blue]🤖 开始 AI 分析 (DeepSeek)[/bold blue]\n"
        f"候选论文: {len(papers)} 篇\n"
        f"目标简报: 6 篇（相关性 ≥ 6/10）\n"
        f"模型: deepseek-chat",
        border_style="blue",
    ))

    try:
        analyzer = PaperAnalyzer(api_key=DEEPSEEK_API_KEY)
        analyses = analyzer.analyze_papers(
            papers,
            relevance_threshold=6,
            target_count=6,
            max_to_analyze=20,
        )
    except Exception as e:
        logger.error("Analysis failed: %s", e)
        console.print(f"[red]分析失败: {e}[/red]")
        return []

    successful = [a for a in analyses if a.is_valid()]
    failed     = [a for a in analyses if not a.is_valid()]

    console.print()
    console.print(f"  ✅ 成功分析: [green]{len(successful)}[/green] 篇")
    if failed:
        console.print(f"  ❌ 分析失败: [red]{len(failed)}[/red] 篇")

    return analyses


# ── 3. 生成文档 ───────────────────────────────────────────────────────────────

def generate_document(analyses: list[PaperAnalysis], fetch_date: date) -> Path:
    console.print()
    console.print("[bold]📝 生成 HTML 简报...[/bold]")
    gen      = HtmlGenerator()
    doc_path = gen.generate(analyses, fetch_date)
    console.print(f"  📄 文件已保存: [green bold]{doc_path}[/green bold]")
    console.print(f"  📏 文件大小: [green]{doc_path.stat().st_size / 1024:.1f} KB[/green]")
    console.print(f"  🌐 用浏览器打开即可查看")
    return doc_path


# ── 4. 发送通知 ───────────────────────────────────────────────────────────────

def send_notification(doc_path: Path, paper_count: int, digest_date: date) -> bool:
    notifier = EmailNotifier()
    if not notifier.is_configured:
        console.print(
            "[yellow]⚠ 邮件未配置，文档已保存到本地。[/yellow]\n"
            "  配置方法: 在 .env 文件中设置 EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT"
        )
        LocalNotifier().notify(doc_path, paper_count, digest_date)
        return False

    console.print()
    console.print("[bold]📧 发送邮件通知...[/bold]")
    success = notifier.send_digest(doc_path, paper_count, digest_date)
    if success:
        console.print(f"  ✅ 邮件已发送至: [green]{notifier.recipient}[/green]")
    else:
        console.print("[red]  ❌ 邮件发送失败[/red]")
        LocalNotifier().notify(doc_path, paper_count, digest_date)
    return success


# ── 主流程 ────────────────────────────────────────────────────────────────────

def run_once(fetch_date: date | None = None) -> Path | None:
    fetch_date = fetch_date or date.today()
    console.rule(f"[bold green]🌾 小麦抗病论文日报 - {fetch_date.strftime('%Y年%m月%d日')}[/bold green]")
    console.print()
    start_time = datetime.now()

    # Step 1
    papers = fetch_all_papers(PLANT_KEYWORDS, LOOKBACK_DAYS)
    if not papers:
        console.print("[yellow]未检索到相关论文。[/yellow]")
        return None

    # Step 2
    analyses = analyze_papers(papers)
    if not analyses:
        console.print(
            "\n[yellow]⚠ 今日未检索到小麦抗病/植物免疫相关论文，不生成简报。[/yellow]\n"
            "  提示：可修改 config.py 中的 RELEVANCE_THRESHOLD（当前6分）或 LOOKBACK_DAYS（当前3天）放宽筛选"
        )
        return None

    # Step 3
    doc_path = generate_document(analyses, fetch_date)

    # Step 4
    successful = [a for a in analyses if a.is_valid()]
    send_notification(doc_path, len(successful), fetch_date)

    elapsed = (datetime.now() - start_time).total_seconds()
    console.print()
    console.rule("[bold green]✅ 完成[/bold green]")
    console.print(
        f"⏱ 总耗时: [bold]{elapsed:.1f}[/bold] 秒\n"
        f"📄 输出文件: [bold green]{doc_path}[/bold green]\n"
        f"📋 日志文件: [bold]{LOG_FILE}[/bold]"
    )
    return doc_path


def run_daemon(schedule_time: str = "08:00"):
    try:
        import schedule
    except ImportError:
        console.print("[red]需要安装 schedule 库：pip install schedule[/red]")
        sys.exit(1)

    console.print(Panel.fit(
        f"[bold green]🌾 Paper Digest 守护进程[/bold green]\n\n"
        f"⏰ 每日执行时间: [bold]{schedule_time}[/bold]\n"
        f"📂 输出目录: {OUTPUT_DIR}\n"
        f"📋 日志目录: {LOG_DIR}\n\n"
        f"按 Ctrl+C 停止运行",
        border_style="green",
    ))

    schedule.every().day.at(schedule_time).do(lambda: run_once() or True)

    console.print("\n[yellow]是否立即执行一次？(y/n)[/yellow] ", end="")
    try:
        if input().strip().lower() == "y":
            console.print()
            run_once()
            console.print()
    except (EOFError, KeyboardInterrupt):
        pass

    console.print(f"[dim]等待下次执行时间: {schedule_time}...[/dim]")
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        console.print("\n[yellow]守护进程已停止。[/yellow]")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    global LOOKBACK_DAYS, OUTPUT_DIR
    parser = argparse.ArgumentParser(
        description="🌾 Paper Digest - 小麦抗病·植物免疫论文日报",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                        # 运行一次
  python main.py --schedule 08:00       # 每天早上 8:00 运行
  python main.py --daemon               # 后台守护进程（每天 8:00）
  python main.py --lookback 3           # 检索最近 3 天
        """,
    )
    parser.add_argument("--schedule", "-s", type=str, metavar="HH:MM")
    parser.add_argument("--daemon",   "-d", action="store_true")
    parser.add_argument("--lookback", "-l", type=int, default=LOOKBACK_DAYS)
    parser.add_argument("--output-dir", "-o", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--no-email", action="store_true")
    args = parser.parse_args()

    LOOKBACK_DAYS = args.lookback
    OUTPUT_DIR    = Path(args.output_dir)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.schedule:
        run_daemon(args.schedule)
    elif args.daemon:
        run_daemon("08:00")
    else:
        run_once()


if __name__ == "__main__":
    main()
