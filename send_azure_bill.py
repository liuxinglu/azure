import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
from azure.identity import DefaultAzureCredential
from azure.mgmt.consumption import ConsumptionManagementClient
from azure.mgmt.consumption.models import BillingPeriodName
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 初始化DefaultAzureCredential，用于身份验证
credential = DefaultAzureCredential()

# 创建ConsumptionManagementClient实例
subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
consumption_client = ConsumptionManagementClient(credential, subscription_id)

def get_latest_billing_period(consumption_client):
    # 获取最新的账单周期
    billing_periods = consumption_client.billing_periods.list()
    latest_billing_period = max(billing_periods, key=lambda x: x.billing_period_end_date) if billing_periods else None
    return latest_billing_period

def save_usage_details_to_csv(consumption_client, billing_period_name):
    # 获取指定账单周期内的使用详情
    usage_details = consumption_client.usage_details.list_by_billing_period(billing_period_name=billing_period_name)
    usage_list = list(usage_details)  # 将生成器转换为列表
    df = pd.DataFrame([vars(detail) for detail in usage_list])  # 将使用详情转换为DataFrame
    csv_file_path = 'azure_usage_details.csv'  # 定义CSV文件路径
    df.to_csv(csv_file_path, index=False)  # 保存DataFrame到CSV文件
    return csv_file_path

def send_email_with_attachment(csv_file_path):
    # 发送带有附件的电子邮件（实现与之前的代码相同）
    # ...（省略了发送邮件的代码，以保持简洁）
    pass  # 请在这里实现发送邮件的逻辑

def main():
    latest_billing_period = get_latest_billing_period(consumption_client)
    if latest_billing_period:
        billing_period_name = BillingPeriodName(latest_billing_period.name)  # 创建BillingPeriodName对象（如果需要的话，根据API要求）
        # 注意：有时API可能直接接受字符串作为账单周期名称，而不是BillingPeriodName对象
        # 如果API不接受BillingPeriodName对象，请直接传递字符串：billing_period_name = latest_billing_period.name
        csv_file_path = save_usage_details_to_csv(consumption_client, billing_period_name)
        # 发送邮件（请在这里调用send_email_with_attachment函数的实现）
        # send_email_with_attachment(csv_file_path)
        print("CSV file created successfully.")
        # 注意：为了安全起见，不要在main函数中直接发送邮件，特别是在生产环境中。
        # 应该在确认CSV文件创建成功后，手动或通过其他安全方式触发邮件发送。
    else:
        print("No latest billing period found.")

if __name__ == "__main__":
    main()