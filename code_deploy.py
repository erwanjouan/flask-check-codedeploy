import boto3

client = boto3.client('elbv2')
ec2 = boto3.resource('ec2')
codedeploy = boto3.client('codedeploy')


def get_last_deployment_id():
    list_deployments = codedeploy.list_deployments()
    return list_deployments['deployments'][0]


def get_last_deployment_event(deployment_id, instance_id):
    try:
        get_deployment_instance = codedeploy.get_deployment_instance(deploymentId=deployment_id, instanceId=instance_id)
        lifecycle_events = get_deployment_instance['instanceSummary']['lifecycleEvents']
        lifecycle_events_size = len(lifecycle_events)
        last_event = lifecycle_events[lifecycle_events_size - 1]
        if last_event['status'] == 'Pending' and lifecycle_events_size > 1:
            last_event = lifecycle_events[lifecycle_events_size - 2]
        return last_event
    except:
        return {}


def get_alb_dns_name():
    alb_dns_name = "http://127.0.0.1"
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


def get_last_deployment_info(last_deployment_id):
    response = codedeploy.get_deployment(deploymentId=last_deployment_id)
    deployment_info = response['deploymentInfo']
    return {
        'deployment_config_name': deployment_info.get('deploymentConfigName'),
        'deployment_type': deployment_info.get('deploymentStyle').get('deploymentType'),
        'deployment_option': deployment_info.get('deploymentStyle').get('deploymentOption'),
        'deployment_createTime': deployment_info.get('createTime'),
        'deployment_id': last_deployment_id,
        'deployment_status': deployment_info.get('status')
    }


def get_ec2_deployment_state(last_deployment_id, ec2_instances):
    to_return = []
    for ec2_instance in ec2_instances:
        last_deployment_event = get_last_deployment_event(last_deployment_id, ec2_instance.id)
        to_return.append({
            'instance_id': ec2_instance.id,
            'private_ip_address': ec2_instance.private_ip_address,
            'state': ec2_instance.state,
            'last_deployment_event': last_deployment_event
        })
    return to_return


def generate_deployment_info_html(html, deployment_info):
    html = html + "<h2>Deployment Info</h2>\n"
    html = html + "<table>\n"
    html = html + "<tr>\n"
    html = html + "<th>Deployment Id</th>\n"
    html = html + "<th>Deployment config name</th>\n"
    html = html + "<th>Type</th>\n"
    html = html + "<th>Option</th>\n"
    html = html + "<th>Status</th>\n"
    html = html + "</tr>\n"
    html = html + "<tr>\n"
    html = html + "<td>" + deployment_info['deployment_id'] + "</td>\n"
    html = html + "<td>" + deployment_info['deployment_config_name'] + "</td>\n"
    html = html + "<td>" + deployment_info['deployment_type'] + "</td>\n"
    html = html + "<td>" + deployment_info['deployment_option'] + "</td>\n"
    html = html + "<td>" + deployment_info['deployment_status'] + "</td>\n"
    html = html + "</tr>\n"
    html = html + "</table>\n"
    return html


def generate_instance_info_html(html, ec2_instance_ids):
    html = html + "<h2>Instances</h2>\n"
    html = html + "<table>\n"
    html = html + "<tr>\n"
    html = html + "<th>instance</th>\n"
    html = html + "<th>private_ip_address</th>\n"
    html = html + "<th>state</th>\n"
    html = html + "<th>last_deployment_id</th>\n"
    html = html + "<th>event_name</th>\n"
    html = html + "<th>event_status</th>\n"
    html = html + "</tr>\n"
    for ec2_instance_id in ec2_instance_ids:
        html = html + "<tr>\n"
        html = html + "<td>" + ec2_instance_id['id'] + "</td>\n"
        html = html + "<td>" + ec2_instance_id['private_ip_address'] + "</td>\n"
        html = html + "<td>" + ec2_instance_id['state'] + "</td>\n"
        html = html + "<td>" + ec2_instance_id['last_deployment_id'] + "</td>\n"
        html = html + "<td>" + ec2_instance_id['event_name'] + "</td>\n"
        html = html + "<td>" + ec2_instance_id['event_status'] + "</td>\n"
    html = html + "</tr>\n"
    html = html + "</table>\n"
    return html


def generate_target_iframe(html, alb_url):
    html = html + '<br/>\n'
    html = html + '<iframe width="800" height="200" src="' + alb_url + '"></iframe>\n'
    return html


def generate_html(deployment_info, ec2_instance_ids, alb_url):
    html = '<html>\n'
    html = html + '<meta http-equiv="refresh" content="5">\n'
    html = html + '<body style="background-color:black;color:white">\n'
    html = generate_deployment_info_html(html, deployment_info)
    html = generate_instance_info_html(html, ec2_instance_ids)
    html = generate_target_iframe(html, alb_url)
    html = html + "</body>\n"
    html = html + "</html>\n"
    return html


def lambda_handler(event, context):
    last_deployment_id = get_last_deployment_id()
    ec2_on_alb_instance_ids = get_ec2_on_alb_instance_id(last_deployment_id)
    deployment_info = get_last_deployment_info(last_deployment_id)
    alb_dns_name = get_alb_dns_name()
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8"
        },
        "body": generate_html(deployment_info, ec2_on_alb_instance_ids, alb_dns_name)
    }
