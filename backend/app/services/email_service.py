import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from app.config import settings

def send_guardian_alert_email(
    guardian_email: str,
    user_name: str,
    risk_level: str,
    fraud_type: str,
    user_input: str,
    details: str,
    advice: str
) -> bool:
    """
    向监护人发送风险预警邮件（使用 SSL 加密端口 465）
    """
    # 1. 配置邮件服务器 (QQ邮箱 SSL)
    smtp_host = "smtp.qq.com"
    smtp_port = 465   # SSL 端口

    # 2. 发件人信息（从配置中读取）
    sender_email = settings.QQ_EMAIL
    sender_password = settings.QQ_AUTHORIZATION_CODE

    # 检查配置是否为空
    if not sender_email or not sender_password:
        print("邮件配置缺失：请检查 QQ_EMAIL 和 QQ_AUTHORIZATION_CODE 环境变量")
        return False

    # 3. 邮件内容
    subject = f"【反诈预警】您的家人 {user_name} 正面临高危风险！"
    
    # 构建邮件的HTML正文
    html_content = f"""
    <html>
    <body>
        <h2>🚨 高风险预警通知</h2>
        <p>您关注的用户 <b>{user_name}</b> 刚刚与以下高风险内容发生了交互：</p>
        <pre style="background-color:#f4f4f4; padding:10px;">{user_input}</pre>
        <hr>
        <p><b>📊 分析结果：</b></p>
        <ul>
            <li><b>风险等级：</b>{risk_level}</li>
            <li><b>诈骗类型：</b>{fraud_type}</li>
            <li><b>详细分析：</b>{details}</li>
            <li><b>处置建议：</b>{advice}</li>
        </ul>
        <hr>
        <p>请立即联系用户进行核实，谨防诈骗！</p>
        <p>此邮件由「多模态反诈智能助手」系统自动发送。</p>
    </body>
    </html>
    """
    
    # 4. 创建邮件对象
    msg = MIMEMultipart()
    # 关键修改：From 只保留邮箱地址，不加显示名称，避免格式错误
    msg['From'] = sender_email
    msg['To'] = guardian_email
    msg['Subject'] = Header(subject, 'utf-8')
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    # 5. 发送邮件（使用 SSL）
    try:
        # 直接使用 SMTP_SSL 连接 465 端口
        server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [guardian_email], msg.as_string())
        server.quit()
        print(f"预警邮件已成功发送至 {guardian_email}")
        return True
    except Exception as e:
        print(f"邮件发送失败: {e}")
        return False