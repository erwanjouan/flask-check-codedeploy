import boto3

ec2 = boto3.resource('ec2')


def find_all_ec2():
    return ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'stopped']}])
