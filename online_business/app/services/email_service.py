"""
Email notifications. In production wire up a real SMTP/SendGrid/Resend client.
"""
import smtplib
from email.mime.text import MIMEText
from app.config import settings


def _send(to: str, subject: str, body: str) -> None:
    if not settings.smtp_user:
        # Email not configured — log and skip silently in dev
        print(f"[EMAIL SKIPPED] To: {to} | Subject: {subject}")
        return
    msg = MIMEText(body, "html")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user
    msg["To"] = to
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_user, to, msg.as_string())


def send_welcome(email: str, username: str) -> None:
    _send(
        to=email,
        subject="Welcome to DigitalMarket!",
        body=f"<h1>Hi {username}!</h1><p>Welcome to DigitalMarket — your digital products marketplace.</p>",
    )


def send_order_confirmation(buyer_email: str, product_title: str, download_token: str) -> None:
    _send(
        to=buyer_email,
        subject=f"Your purchase: {product_title}",
        body=(
            f"<h2>Thanks for your purchase!</h2>"
            f"<p>Product: <strong>{product_title}</strong></p>"
            f"<p>Use your download token to access your file: <code>{download_token}</code></p>"
        ),
    )


def send_sale_notification(seller_email: str, product_title: str, earnings: float) -> None:
    _send(
        to=seller_email,
        subject=f"You made a sale! +${earnings:.2f}",
        body=(
            f"<h2>Congratulations — you made a sale!</h2>"
            f"<p>Product: <strong>{product_title}</strong></p>"
            f"<p>Your earnings: <strong>${earnings:.2f}</strong> have been added to your wallet.</p>"
        ),
    )
