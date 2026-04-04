import asyncio
import os
from typing import List, Optional, Union, Dict, Any
import aiosmtplib
import email.mime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from envconfig import config
import re


class EmailSender:
    """
    Asynchronous email sender with SMTP support.
    
    This class handles email configuration validation and provides methods
    for sending emails asynchronously.
    """

    PROVIDERS = {
        "gmail.com": "smtp.gmail.com",
        "yandex.ru": "smtp.yandex.ru",
        "yandex.com": "smtp.yandex.com",
        "mail.ru": "smtp.mail.ru",
        "list.ru": "smtp.mail.ru",
        "bk.ru": "smtp.mail.ru",
        "inbox.ru": "smtp.mail.ru",
        "rambler.ru": "smtp.rambler.ru",
        "outlook.com": "smtp-mail.outlook.com",
        "hotmail.com": "smtp-mail.outlook.com",
        "live.com": "smtp-mail.outlook.com",
        "yahoo.com": "smtp.mail.yahoo.com",
        "yahoo.ru": "smtp.mail.yahoo.com",
        "mailgun.org": "smtp.mailgun.org",
        "sendgrid.net": "smtp.sendgrid.net",
        "zoho.com": "smtp.zoho.com",
        "zoho.eu": "smtp.zoho.eu",
        "protonmail.com": "smtp.protonmail.com",
        "protonmail.ch": "smtp.protonmail.ch",
        "icloud.com": "smtp.mail.me.com",
        "me.com": "smtp.mail.me.com",
        "aol.com": "smtp.aol.com",
        "gmx.com": "mail.gmx.com",
        "gmx.net": "mail.gmx.net",
        "163.com": "smtp.163.com",
        "qq.com": "smtp.qq.com",
        "foxmail.com": "smtp.qq.com",
        "seznam.cz": "smtp.seznam.cz",
        "email.cz": "smtp.email.cz",
        "post.cz": "smtp.post.cz",
        "o2.pl": "poczta.o2.pl",
        "wp.pl": "smtp.wp.pl",
        "interia.pl": "smtp.poczta.interia.pl"
    }

    def __init__(self):
        """
        Initialize the email sender and validate configuration.
        
        Raises:
            ValueError: Required email configuration is missing
        """
        self._validate_config()
        
    def _validate_config(self) -> None:
        """
        Validate that all required email configuration is present.
        
        Checks for:
            - Email address is set
            - Either password or token is set for authentication
            - SMTP server URL and port are configured
        
        Raises:
            ValueError: If any required configuration is missing
        """
        if config.email is None:
            raise ValueError(
                "EMAIL is not set. Please configure EMAIL and either EMAIL_PWD or EMAIL_TOKEN"
            )
        
        if not re.fullmatch(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}", config.email):
            raise ValueError(
                "Invalid EMAIL. Please check the correctness."
            )
        
        if config.email_pwd is None and config.email_token is None:
            raise ValueError(
                "Either EMAIL_PWD or EMAIL_TOKEN must be set for authentication"
            )
        
        if config.email_smtp_url is None:
            if config.email.split('@') in self.PROVIDERS.keys:
                config.email_smtp_url = self.PROVIDERS[config.email.split('@')]
                config.email_smtp_port = 465
            else:
                raise ValueError("EMAIL_SMTP_URL is not configured")
        
        if config.email_smtp_port is None:
            raise ValueError("EMAIL_SMTP_PORT is not configured")
    
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        is_html: bool = False
    ) -> Dict[str, Any]:
        """
        Send a single email asynchronously.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            body: Email body content (plain text or HTML)
            is_html: Whether the body contains HTML markup. Defaults to False
        
        Returns:
            Dict containing:
                - success (bool): Whether sending was successful
                - message (str): Status or error message
        """
        try:
            msg = MIMEMultipart()
            sender_name = "Random Coffee Service"
            msg["From"] = formataddr((sender_name, config.email))
            msg["To"] = ", ".join(to_emails)
            msg["Subject"] = subject
            
            content_type = "html" if is_html else "plain"
            msg.attach(MIMEText(body, content_type, "utf-8"))
            
            smtp_port = int(config.email_smtp_port)
            use_tls = smtp_port == 465
            smtp = aiosmtplib.SMTP(
                hostname=config.email_smtp_url,
                port=smtp_port,
                use_tls=use_tls
            )

            await smtp.connect()
            
            auth_credential = config.email_pwd or config.email_token
            await smtp.login(config.email, auth_credential)
            
            result = await smtp.send_message(msg, recipients=to_emails)
            
            await smtp.quit()
            
            return {
                "success": True,
                "message": f"Email successfully sent to {len(to_emails)} recipient(s)"
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}"
            }


async def send_email(
    to_emails: Union[str, List[str]],
    subject: str,
    body: str,
    is_html: bool = False
) -> Dict[str, Any]:
    """
    Function to send an email.
    
    This is a convenience wrapper around EmailSender for quick email sending
    without needing to instantiate the class.
    
    Args:
        to_emails: Single email address string or list of addresses
        subject: Email subject line
        body: Email body content
        is_html: Whether the body contains HTML markup. Defaults to False
    
    Returns:
        Result dictionary with success status and message
    """
    sender = EmailSender()
    
    if isinstance(to_emails, str):
        to_emails = [to_emails]
    
    return await sender.send_email(to_emails, subject, body, is_html)