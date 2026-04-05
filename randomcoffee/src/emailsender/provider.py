from typing import List, Union, Dict, Any
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from envconfig import Config


config = Config.instance()
class EmailSender:
    """
    Asynchronous email sender with SMTP support.
    
    This class provides methods for sending emails asynchronously.
    """
    
    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        is_html: bool = False
    ) -> bool:
        """
        Send a single email asynchronously.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject line
            body: Email body content (plain text or HTML)
            is_html: Whether the body contains HTML markup. Defaults to False
        
        Returns:
            True if success else False
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
            
            auth_credential = config.email_token or config.email_pwd
            await smtp.login(config.email, auth_credential)
            
            await smtp.send_message(msg, recipients=to_emails)
            
            await smtp.quit()
            
            return True
            
        except Exception as e:
            return False


async def send_email(
    to_emails: Union[str, List[str]],
    subject: str,
    body: str,
    is_html: bool = False
) -> bool:
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
        True if success else False
    """
    sender = EmailSender()
    
    if isinstance(to_emails, str):
        to_emails = [to_emails]
    
    return await sender.send_email(to_emails, subject, body, is_html)