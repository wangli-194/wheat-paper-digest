"""
Notification Module

Sends the generated paper digest via email and/or saves to local directory.
Supports Gmail SMTP (with app password) and other email providers.
"""

from __future__ import annotations

import logging
import smtplib
import socket
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional

from config import (
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_RECIPIENT,
    SMTP_SERVER,
    SMTP_PORT,
)

logger = logging.getLogger(__name__)


class EmailNotifier:
    """Sends email notifications with the paper digest attached."""

    def __init__(
        self,
        sender: str = "",
        password: str = "",
        recipient: str = "",
        smtp_server: str = "",
        smtp_port: int = 0,
    ):
        self.sender = sender or EMAIL_SENDER
        self.password = password or EMAIL_PASSWORD
        self.recipient = recipient or EMAIL_RECIPIENT
        self.smtp_server = smtp_server or SMTP_SERVER
        self.smtp_port = smtp_port or SMTP_PORT

    @property
    def is_configured(self) -> bool:
        """Check if email settings are configured."""
        return bool(self.sender and self.password and self.recipient)

    def send_digest(
        self,
        doc_path: Path,
        paper_count: int,
        digest_date: Optional[date] = None,
    ) -> bool:
        """
        Send the paper digest document via email.

        Args:
            doc_path: Path to the .docx file
            paper_count: Number of papers in the digest
            digest_date: Date of the digest

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.warning(
                "Email not configured. Set EMAIL_SENDER, EMAIL_PASSWORD, "
                "and EMAIL_RECIPIENT in .env file."
            )
            return False

        if not doc_path.exists():
            logger.error("Document not found: %s", doc_path)
            return False

        digest_date = digest_date or date.today()
        date_str = digest_date.strftime("%Y年%m月%d日")

        # ── Build email ─────────────────────────────────────────────────
        msg = MIMEMultipart()
        msg["From"] = self.sender
        msg["To"] = self.recipient
        msg["Subject"] = f"🌱 植物学前沿论文日报 - {date_str} ({paper_count}篇)"

        # Plain text body
        body = self._build_body(paper_count, digest_date, doc_path)
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Attach document
        with open(doc_path, "rb") as f:
            attachment = MIMEBase("application", "octet-stream")
            attachment.set_payload(f.read())
            encoders.encode_base64(attachment)
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=doc_path.name,
            )
            msg.attach(attachment)

        # ── Send ────────────────────────────────────────────────────────
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.sender, self.password)
                server.sendmail(self.sender, self.recipient, msg.as_string())

            logger.info(
                "Email sent to %s: %s", self.recipient, msg["Subject"]
            )
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error(
                "SMTP authentication failed. If using Gmail, ensure you're "
                "using an App Password (not your regular password). "
                "Generate one at: https://myaccount.google.com/apppasswords"
            )
            return False
        except smtplib.SMTPException as e:
            logger.error("SMTP error: %s", e)
            return False
        except socket.error as e:
            logger.error("Network error sending email: %s", e)
            return False

    def _build_body(
        self,
        paper_count: int,
        digest_date: date,
        doc_path: Path,
    ) -> str:
        """Build the email body text."""
        date_str = digest_date.strftime("%Y年%m月%d日")
        hostname = socket.gethostname()

        return f"""植物学前沿论文日报
Plant Biology Research Daily Digest
{'=' * 50}

📅 日期: {date_str}
📄 论文数量: {paper_count} 篇
📎 附件: {doc_path.name}
🖥 生成主机: {hostname}

{'=' * 50}

今日植物学前沿论文摘要已生成，请查收附件中的 Word 文档。

文档包含以下内容的详细分析:
  • 📋 发表信息 - 期刊、日期、DOI
  • 🏛 研究单位 - 主要研究机构和实验室
  • 🔬 研究背景 - 研究问题和领域现状
  • 🧪 研究方法 - 关键实验技术和手段
  • 📊 实验结果 - 主要发现和数据
  • 💬 讨论 - 作者对结果的解读
  • ⭐ 创新点 - 研究的新颖性和突破
  • 🌱 植物学相关性 - 对植物科学的意义

数据来源: bioRxiv, PubMed, Nature Plants, Nature, Cell,
          The Plant Cell, New Phytologist 等

---
Paper Digest Bot | 自动化论文阅读工具
生成时间: {digest_date.strftime('%Y-%m-%d')}
"""


class LocalNotifier:
    """Fallback notifier that saves digest reports locally."""

    def __init__(self, output_dir: Optional[Path] = None):
        from config import OUTPUT_DIR
        self.output_dir = output_dir or OUTPUT_DIR

    def notify(
        self,
        doc_path: Path,
        paper_count: int,
        digest_date: Optional[date] = None,
    ) -> Path:
        """
        Save a summary text file alongside the document.

        Returns path to the summary file.
        """
        digest_date = digest_date or date.today()
        summary_path = self.output_dir / f"摘要_{digest_date.strftime('%Y%m%d')}.txt"

        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"植物学论文日报 - {digest_date.strftime('%Y年%m月%d日')}\n")
            f.write(f"{'=' * 50}\n\n")
            f.write(f"论文总数: {paper_count}\n")
            f.write(f"文档路径: {doc_path}\n")
            f.write(f"生成时间: {digest_date.isoformat()}\n")

        logger.info("Local summary saved: %s", summary_path)
        return summary_path
