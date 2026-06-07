import mimetypes
import os

from django.core.mail import EmailMessage


class SendGridError(Exception):
    pass


def file_to_sendgrid_attachment(file_path: str, filename: str):
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "application/octet-stream"
    with open(file_path, "rb") as f:
        content = f.read()
    return (filename, content, mime_type)


def send_email(
    to_email: str,
    subject: str,
    text: str,
    html: str | None = None,
    reply_to: str | None = None,
    attachments: list | None = None,
):
    from_email = os.getenv("DEFAULT_FROM_EMAIL")

    msg = EmailMessage(
        subject=subject,
        body=text,
        from_email=from_email,
        to=[to_email],
        reply_to=[reply_to] if reply_to else [],
    )

    if html:
        msg.content_subtype = "html"
        msg.body = html

    if attachments:
        for filename, content, mime_type in attachments:
            msg.attach(filename, content, mime_type)

    try:
        msg.send()
    except Exception as e:
        raise SendGridError(f"Email falhou: {e}")
