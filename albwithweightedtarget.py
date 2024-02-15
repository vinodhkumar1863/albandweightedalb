import boto3

# Create a new session using boto3
ec2_client = boto3.client('ec2')
elbv2_client = boto3.client('elbv2')

# Create an Application Load Balancer
response = elbv2_client.create_load_balancer(
    Name='my-load-balancer',
    Subnets=[
        'subnet-abcdef12',
        'subnet-abcdef13'
    ],
    SecurityGroups=[
        'sg-12345678'
    ],
    Type='application',
    Scheme='internet-facing'
)
load_balancer_arn = response['LoadBalancers'][0]['LoadBalancerArn']

# Create target groups
target_group_1_response = elbv2_client.create_target_group(
    Name='target_group_1',
    Protocol='HTTP',
    Port=80,
    VpcId='vpc-ab123cde'
)
target_group_1_arn = target_group_1_response['TargetGroups'][0]['TargetGroupArn']

target_group_2_response = elbv2_client.create_target_group(
    Name='target_group_2',
    Protocol='HTTP',
    Port=80,
    VpcId='vpc-ab123cde'
)
target_group_2_arn = target_group_2_response['TargetGroups'][0]['TargetGroupArn']

# Register targets with the target groups
instances = ['i-001', 'i-002', 'i-003', 'i-004', 'i-005', 'i-006']

for i in range(3):
    instance_id = instances[i]
    elbv2_client.register_targets(
        TargetGroupArn=target_group_1_arn,
        Targets=[
            {
                'Id': instance_id
            }
        ]
    )

for i in range(3, 6):
    instance_id = instances[i]
    elbv2_client.register_targets(
        TargetGroupArn=target_group_2_arn,
        Targets=[
            {
                'Id': instance_id
            }
        ]
    )

# Create a security group for ALB to listen to only port 80, HTTP
alb_security_group_id = ec2_client.create_security_group(
    GroupName='alb-security-group',
    Description='Security group for ALB to listen to only port 80',
    VpcId='your-vpc-id'
)['GroupId']

ec2_client.authorize_security_group_ingress(
    GroupId=alb_security_group_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 80,
            'ToPort': 80,
            'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  # Replace with your specific IP range
        }
    ]
)

# Create a security group for instances to listen to only ALB
instance_security_group_id = ec2_client.create_security_group(
    GroupName='instance-security-group',
    Description='Security group for instances to listen to only ALB',
    VpcId='your-vpc-id'
)['GroupId']

ec2_client.authorize_security_group_ingress(
    GroupId=instance_security_group_id,
    IpPermissions=[
        {
            'IpProtocol': 'tcp',
            'FromPort': 80,
            'ToPort': 80,
            'UserIdGroupPairs': [{'GroupId': alb_security_group_id}]
        }
    ]
)

# Create a weighted target group
elbv2_client.create_listener(
    LoadBalancerArn=load_balancer_arn,
    Protocol='HTTP',
    Port=80,
    DefaultActions=[
        {
            'Type': 'forward',
            'TargetGroupArn': target_group_1_arn,
            'Weight': 8
        },
        {
            'Type': 'forward',
            'TargetGroupArn': target_group_2_arn,
            'Weight': 2
        }
    ]
)
