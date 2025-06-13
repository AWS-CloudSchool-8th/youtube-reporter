import boto3

def get_bedrock_client():
    return boto3.client("bedrock-runtime", region_name="ap-northeast-2")