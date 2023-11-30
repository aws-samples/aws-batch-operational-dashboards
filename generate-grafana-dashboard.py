#!/usr/bin/env python3

import argparse
import boto3
import jinja2
import json


def get_batch_container_insights(log_group_name):
    client = boto3.client('logs')
    response = client.describe_log_groups(logGroupNamePrefix=log_group_name)
    for i in response['logGroups']:
        return json.dumps({'name': i['logGroupName'], 'arn': i['arn']})

    return None


def batch_container_insights_logs(ce_ids):
    logs = []
    for i in ce_ids:
        log = get_batch_container_insights('/aws/ecs/containerinsights/' + i)
        if log is not None:
            logs.append(log)
        else:
            print(f'**WARNING**: Did not find log group for {i}')
    return logs


def get_batch_ce():
    client = boto3.client('batch')
    response = client.describe_compute_environments()
    ce_list = []

    for i in response['computeEnvironments']:
        if i['containerOrchestrationType'] != 'EKS':
            ce_list.append(i)

    return ce_list


def container_insights_status(cluster_arn):
    client = boto3.client('ecs')
    response = client.describe_clusters(clusters=[cluster_arn],
                                        include=[
                                            'SETTINGS',
                                        ])
    for i in response['clusters'][0]['settings']:
        if i['name'] == 'containerInsights':
            ci_state = i['value']

    return ci_state


def write_file(data):
    f = open('batch-grafana-dashboard.json', 'w')
    f.write(data)
    f.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--table', type=str, required=True)
    arg = parser.parse_args()

    print('Checking container insights status to get AWS Batch job metric\n')
    ce_list = get_batch_ce()
    ce_ci_enabled = []
    for i in ce_list:
        ci_state = container_insights_status(i['ecsClusterArn'])
        if ci_state == 'enabled':
            ce_ci_enabled.append(i['ecsClusterArn'].split('/')[1])
        else:
            print(
                f'**WARNING**: You will not get AWS Batch job metric for **{i["computeEnvironmentName"]}** Compute environment since Container Insights is **{ci_state}**'
            )

    logs = batch_container_insights_logs(ce_ci_enabled)

    f = open('batch-grafana-dashboard-template.json')
    data = f.read()
    f.close()
    template = jinja2.Template(data)
    out = template.render(TABLE=arg.table.lower(), LOG_GROUP=logs)

    write_file(out)


if __name__ == '__main__':
    main()
