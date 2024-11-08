import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.mgmt.consumption import ConsumptionManagementClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Azure 认证和客户端初始化
credential = DefaultAzureCredential()
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
consumption_client = ConsumptionManagementClient(credential, subscription_id)

def get_usage_details_for_last_month(consumption_client):
    # 获取上个月的起始和结束日期
    end_date = datetime.now().replace(day=1)  # 当前月的第一天
    start_date = (end_date - timedelta(days=1)).replace(day=1)  # 上个月的第一天

    # 获取上个月的使用详情
    try:
        usage_details = consumption_client.usage_details.list(
            scope=f"/subscriptions/{subscription_id}",
            expand="properties/additionalInfo",
            filter=f"properties/usageEnd ge '{start_date}' and properties/usageEnd lt '{end_date}'"
        )
        usage_list = list(usage_details)
        df = pd.DataFrame([vars(detail) for detail in usage_list])
        csv_file_path = 'azure_usage_details.csv'
        df.to_csv(csv_file_path, index=False)
        return csv_file_path
    except Exception as e:
        print(f"Failed to retrieve usage details: {e}")
        return None

def send_email_with_attachment(csv_file_path):
    # SMTP 配置信息
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = os.getenv("SENDER_EMAIL")
    receiver_email = os.getenv("RECEIVER_EMAIL")
    subject = "Azure Usage Details CSV"

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        # 邮件正文
        body = "Please find the attached Azure usage details."
        msg.attach(MIMEText(body, 'plain'))

        # 添加 CSV 文件附件
        with open(csv_file_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(csv_file_path)}')
            msg.attach(part)

        # 发送邮件
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def main():
    csv_file_path = get_usage_details_for_last_month(consumption_client)
    if csv_file_path:
        send_email_with_attachment(csv_file_path)
        print("CSV file created and email sent successfully.")
    else:
        print("Failed to create CSV file.")

if __name__ == "__main__":
    main()
