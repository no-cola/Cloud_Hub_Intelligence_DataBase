#!/usr/bin/env python3

import smtplib
import sys
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate
import socket

def send_email(recipient, subject, body, attachment_path=None):
    # 配置邮件服务器（使用SSL端口）
    smtp_server = "smtp.qq.com"
    smtp_port = 465  # 改为更稳定的SSL端口
    sender_email = "3022872158@qq.com"
    password = "yfzaiwqjajrbdhbd"  # 确保是QQ邮箱生成的授权码

    # 创建邮件
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(body))

    # 添加附件
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as file:
            part = MIMEApplication(file.read(), Name=os.path.basename(attachment_path))
        part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
        msg.attach(part)
    
    # 发送邮件（使用SMTP_SSL替代原始连接）
    try:
        # 检查DNS解析是否正常
        try:
            socket.getaddrinfo(smtp_server, smtp_port)
        except socket.gaierror as e:
            print(f"DNS解析失败: {e}")
            return False

        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: send_email.py <接收者邮箱> <主题> <内容> [附件路径]")
        sys.exit(1)
    
    recipient = sys.argv[1]
    subject = sys.argv[2]
    body = sys.argv[3]
    attachment_path = sys.argv[4] if len(sys.argv) > 4 else None
    
    if send_email(recipient, subject, body, attachment_path):
        print("邮件发送成功")
        sys.exit(0)
    else:
        print("邮件发送失败")
        sys.exit(1)
