import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.mgmt.consumption import ConsumptionManagementClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化DefaultAzureCredential，用于身份验证
credential = DefaultAzureCredential()

# 创建ConsumptionManagementClient实例
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')  # 从环境变量获取Azure订阅ID
consumption_client = ConsumptionManagementClient(credential, subscription_id)

def get_latest_billing_period(consumption_client):
    billing_periods = consumption_client.bills.list()  # 注意：这里使用了bills.list()而不是charges.list()，因为bills通常包含更完整的账单信息
    latest_billing_period = max(billing_periods, key=lambda x: x.billing_period_end_date) if billing_periods else None
    return latest_billing_period

def save_billing_info_to_csv(consumption_client, billing_period_name):
    usage_details = consumption_client.usage_details.list_by_billing_period(billing_period_name)
    df = pd.DataFrame([vars(detail) for detail in usage_details])  # 将usage_details转换为DataFrame
    csv_file_path = 'azure_billing_info.csv'  # 定义CSV文件路径
    df.to_csv(csv_file_path, index=False)  # 保存DataFrame到CSV文件
    return csv_file_path

def send_email_with_attachment(csv_file_path):
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    email_from = smtp_user
    email_to = os.getenv('EMAIL_TO')

    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = 'Azure Billing Information'

    body = 'Please find the attached Azure billing information.'
    msg.attach(MIMEText(body, 'plain'))

    with open(csv_file_path, 'rb') as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename= {os.path.basename(csv_file_path)}')
    msg.attach(part)

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # 启用TLS加密
            server.login(smtp_user, smtp_password)  # 登录SMTP服务器
            server.sendmail(email_from, email_to, msg.as_string())  # 发送邮件
        print("Email with attachment sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")
    finally:
        os.remove(csv_file_path)  # 清理文件

def main():
    latest_billing_period = get_latest_billing_period(consumption_client)
    if latest_billing_period:
        csv_file_path = save_billing_info_to_csv(consumption_client, latest_billing_period.name)
        send_email_with_attachment(csv_file_path)
    else:
        print("No latest billing period found, no email sent.")

if __name__ == "__main__":
    main()