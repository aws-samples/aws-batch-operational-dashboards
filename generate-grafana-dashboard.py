#!/usr/bin/env python3

import argparse
import boto3
import jinja2


def get_batch_container_insights():
    client = boto3.client('logs')
    response = client.describe_log_groups(
        logGroupNamePrefix='/aws/ecs/containerinsights/AWSBatch')
    logs = []
    for i in response['logGroups']:
        logs.append(i['logGroupName'])
    return logs


def write_file(data):
    f = open('batch-grafana-dashboard.json', 'w')
    f.write(data)
    f.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--table', type=str, required=True)
    arg = parser.parse_args()

    logs = get_batch_container_insights()

    f = open('batch-grafana-dashboard-template.json')
    data = f.read()
    f.close()
    template = jinja2.Template(data)
    out = template.render(TABLE=arg.table.lower(), LOG_GROUP=logs)

    write_file(out)


if __name__ == '__main__':
    main()
