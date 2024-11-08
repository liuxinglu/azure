import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.mgmt.consumption import ConsumptionManagementClient

# 初始化DefaultAzureCredential，用于身份验证
credential = DefaultAzureCredential()

# 创建ConsumptionManagementClient实例
subscription_id = '你的订阅ID'  # 替换为你的Azure订阅ID
consumption_client = ConsumptionManagementClient(credential, subscription_id)

# 获取最新的账单周期
billing_periods = consumption_client.charges.list()
latest_billing_period = max(billing_periods, key=lambda x:x.end_date)

# 配置邮件发送
smtp_server = 'smtp.example.com'  # 替换为你的SMTP服务器地址
smtp_port = 587  # 替换为你的SMTP服务器端口
smtp_user = 'your-email@example.com'  # 替换为你的邮箱地址
smtp_password = 'your-email-password'  # 替换为你的邮箱密码（注意安全性）
email_from = smtp_user
email_to = 'group-email@example.com'  # 替换为你要发送到的群组邮箱地址

# 保存账单信息到CSV文件（或其他格式）
if latest_billing_period:
    usage_details = consumption_client.usage_details.list_by_billing_period(latest_billing_period.name)
    df = pd.DataFrame([vars(detail) for detail in usage_details])  # 将usage_details转换为DataFrame
    csv_file_path = 'azure_billing_info.csv'  # 定义CSV文件路径
    df.to_csv(csv_file_path, index=False)  # 保存DataFrame到CSV文件

    # 创建邮件并添加附件
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = 'Azure Billing Information'

    # 添加邮件正文（可选）
    body = 'Please find the attached Azure billing information.'
    msg.attach(MIMEText(body, 'plain'))

    # 添加附件
    with open(csv_file_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(csv_file_path)}')
    msg.attach(part)

    try:
        # 发送邮件
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # 启用TLS加密
        server.login(smtp_user, smtp_password)  # 登录SMTP服务器
        server.sendmail(email_from, email_to, msg.as_string())  # 发送邮件
        server.quit()  # 关闭连接
        print("Email with attachment sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        # 清理文件（可选）
        os.remove(csv_file_path)
else:
    print("No latest billing period found, no email sent.")

# 注意：在生产环境中，请确保妥善保管敏感信息，并考虑使用更安全的方法来处理它们，
# 例如使用环境变量、密钥管理服务或加密配置文件。