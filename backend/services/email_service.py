"""Email service using Resend for transactional emails."""
import asyncio
import logging
import resend

from config import settings

logger = logging.getLogger(__name__)

resend.api_key = settings.RESEND_API_KEY


async def send_password_reset_email(to_email: str, reset_token: str, app_url: str = "") -> dict:
    """Send a password reset email with a token link."""
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set — skipping email send")
        return {"status": "skipped", "reason": "Email service not configured"}

    reset_link = f"{app_url}?reset_token={reset_token}" if app_url else f"Reset token: {reset_token}"

    html_content = f"""
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 480px; margin: 0 auto; padding: 40px 20px;">
      <div style="text-align: center; margin-bottom: 32px;">
        <h1 style="font-size: 24px; font-weight: 800; color: #111827; margin: 0;">WTFHappened</h1>
        <p style="font-size: 13px; color: #9CA3AF; margin-top: 4px;">Trending topics explained</p>
      </div>
      <div style="background: #F9FAFB; border-radius: 16px; padding: 32px 24px; text-align: center;">
        <h2 style="font-size: 18px; font-weight: 700; color: #111827; margin: 0 0 8px;">Reset your password</h2>
        <p style="font-size: 14px; color: #6B7280; margin: 0 0 24px; line-height: 1.5;">
          We received a request to reset your password. Use the code below to set a new one. This code expires in 1 hour.
        </p>
        <div style="background: #111827; border-radius: 12px; padding: 16px 24px; display: inline-block; margin-bottom: 24px;">
          <span style="font-family: monospace; font-size: 18px; font-weight: 700; color: #FFFFFF; letter-spacing: 1px;">{reset_token}</span>
        </div>
        <p style="font-size: 12px; color: #9CA3AF; margin: 0;">
          If you didn't request this, you can safely ignore this email.
        </p>
      </div>
      <p style="font-size: 11px; color: #D1D5DB; text-align: center; margin-top: 24px;">
        WTFHappened &mdash; Understand what's happening in 30 seconds
      </p>
    </div>
    """

    params = {
        "from": settings.SENDER_EMAIL,
        "to": [to_email],
        "subject": "Reset your WTFHappened password",
        "html": html_content,
    }

    try:
        result = await asyncio.to_thread(resend.Emails.send, params)
        logger.info(f"Password reset email sent to {to_email}, id={result.get('id')}")
        return {"status": "sent", "email_id": result.get("id")}
    except Exception as e:
        logger.error(f"Failed to send reset email to {to_email}: {e}")
        return {"status": "failed", "error": str(e)}
