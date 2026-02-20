import os
import base64
import mimetypes
import requests


class SendGridError(Exception):
    pass


def file_to_sendgrid_attachment(file_path: str, filename: str):
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "application/octet-stream"

    with open(file_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    return {
        "content": content_b64,
        "filename": filename,
        "type": mime_type,
        "disposition": "attachment",
    }


def send_email(
    to_email: str,
    subject: str,
    text: str,
    html: str | None = None,
    reply_to: str | None = None,
    attachments: list[dict] | None = None,
):
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        raise SendGridError("SENDGRID_API_KEY não definida")

    from_email = os.getenv("DEFAULT_FROM_EMAIL", "emirbraz.d2@gmail.com")

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/plain", "value": text}],
    }

    if reply_to:
        payload["reply_to"] = {"email": reply_to}

    if html:
        payload["content"].append({"type": "text/html", "value": html})

    if attachments:
        payload["attachments"] = attachments

    r = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    if r.status_code != 202:
        raise SendGridError(f"SendGrid falhou ({r.status_code}): {r.text}")
