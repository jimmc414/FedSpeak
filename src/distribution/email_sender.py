"""Email alert distribution via SMTP.

This module sends alert notifications via email using SMTP. Supports both
production SMTP servers and local debugging servers.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Optional
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ..config.settings import get_settings
from ..exceptions import DataError

logger = logging.getLogger(__name__)


class EmailSender:
    """Send alert notifications via email.

    Supports:
    - Production SMTP servers (with TLS)
    - Local SMTP debugging servers (localhost:1025)
    - HTML email templates with Jinja2

    Attributes:
        smtp_server: SMTP server hostname
        smtp_port: SMTP server port
        smtp_from: From email address
        smtp_tls: Whether to use TLS
        recipients: List of recipient email addresses
        enabled: Whether email sending is enabled
    """

    def __init__(self):
        """Initialize email sender from config."""
        settings = get_settings()

        self.enabled = settings.get('distribution.email.enabled', default=False)
        self.smtp_server = settings.get('distribution.email.smtp_server', default='localhost')
        self.smtp_port = settings.get('distribution.email.smtp_port', default=1025)
        self.smtp_from = settings.get('distribution.email.smtp_from', default='fedspeak@localhost')
        self.smtp_tls = settings.get('distribution.email.smtp_tls', default=False)
        self.recipients = settings.get('distribution.email.recipients', default=[])

        # Setup Jinja2 for email templates
        # Use project root relative path (src/distribution/../../templates)
        template_dir = Path(__file__).parent.parent.parent / 'templates'
        template_dir.mkdir(exist_ok=True)

        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

        logger.info(
            f"EmailSender initialized: enabled={self.enabled}, "
            f"server={self.smtp_server}:{self.smtp_port}, recipients={len(self.recipients)}"
        )

    def send_alert(self, alert: Dict, recipients: Optional[List[str]] = None) -> bool:
        """Send alert via email.

        Args:
            alert: Alert dictionary with alert details
            recipients: Optional recipient list (uses config default if not provided)

        Returns:
            True if email sent successfully, False otherwise

        Raises:
            DataError: If email sending fails
        """
        if not self.enabled:
            logger.info(f"Email disabled, skipping send for alert {alert.get('alert_id')}")
            return False

        recipient_list = recipients or self.recipients

        if not recipient_list:
            logger.warning("No recipients configured, skipping email send")
            return False

        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"FedSpeak Alert: {alert['shift_type'].upper()} - {alert['term']}"
            msg['From'] = self.smtp_from
            msg['To'] = ', '.join(recipient_list)

            # Generate HTML body from template
            html_body = self._render_alert_html(alert)

            # Generate plain text fallback
            text_body = self._render_alert_text(alert)

            # Attach both parts
            part1 = MIMEText(text_body, 'plain')
            part2 = MIMEText(html_body, 'html')

            msg.attach(part1)
            msg.attach(part2)

            # Send email
            logger.info(f"Sending alert email to {len(recipient_list)} recipients")

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.smtp_tls:
                    server.starttls()

                server.send_message(msg)

            logger.info(f"Alert email sent successfully: {alert.get('alert_id')}")
            return True

        except Exception as e:
            error_msg = f"Failed to send alert email: {e}"
            logger.error(error_msg)
            raise DataError(error_msg) from e

    def _render_alert_html(self, alert: Dict) -> str:
        """Render alert as HTML using Jinja2 template.

        Args:
            alert: Alert dictionary

        Returns:
            HTML string
        """
        try:
            template = self.jinja_env.get_template('email_alert.html')
            return template.render(alert=alert)
        except Exception as e:
            logger.warning(f"Failed to render HTML template: {e}, using fallback")
            return self._render_alert_html_fallback(alert)

    def _render_alert_html_fallback(self, alert: Dict) -> str:
        """Fallback HTML rendering if template not found.

        Args:
            alert: Alert dictionary

        Returns:
            HTML string
        """
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background-color: #1f3b73; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .alert-box {{ border-left: 4px solid #d32f2f; padding: 10px; margin: 10px 0; background-color: #ffebee; }}
                .detail {{ margin: 10px 0; }}
                .label {{ font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>FedSpeak Language Shift Alert</h1>
            </div>
            <div class="content">
                <div class="alert-box">
                    <h2>{alert['shift_type'].upper()}: "{alert['term']}"</h2>
                </div>

                <div class="detail">
                    <span class="label">Date:</span> {alert['document']['date']}
                </div>

                <div class="detail">
                    <span class="label">Confidence:</span> {alert['confidence'].upper()}
                </div>

                <div class="detail">
                    <span class="label">Change:</span> {alert['change']['change_description']}
                </div>

                <div class="detail">
                    <span class="label">Alert ID:</span> {alert['alert_id']}
                </div>

                <div class="detail">
                    <span class="label">Timestamp:</span> {alert['timestamp']}
                </div>
            </div>
        </body>
        </html>
        """
        return html

    def _render_alert_text(self, alert: Dict) -> str:
        """Render alert as plain text.

        Args:
            alert: Alert dictionary

        Returns:
            Plain text string
        """
        text = f"""
FedSpeak Language Shift Alert
{'='*70}

SHIFT TYPE: {alert['shift_type'].upper()}
TERM: "{alert['term']}"

Document Date: {alert['document']['date']}
Confidence: {alert['confidence'].upper()}
Change: {alert['change']['change_description']}

Alert ID: {alert['alert_id']}
Timestamp: {alert['timestamp']}

{'='*70}

This alert was automatically generated by the FedSpeak monitoring system.
"""
        return text
