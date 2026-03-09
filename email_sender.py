"""
email_sender.py — Gmail SMTP integration for sending application status emails.
Uses Python's built-in smtplib (no extra dependencies needed).
"""

import smtplib
import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def _status_badge(status: str) -> str:
    """Return an HTML badge for the application status."""
    colors = {
        "Submitted": ("#FF9800", "#FFF"),
        "Interview": ("#2196F3", "#FFF"),
        "Selected": ("#4CAF50", "#FFF"),
        "Not Selected": ("#F44336", "#FFF"),
    }
    bg, fg = colors.get(status, ("#999", "#FFF"))
    return (
        f"<span style='background:{bg};color:{fg};padding:4px 14px;"
        f"border-radius:14px;font-size:13px;font-weight:600;'>{status}</span>"
    )


def build_email_html(applications: list) -> str:
    """Build the HTML email body matching the user's requested format."""

    today = datetime.date.today().strftime("%Y-%m-%d")

    # Table rows
    rows_html = ""
    for app in applications:
        status = app.get("status", "Submitted")
        submitted = app.get("submitted_at", "")[:10]
        rows_html += f"""
        <tr style="border-bottom:1px solid #E0E0E0;">
            <td style="padding:14px 16px;color:#1A1A1A;font-weight:600;font-size:14px;">
                {app.get('company_name', 'Unknown')}
            </td>
            <td style="padding:14px 16px;color:#333;font-size:14px;">
                {app.get('role', 'Unknown')}
            </td>
            <td style="padding:14px 16px;text-align:center;">
                {_status_badge(status)}
            </td>
            <td style="padding:14px 16px;color:#555;font-size:14px;text-align:center;">
                {submitted}
            </td>
            <td style="padding:14px 16px;color:#555;font-size:14px;text-align:center;">
                {today}
            </td>
        </tr>"""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0;padding:0;background:#F5F5F5;font-family:Arial,Helvetica,sans-serif;">
        <div style="max-width:700px;margin:20px auto;background:#FFFFFF;border-radius:12px;
                    overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">

            <!-- Header -->
            <div style="background:linear-gradient(135deg,#1A1A2E 0%,#16213E 50%,#0F3460 100%);
                        padding:30px 32px;">
                <div style="display:flex;align-items:center;">
                    <span style="font-size:28px;margin-right:12px;">💼</span>
                    <div>
                        <h1 style="color:#FFFFFF;margin:0;font-size:22px;font-weight:700;">
                            Application Status Update
                        </h1>
                        <p style="color:#4ECCA3;margin:4px 0 0 0;font-size:14px;">
                            AI Job Application Assistant
                        </p>
                    </div>
                </div>
            </div>

            <!-- Table -->
            <div style="padding:0 0 8px 0;">
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="background:#F8F8FA;border-bottom:2px solid #E0E0E0;">
                            <th style="padding:14px 16px;text-align:left;color:#666;
                                       font-size:12px;font-weight:600;text-transform:uppercase;
                                       letter-spacing:0.5px;">Company</th>
                            <th style="padding:14px 16px;text-align:left;color:#666;
                                       font-size:12px;font-weight:600;text-transform:uppercase;
                                       letter-spacing:0.5px;">Role</th>
                            <th style="padding:14px 16px;text-align:center;color:#666;
                                       font-size:12px;font-weight:600;text-transform:uppercase;
                                       letter-spacing:0.5px;">Status</th>
                            <th style="padding:14px 16px;text-align:center;color:#666;
                                       font-size:12px;font-weight:600;text-transform:uppercase;
                                       letter-spacing:0.5px;">Applied</th>
                            <th style="padding:14px 16px;text-align:center;color:#666;
                                       font-size:12px;font-weight:600;text-transform:uppercase;
                                       letter-spacing:0.5px;">Updated</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>

            <!-- Footer -->
            <div style="text-align:center;padding:20px;border-top:1px solid #EEEEEE;">
                <p style="color:#999;font-size:12px;margin:0;">
                    Sent from AI Job Application Assistant
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def send_status_email(
    sender_email: str,
    app_password: str,
    recipient_email: str,
    applications: list,
) -> str:
    """Send application status email via Gmail SMTP.

    Returns:
        Empty string on success, error message on failure.
    """
    if not applications:
        return "No applications to send."

    html_body = build_email_html(applications)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Application Status Update — AI Job Application Assistant"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, app_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        return ""
    except smtplib.SMTPAuthenticationError:
        return "Authentication failed. Check your Gmail address and App Password."
    except smtplib.SMTPException as e:
        return f"SMTP error: {e}"
    except Exception as e:
        return f"Failed to send email: {e}"
