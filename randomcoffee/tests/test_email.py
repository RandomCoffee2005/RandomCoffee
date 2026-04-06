from emailsender import send_email, EmailSender
from pytest_mock import MockerFixture
from unittest.mock import AsyncMock
import pytest 


def patch(mocker: MockerFixture,
        email: str = "test@example.com",
        email_pwd: str | None = "example_pwd",
        email_token: str | None = "example_token",
        smtp_url: str | None = "smtp.example.com",
        smtp_port: str | None = "465",
        smtp_should_fail: bool = False
    ):
    env_vars = {
        "EMAIL": email,
        "EMAIL_PWD": email_pwd,
        "EMAIL_TOKEN": email_token,
        "EMAIL_SMTP_URL": smtp_url,
        "EMAIL_SMTP_PORT": smtp_port
    }
    mocker.patch("os.getenv", env_vars.get)
    
    mock_smtp_instance = AsyncMock()
    
    if smtp_should_fail:
        mock_smtp_instance.connect.side_effect = Exception("SMTP failed")

    mock_smtp_class = mocker.patch('aiosmtplib.SMTP')
    mock_smtp_class.return_value = mock_smtp_instance

    return {
        'smtp_class': mock_smtp_class,
        'smtp_instance': mock_smtp_instance
    }
    
@pytest.mark.asyncio
async def test_send_email_sends_successfully(mocker: MockerFixture):
    mocks = patch(mocker)
    
    sender = EmailSender()
    result = await sender.send_email(
        to_emails=["user@example.com"],
        subject="Test",
        body="Hello"
    )
    
    assert result is True
    mocks['smtp_instance'].send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_returns_false_on_error(mocker: MockerFixture):
    mocks = patch(mocker, smtp_should_fail=True)
    
    sender = EmailSender()
    result = await sender.send_email(
        to_emails=["user@example.com"],
        subject="Test",
        body="Hello"
    )
    
    assert result is False


@pytest.mark.asyncio
async def test_send_email_function_wrapper(mocker: MockerFixture):
    mocks = patch(mocker)
    
    result = await send_email(
        to_emails=["user@example.com"],
        subject="Test",
        body="Hello"
    )
    
    assert result is True
    mocks['smtp_instance'].send_message.assert_called_once()