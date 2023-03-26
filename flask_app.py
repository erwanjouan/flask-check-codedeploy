from flask import Flask, render_template
from code_deploy import get_last_deployment_id, get_last_deployment_info, get_alb_dns_name, get_ec2_deployment_state
from ec2 import find_all_ec2

app = Flask(__name__)


@app.route('/')
def code_deployment():
    last_deployment_id = get_last_deployment_id()
    ec2_instances = find_all_ec2()
    deployment_info = get_last_deployment_info(last_deployment_id)
    ec2_deployment_states = get_ec2_deployment_state(last_deployment_id, ec2_instances)
    alb_dns_name = get_alb_dns_name()
    return render_template('index.html',
                           deployment_headers=deployment_info.keys(),
                           deployment_contents=deployment_info.values(),
                           ec2_deployment_states_headers=['id', 'ip', 'state'],
                           ec2_deployment_states_contents=ec2_deployment_states,
                           alb_dns_name=alb_dns_name
                           )
