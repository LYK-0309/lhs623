"""邮件发送工具 — QQ 邮箱 SMTP 验证码发送（真实发送，无 fallback）"""
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from flask import current_app


class MailNotConfiguredError(Exception):
    """邮箱未配置异常"""
    pass


def send_qq_email(to_addr, subject, body):
    """
    发送 QQ 邮箱验证码（必须配置 SMTP）
    
    Args:
        to_addr:  收件人 QQ 邮箱地址
        subject:  邮件主题
        body:     邮件正文
        
    Returns:
        (success: bool, message: str)
        
    Raises:
        MailNotConfiguredError: 未配置邮箱凭据
    """
    cfg = current_app.config
    username = cfg.get('MAIL_USERNAME', '')
    password = cfg.get('MAIL_PASSWORD', '')

    if not username or not password:
        raise MailNotConfiguredError(
            '系统邮件服务未配置。'
            '请在 .env 文件中设置 MAIL_USERNAME 和 MAIL_PASSWORD，'
            '参考 .env.example 获取说明。'
        )

    try:
        msg = MIMEText(body, 'plain', 'utf-8')

        # 使用 formataddr 生成符合 RFC 5322 的 From 头（解决 QQ SMTP 550 错误）
        # QQ SMTP 要求 From 头必须是合法的邮箱地址格式
        msg['From'] = formataddr(('影评分享系统', username))
        msg['To'] = to_addr
        msg['Subject'] = Header(subject, 'utf-8')

        if cfg.get('MAIL_USE_SSL'):
            server = smtplib.SMTP_SSL(
                cfg['MAIL_SERVER'], cfg['MAIL_PORT'], timeout=15,
                context=None  # 使用默认 SSL 上下文
            )
        else:
            server = smtplib.SMTP(cfg['MAIL_SERVER'], cfg['MAIL_PORT'], timeout=15)
            if cfg.get('MAIL_USE_TLS'):
                server.starttls()

        # 设置 debug 级别便于排查
        server.set_debuglevel(0)

        server.login(username, password)
        server.sendmail(username, [to_addr], msg.as_string())
        server.quit()
        return True, '验证码已发送到您的 QQ 邮箱，请查收'

    except MailNotConfiguredError:
        raise
    except smtplib.SMTPAuthenticationError as e:
        current_app.logger.error(f'[Email] SMTP认证失败: {e}')
        return False, f'邮箱认证失败，请检查 SMTP 授权码是否正确 ({e})'
    except smtplib.SMTPConnectError as e:
        current_app.logger.error(f'[Email] SMTP连接失败: {e}')
        return False, f'无法连接邮件服务器，请检查网络 ({e})'
    except smtplib.SMTPRecipientsRefused as e:
        current_app.logger.error(f'[Email] 收件人被拒: {e}')
        return False, f'收件人地址被拒绝 ({e})'
    except smtplib.SMTPSenderRefused as e:
        current_app.logger.error(f'[Email] 发件人被拒: {e}')
        return False, f'发件人地址被拒绝，请检查 MAIL_USERNAME 是否正确 ({e})'
    except smtplib.SMTPDataError as e:
        current_app.logger.error(f'[Email] 邮件数据错误: {e}')
        return False, f'邮件数据格式错误 ({e})'
    except smtplib.SMTPException as e:
        current_app.logger.error(f'[Email] SMTP异常: {type(e).__name__}: {e}')
        return False, f'邮件发送失败：{str(e)}'
    except ConnectionError as e:
        current_app.logger.error(f'[Email] 网络连接失败: {e}')
        return False, '网络连接失败，请检查网络'
    except Exception as e:
        current_app.logger.error(f'[Email] 发送异常: {type(e).__name__}: {e}')
        return False, f'邮件发送异常：{type(e).__name__}: {str(e)}'


def send_verification_email(email, code):
    """发送注册/登录验证码邮件"""
    subject = '【影评分享系统】您的验证码'
    body = (
        f'{code} 是您本次操作的验证码。\n'
        f'有效期为 5 分钟，请勿泄露给他人。\n\n'
        f'如非本人操作，请忽略此邮件。\n\n'
        f'—— 影评分享系统'
    )
    return send_qq_email(email, subject, body)
