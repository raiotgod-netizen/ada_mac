from __future__ import annotations

import mimetypes
import os
import re
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import Iterable

from dotenv import load_dotenv

load_dotenv()


class EmailAgent:
    def __init__(self):
        self.gmail_address = os.getenv("ADA_GMAIL_ADDRESS", "").strip()
        self.gmail_app_password = os.getenv("ADA_GMAIL_APP_PASSWORD", "").strip()
        self.display_name = os.getenv("ADA_GMAIL_DISPLAY_NAME", "ADA")
        self.smtp_host = os.getenv("ADA_GMAIL_SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("ADA_GMAIL_SMTP_PORT", "587"))

    def configured(self) -> bool:
        return bool(self.gmail_address and self.gmail_app_password)

    def snapshot(self) -> dict:
        return {
            "configured": self.configured(),
            "address": self.gmail_address or None,
            "display_name": self.display_name,
            "provider": "gmail",
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
        }

    def validate_configuration(self) -> dict:
        if not self.gmail_address:
            return {"ok": False, "result": "Falta ADA_GMAIL_ADDRESS en .env"}
        if not self.gmail_app_password:
            return {"ok": False, "result": "Falta ADA_GMAIL_APP_PASSWORD en .env"}
        if "@" not in self.gmail_address:
            return {"ok": False, "result": "ADA_GMAIL_ADDRESS no parece un correo válido."}
        return {"ok": True, "result": "Configuración de correo detectada."}

    def test_smtp_connection(self) -> dict:
        validation = self.validate_configuration()
        if not validation.get("ok"):
            return validation
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.gmail_address, self.gmail_app_password)
            return {"ok": True, "result": f"Conexión SMTP validada correctamente para {self.gmail_address}"}
        except smtplib.SMTPAuthenticationError:
            return {"ok": False, "result": "Autenticación SMTP falló. Revisa la app password de Gmail."}
        except Exception as e:
            return {"ok": False, "result": f"No se pudo validar SMTP: {e}"}

    def send_email(self, to: str | Iterable[str], subject: str, body: str, html: str | None = None, attachments: list[str] | None = None) -> dict:
        if not self.configured():
            return {
                "ok": False,
                "result": "Correo Gmail no configurado. Faltan ADA_GMAIL_ADDRESS y/o ADA_GMAIL_APP_PASSWORD en .env",
            }

        recipients = [to] if isinstance(to, str) else [item for item in (to or []) if item]
        expanded = []
        for item in recipients:
            if isinstance(item, str):
                expanded.extend([part.strip() for part in item.replace(';', ',').split(',') if part.strip()])
        recipients = [item for item in expanded if str(item).strip()]
        email_pattern = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
        invalid = [item for item in recipients if not email_pattern.match(item)]
        if invalid:
            return {"ok": False, "result": f"Destinatarios inválidos: {', '.join(invalid)}"}
        if not recipients:
            return {"ok": False, "result": "Debes indicar al menos un destinatario."}

        msg = EmailMessage()
        msg["Subject"] = (subject or "Mensaje de ADA").strip() or "Mensaje de ADA"
        msg["From"] = f"{self.display_name} <{self.gmail_address}>"
        msg["To"] = ", ".join(recipients)
        msg.set_content((body or "").strip() or "Mensaje enviado por ADA")
        if html:
            msg.add_alternative(html, subtype="html")

        attached_files = []
        for raw_path in attachments or []:
            path = Path(raw_path)
            if not path.exists() or not path.is_file():
                return {"ok": False, "result": f"No existe el adjunto: {path}"}
            mime_type, _ = mimetypes.guess_type(str(path))
            maintype, subtype = (mime_type or "application/octet-stream").split("/", 1)
            with open(path, "rb") as f:
                msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=path.name)
            attached_files.append(path.name)

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.gmail_address, self.gmail_app_password)
                server.send_message(msg)
            return {
                "ok": True,
                "result": f"Correo enviado correctamente a {', '.join(recipients)} desde {self.gmail_address}",
                "attachments": attached_files,
            }
        except smtplib.SMTPAuthenticationError:
            return {"ok": False, "result": "Autenticación SMTP falló. Revisa ADA_GMAIL_ADDRESS y ADA_GMAIL_APP_PASSWORD (app password)."}
        except smtplib.SMTPRecipientsRefused:
            return {"ok": False, "result": f"El servidor rechazó los destinatarios: {', '.join(recipients)}"}
        except smtplib.SMTPServerDisconnected:
            return {"ok": False, "result": "El servidor SMTP cerró la conexión inesperadamente."}
        except TimeoutError:
            return {"ok": False, "result": "Timeout conectando con el servidor SMTP."}
        except Exception as e:
            return {"ok": False, "result": f"Error enviando correo Gmail: {e}"}

    def _imap_connection(self):
        import imaplib
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
        mail.login(self.gmail_address, self.gmail_app_password)
        return mail

    def read_inbox(self, limit: int = 10, unread_only: bool = False) -> dict:
        """Read recent emails from inbox."""
        if not self.configured():
            return {"ok": False, "result": "Gmail no configurado."}
        try:
            import imaplib, email
            from email.header import decode_header
            mail = self._imap_connection()
            mail.select('INBOX' if not unread_only else 'INBOX')
            status, messages = mail.search(None, 'UNSEEN' if unread_only else 'ALL')
            ids = messages[0].split()
            total = len(ids)
            ids = ids[-limit:] if limit else ids
            emails = []
            for eid in reversed(ids):
                try:
                    status, msg_data = mail.fetch(eid, '(RFC822)')
                    raw = msg_data[0][1]
                    msg = email.message_from_bytes(raw)
                    subject_parts = decode_header(msg['Subject'] or 'Sin asunto')[0]
                    if isinstance(subject_parts[0], bytes):
                        subject = subject_parts[0].decode(subject_parts[1] or 'utf-8', errors='replace')
                    else:
                        subject = subject_parts[0] or 'Sin asunto'
                    sender = email.utils.parseaddr(msg.get('From', ''))
                    date = msg.get('Date', '')
                    body = ''
                    if msg.is_multipart():
                        for part in msg.walk():
                            ct = part.get_content_type()
                            if ct == 'text/plain' and not part.get('Content-Disposition'):
                                charset = part.get_content_charset() or 'utf-8'
                                body = part.get_payload(decode=True).decode(charset, errors='replace')[:500]
                                break
                    else:
                        charset = msg.get_content_charset() or 'utf-8'
                        body = (msg.get_payload(decode=True) or b'').decode(charset, errors='replace')[:500]
                    emails.append({
                        "from": sender[1] if len(sender) > 1 else sender[0],
                        "from_name": sender[0],
                        "subject": subject,
                        "date": date,
                        "snippet": body.replace('\r\n', ' ').strip(),
                        "id": eid.decode() if isinstance(eid, bytes) else str(eid)
                    })
                except Exception:
                    continue
            mail.logout()
            return {"ok": True, "emails": emails, "total_inbox": total, "returned": len(emails)}
        except Exception as e:
            return {"ok": False, "result": f"Error leyendo inbox: {e}"}

    def search_emails(self, query: str, limit: int = 10) -> dict:
        """Search emails by subject, sender, or content."""
        if not self.configured():
            return {"ok": False, "result": "Gmail no configurado."}
        try:
            import imaplib, email
            from email.header import decode_header
            mail = self._imap_connection()
            mail.select('INBOX')
            status, messages = mail.search(None, f'ALL (SUBJECT "{query}" OR FROM "{query}")')
            ids = messages[0].split()
            ids = ids[-limit:] if limit else ids
            emails = []
            for eid in reversed(ids):
                try:
                    status, msg_data = mail.fetch(eid, '(RFC822)')
                    raw = msg_data[0][1]
                    msg = email.message_from_bytes(raw)
                    subject_parts = decode_header(msg['Subject'] or 'Sin asunto')[0]
                    if isinstance(subject_parts[0], bytes):
                        subject = subject_parts[0].decode(subject_parts[1] or 'utf-8', errors='replace')
                    else:
                        subject = subject_parts[0] or 'Sin asunto'
                    sender = email.utils.parseaddr(msg.get('From', ''))
                    date = msg.get('Date', '')
                    emails.append({
                        "from": sender[1] if len(sender) > 1 else sender[0],
                        "from_name": sender[0],
                        "subject": subject,
                        "date": date,
                        "id": eid.decode() if isinstance(eid, bytes) else str(eid)
                    })
                except Exception:
                    continue
            mail.logout()
            return {"ok": True, "emails": emails, "query": query, "returned": len(emails)}
        except Exception as e:
            return {"ok": False, "result": f"Error buscando correos: {e}"}
