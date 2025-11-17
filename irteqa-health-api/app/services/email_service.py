"""
Email Service
Handles sending emails via SendGrid or SMTP
"""

import os
from typing import Optional, Dict, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# Email configuration
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@irteqa.com")
FROM_NAME = os.getenv("FROM_NAME", "Irteqa Health")


class EmailService:
    """Service for sending emails"""

    def __init__(self):
        self.use_sendgrid = bool(SENDGRID_API_KEY)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send an email

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email
            text_content: Plain text version (optional)
            from_email: Sender email (optional, uses default)
            from_name: Sender name (optional, uses default)

        Returns:
            True if email sent successfully, False otherwise
        """

        if self.use_sendgrid:
            return await self._send_via_sendgrid(
                to_email, subject, html_content, text_content, from_email, from_name
            )
        else:
            return await self._send_via_smtp(
                to_email, subject, html_content, text_content, from_email, from_name
            )

    async def _send_via_sendgrid(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        from_email: Optional[str],
        from_name: Optional[str]
    ) -> bool:
        """Send email via SendGrid API"""
        try:
            # For now, use SMTP fallback
            # TODO: Implement SendGrid API integration
            return await self._send_via_smtp(
                to_email, subject, html_content, text_content, from_email, from_name
            )
        except Exception as e:
            print(f"[EMAIL] SendGrid error: {e}")
            return False

    async def _send_via_smtp(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str],
        from_email: Optional[str],
        from_name: Optional[str]
    ) -> bool:
        """Send email via SMTP"""
        try:
            sender_email = from_email or FROM_EMAIL
            sender_name = from_name or FROM_NAME

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{sender_name} <{sender_email}>"
            msg['To'] = to_email

            # Add text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # For development: just log the email
            if not SMTP_USER or not SMTP_PASSWORD:
                print(f"\n[EMAIL] Would send email:")
                print(f"  To: {to_email}")
                print(f"  Subject: {subject}")
                print(f"  From: {sender_name} <{sender_email}>")
                print(f"  Content: {text_content or html_content[:100]}...")
                return True

            # Send via SMTP
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)

            print(f"[EMAIL] Sent to {to_email}: {subject}")
            return True

        except Exception as e:
            print(f"[EMAIL] SMTP error: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def send_welcome_email(self, to_email: str, patient_name: str, onboarding_link: str) -> bool:
        """Send welcome email to new patient"""

        subject = "Welcome to Irteqa Health - Let's Get Started"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3b82f6; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f9fafb; padding: 30px; }}
                .button {{ display: inline-block; background-color: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; color: #6b7280; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Irteqa Health</h1>
                </div>
                <div class="content">
                    <p>Hi {patient_name},</p>

                    <p>Thank you for reaching out to Irteqa Health. We're here to support you on your mental health journey.</p>

                    <p>To get started, we need to gather some information to match you with the right therapist and provide you with the best care possible.</p>

                    <p><strong>Next Steps:</strong></p>
                    <ol>
                        <li>Complete your intake form (10-15 minutes)</li>
                        <li>Review and sign the consent forms</li>
                        <li>Get matched with a therapist</li>
                        <li>Schedule your first session</li>
                    </ol>

                    <p style="text-align: center;">
                        <a href="{onboarding_link}" class="button">Start Your Onboarding</a>
                    </p>

                    <p>If you have any questions, feel free to reply to this email or call us at (555) 123-4567.</p>

                    <p>We look forward to working with you!</p>

                    <p>Warm regards,<br>
                    The Irteqa Health Team</p>
                </div>
                <div class="footer">
                    <p>Irteqa Health | Confidential Mental Health Services</p>
                    <p>This email contains confidential information. If you received this in error, please delete it.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to Irteqa Health

        Hi {patient_name},

        Thank you for reaching out to Irteqa Health. We're here to support you on your mental health journey.

        To get started, please complete your onboarding at: {onboarding_link}

        Next Steps:
        1. Complete your intake form (10-15 minutes)
        2. Review and sign the consent forms
        3. Get matched with a therapist
        4. Schedule your first session

        If you have any questions, feel free to reply to this email or call us at (555) 123-4567.

        We look forward to working with you!

        Warm regards,
        The Irteqa Health Team
        """

        return await self.send_email(to_email, subject, html_content, text_content)

    async def send_intake_reminder(self, to_email: str, patient_name: str, intake_link: str) -> bool:
        """Send reminder to complete intake form"""

        subject = "Reminder: Complete Your Irteqa Health Intake Form"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2>Hi {patient_name},</h2>

                <p>We noticed you haven't completed your intake form yet. This is an important step to help us provide you with the best care.</p>

                <p>It only takes 10-15 minutes and helps us:</p>
                <ul>
                    <li>Understand your mental health needs</li>
                    <li>Match you with the right therapist</li>
                    <li>Prepare for your first session</li>
                </ul>

                <p style="text-align: center; margin: 30px 0;">
                    <a href="{intake_link}" style="display: inline-block; background-color: #3b82f6; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px;">Complete Intake Form</a>
                </p>

                <p>If you have any questions or need assistance, please don't hesitate to reach out.</p>

                <p>Best regards,<br>The Irteqa Health Team</p>
            </div>
        </body>
        </html>
        """

        return await self.send_email(to_email, subject, html_content)


# Singleton instance
email_service = EmailService()
