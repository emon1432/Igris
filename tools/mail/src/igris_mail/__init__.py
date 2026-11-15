"""Mail tool package exports."""

from igris_mail.models import EmailMessage, EmailSummary, EmailDraft
from igris_mail.parser import UntrustedEmailParser
from igris_mail.mail_tool import MailTool, MailToolError

__all__ = [
    "EmailMessage",
    "EmailSummary",
    "EmailDraft",
    "UntrustedEmailParser",
    "MailTool",
    "MailToolError",
]

