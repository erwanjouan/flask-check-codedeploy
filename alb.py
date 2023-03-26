import boto3

client = boto3.client('elbv2')
ec2 = boto3.resource('ec2')
codedeploy = boto3.client('codedeploy')


def get_alb_dns_name():
    alb_dns_name = "http://127.0.0.1:5000"
    response = client.describe_load_balancers()
    if len(response['LoadBalancers']) > 0:
        alb_dns_name = "http://" + response['LoadBalancers'][0]['DNSName'] + "/api"
    return alb_dns_name


def get_ec2_on_alb_instance_id(last_deployment_id):
    ec2_instance_ids = []
    response = client.describe_load_balancers()
    loadBalancerArn = (response['LoadBalancers'][0]['LoadBalancerArn'])
    response = client.describe_target_groups(LoadBalancerArn=loadBalancerArn)
    for targetGroup in response['TargetGroups']:
        targetGroupArn = targetGroup['TargetGroupArn']
        response = client.describe_target_health(TargetGroupArn=targetGroupArn)
        targetHealthDescriptions = response['TargetHealthDescriptions']
        for targetHealthDescription in targetHealthDescriptions:
            instance_id = targetHealthDescription['Target']['Id']
            state = targetHealthDescription['TargetHealth']['State']
            last_deployment_event = get_last_deployment_event(last_deployment_id, instance_id)
            current_instance = list(ec2.instances.filter(InstanceIds=[instance_id]))
            private_ip_address = current_instance[0].private_ip_address
            ec2_instance_ids.append({
                'id': instance_id,
                'state': state,
                'event_name': last_deployment_event['lifecycleEventName'],
                'event_status': last_deployment_event['status'],
                'last_deployment_id': last_deployment_id,
                'private_ip_address': private_ip_address
            })
    return ec2_instance_ids

