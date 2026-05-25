from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path


@dataclass(slots=True)
class EmailSettings:
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    email_from: str
    use_ssl: bool
    use_starttls: bool


def parse_dotenv_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    content: str | None = None
    for encoding in ("utf-8", "utf-8-sig", "gbk", "cp936", "utf-16"):
        try:
            content = env_path.read_text(encoding=encoding)
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        raise SystemExit(f"Unable to read .env file: {env_path}")

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


def load_settings() -> EmailSettings:
    script_dir = Path(__file__).resolve().parent
    env_values: dict[str, str] = {}

    for candidate in (script_dir / ".env", script_dir.parent / ".env"):
        env_values.update(parse_dotenv_file(candidate))

    def read(name: str, default: str | None = None) -> str:
        return os.getenv(name) or env_values.get(name) or (default or "")

    missing: list[str] = []
    required_names = ("SMTP_USER", "SMTP_PASS", "EMAIL_FROM")
    for name in required_names:
        if not read(name):
            missing.append(name)

    if missing:
        raise SystemExit(
            "Missing required config: "
            + ", ".join(missing)
            + ". Create backend/.env or set environment variables first."
        )

    return EmailSettings(
        smtp_host=read("SMTP_HOST", "smtp.qq.com"),
        smtp_port=int(read("SMTP_PORT", "465")),
        smtp_user=read("SMTP_USER"),
        smtp_pass=read("SMTP_PASS"),
        email_from=read("EMAIL_FROM"),
        use_ssl=read("SMTP_USE_SSL", "true").lower() == "true",
        use_starttls=read("SMTP_USE_STARTTLS", "false").lower() == "true",
    )


def send_email(
    *,
    settings: EmailSettings,
    to_email: str,
    subject: str,
    body: str,
) -> None:
    message = EmailMessage()
    message["From"] = settings.email_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    if settings.use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
            smtp.login(settings.smtp_user, settings.smtp_pass)
            smtp.send_message(message)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as smtp:
        smtp.ehlo()
        if settings.use_starttls:
            smtp.starttls()
            smtp.ehlo()
        smtp.login(settings.smtp_user, settings.smtp_pass)
        smtp.send_message(message)


def main() -> None:
    settings = load_settings()

    to_email = os.getenv("TEST_TO_EMAIL", "1773040108@qq.com")
    subject = os.getenv("TEST_SUBJECT", "【穗安】-预警提示")
    body = os.getenv("TEST_BODY", "预警！")

    try:
        send_email(
            settings=settings,
            to_email=to_email,
            subject=subject,
            body=body,
        )
    except smtplib.SMTPAuthenticationError as exc:
        message = exc.smtp_error.decode(errors="ignore")
        raise SystemExit(f"SMTP authentication failed: {message}") from exc

    print(f"Test email sent successfully to {to_email}.")


if __name__ == "__main__":
    main()
