import ast
import json
import boto3
from botocore.exceptions import ClientError
import json
import base64
from datetime import date
from dateutil.relativedelta import relativedelta
from linebot import LineBotApi
from linebot.models import TextSendMessage


ce = boto3.client('ce')

def lambda_handler(event, context):
    body = json.loads(event['body'])
    if len(body['events']) == 0:
        return {
            'statusCode': 200,
            'body': ''
        }

    user_text = body['events'][0]['message']['text']
    reply_token = body['events'][0]['replyToken']

    if not user_text == '料金':
        return {
            'statusCode': 200,
            'body': ''
        }

    res = get_secret()
    channel_access_token = ast.literal_eval(res)
    line_bot_api = LineBotApi(channel_access_token['LINE_CHANNEL_ACCESS_TOKEN'])

    today = date.today() #今日
    tomorrow = today + relativedelta(days=1) #明日
    thismonth_first = today + relativedelta(day=1) #今月1日
    nextmonth_first = today + relativedelta(day=1, months=1) #来月最初

    cost_end = str(today)
    forecast_start = str(tomorrow)
    forecast_end = str(nextmonth_first)

    cost_start = str(thismonth_first)
    message_cost = get_cost(cost_start,cost_end)
    message_forecast = get_forecast(forecast_start,forecast_end)
    message = ('今月の現在までの利用金額は $'+message_cost+' で今月の利用予測金額は $'+message_forecast+' です')

    message_obj = TextSendMessage(text=message)
    line_bot_api.reply_message(reply_token, message_obj)


    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "send a message!",
        }),
    }

def get_cost(cost_start,cost_end):
    cost = ce.get_cost_and_usage(
        TimePeriod={
            'Start': cost_start,
            'End': cost_end
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost',],
    )
    format_cost = round(float(cost['ResultsByTime'][0]['Total']['UnblendedCost']['Amount']),2)
    return str(format_cost)

def get_forecast(forecast_start,forecast_end):
    forecast = ce.get_cost_forecast(
        TimePeriod={
            'Start': forecast_start,
            'End': forecast_end
        },
        Granularity='MONTHLY',
        Metric='UNBLENDED_COST',
    )
    format_forecast = round(float(forecast['Total']['Amount']),2)
    return str(format_forecast)

def get_secret():
    secret_name = "arn:aws:secretsmanager:ap-northeast-1:141864838114:secret:LINE_CHANNEL_ACCESS_TOKEN-d0kHNM"
    secretsmanager = boto3.client('secretsmanager')
    try:
        get_secret_value_response = secretsmanager.get_secret_value(SecretId=secret_name)
    except ClientError as e:
        raise e
    else:
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            secret = base64.b64decode(get_secret_value_response['SecretBinary'])
    return secret