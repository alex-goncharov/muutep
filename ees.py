#!/bin/env python

import optparse
import yaml
import boto3
import boto3.session
import sys
from pprint import pprint



cfg_file = './ees.config.yaml'
defaults = {
        'aws_access_key_id': None,
        'aws_secret_access_key': None,
        'tag': {
            'Key': 'ES_cluster',
            'Value': '',
            },
        'region_name': 'eu-central-1',
        'vpc_cidr_block': '10.0.0.0/24',
        'subnets': {
            'dmz': {
                'cidr': '10.0.0.0/26',
                'id': None,
                'zone': 'eu-central-1a',
                },
            'priv': {
                'cidr': '10.0.0.64/26',
                'id': None,
                'zone': 'eu-central-1a',
                },
            },
        'internet_gateway': None,
        'allow_ssh_from': '80.100.141.205/32',
        }

instance_defaults = {
        'ImageId': 'ami-dafdcfc7',
        'MinCount': 1,
        'MaxCount': 1,
        'KeyName': 'es_cluster',
        'InstanceType': 't2.micro',
        'Placement': {
            'AvailabilityZone': 'eu-central-1a',
            'Tenancy': 'default',
            },
        }

def get_conf(cfile, defaults):

    ret = defaults.copy()

    f = open(cfile, 'r')
    cfg = yaml.load(f)
    f.close
    ret.update(cfg)

    return ret


def get_ec2(config):

    s = boto3.session.Session(aws_access_key_id = config['aws_access_key_id'],
                              aws_secret_access_key = config['aws_secret_access_key'],
                              region_name = config['region_name'])
    r = s.resource('ec2')

    try:
        r.vpcs.all()
    except BotoCoreError as e:
        print "Could not get vpcs list from ec2 resource, possible login failure"
        print e
        return None
    return r

def get_vpc(ec2, config, resources):

    if 'vpc' in resources:
        vpc = ec2.Vpc(resources['vpc'][0])
        print('VPC exists: %s' % vpc.id)
    else:
        vpc = ec2.create_vpc(
                DryRun = False,
                CidrBlock = config['vpc_cidr_block'],
                InstanceTenancy = 'default'
                )
        add_std_tags(vpc, config['tag'], 'ES VPC')
        for sg in vpc.security_groups.all():
            sg.authorize_ingress(IpProtocol = 'TCP', FromPort = 22, ToPort=22, CidrIp = config['allow_ssh_from'])
            sg.authorize_ingress(IpProtocol = 'TCP', FromPort = 80, ToPort=80, CidrIp = '0.0.0.0/0')
            sg.authorize_ingress(IpProtocol = 'TCP', FromPort = 443, ToPort=443, CidrIp = '0.0.0.0/0')
        print('Created new VPC: %s' % vpc.id)

    return vpc

def get_gw(ec2, vpc, config, resources):

    if 'internet-gateway' in resources:
        gw = ec2.InternetGateway(resources['internet-gateway'][0])
        print('IGW exists: %s' % gw.id)
    else:
        gw = ec2.create_internet_gateway()
        add_std_tags(gw, config['tag'], 'ES IGW')
        gw.attach_to_vpc(VpcId = vpc.id)
        print('Created new IGW: %s' % gw.id)

    return gw

def get_subnets(vpc, config):
    # should have 2 subnets, one tagged with net_access = dmz
    # another net_access = priv

    dmz = None
    priv = None
    for s in vpc.subnets.all():
        s_tag = None
        a_tag = None
        for t in s.tags:
            if t['Key'] == config['tag']['Key']:
                s_tag = True
            if t['Key'] == 'net_access':
                a_tag = t['Value']
        if s_tag is not None and a_tag == 'dmz':
            dmz = s
            print('DMZ exists: %s' % dmz.id)
        if s_tag is not None and a_tag == 'priv':
            priv = s
            print('PRIV exists: %s' % priv.id)

    if dmz is None:
        dmz = vpc.create_subnet(
                DryRun = False,
                CidrBlock = config['subnets']['dmz']['cidr'],
                AvailabilityZone = config['subnets']['dmz']['zone']
                )
        add_std_tags(dmz, config['tag'], 'ES DMZ', {'Key': 'net_access', 'Value': 'dmz'})
        print('Created new DMZ: %s' % dmz.id)
    if priv is None:
        priv = vpc.create_subnet(
                DryRun = False,
                CidrBlock = config['subnets']['priv']['cidr'],
                AvailabilityZone = config['subnets']['priv']['zone']
                )
        add_std_tags(priv, config['tag'], 'ES PRIV', {'Key': 'net_access', 'Value': 'priv'})
        print('Created new PRIV: %s' % priv.id)

    return (dmz, priv)

def get_enic(ec2, subnet, config, resources):
    if 'network-interface' in resources:
        nic = ec2.NetworkInterface(resources['network-interface'][0])
        print('ENIC exists: %s' % nic.id)
    else:

        client = boto3.client('ec2')

        nic = ec2.create_network_interface(
                SubnetId = subnet.id,
                Description = 'EC external nic'
                )
        add_std_tags(nic, config['tag'], 'ES ENIC')
        eip = client.allocate_address(Domain = 'vpc')
        eip = ec2.VpcAddress(eip['AllocationId'])
        eip.associate(NetworkInterfaceId = nic.id)

        print('Created new ENIC: %s' % nic.id)
    return nic

def get_inet_rt(ec2, vpc, gw, subnet, config, resources):
    if 'route-table' in resources:
        rt = ec2.RouteTable(resources['route-table'][0])
        print('IRT exists %s' % rt.id)
    else:
        rt = ec2.create_route_table(DryRun = False, VpcId = vpc.id)
        rt.create_route(
                DryRun = False,
                DestinationCidrBlock = '0.0.0.0/0',
                GatewayId = gw.id)
        add_std_tags(rt, config['tag'], 'ES IRT')
        rt.associate_with_subnet(SubnetId = subnet.id)
        print('Created new IRT: %s' % rt.id)
    return rt

def get_reverse_proxy(ec2, vpc, priv, enic, config):

    global instance_defaults

    f = [
            {'Name': 'vpc-id', 'Values': [vpc.id]},
            {'Name': 'tag-key', 'Values': [config['tag']['Key']]},
            {'Name': 'tag-key', 'Values': ['role']},
            {'Name': 'tag-value', 'Values': ['reverse-proxy'] },
        ]

    rp = None
    for i in ec2.instances.filter(Filters = f):
        pprint(i)
        return i


    rpi = instance_defaults.copy()
    #rpi['SubnetId'] = priv.id
    rpi['NetworkInterfaces'] = [{'NetworkInterfaceId': enic.id, 'DeviceIndex': 0}]
    rp = ec2.create_instances( **rpi )
    for i in rp:
        add_std_tags(i, config['tag'], 'ES RP', {'Key': 'role', 'Value': 'reverse-proxy'})
    return rp

def get_sg(ec2, vpc, config):

    pass



def add_std_tags(res, tag, name_tag, tags = None):
    _tags = [ tag, {'Key': 'Name', 'Value': name_tag} ]
    if tags is not None:
        _tags.append(tags)
    res.create_tags( Tags = _tags)


def get_tagged(client, tag):
    f = [
            {
                'Name': 'key',
                'Values': [tag['Key']]
            },
            {
                'Name': 'value',
                'Values': [tag['Value']]
            },
        ]
    response = client.describe_tags(Filters = f)
    resources = {}
    for r in response['Tags']:
        if r['ResourceType'] in resources:
            resources[r['ResourceType']].append(r['ResourceId'])
        else:
            resources[r['ResourceType']] = [r['ResourceId']]
    return resources


def mk_net(ec2, config, resources):

    vpc = get_vpc(ec2, config, resources)
    sg = get_sg(ec2, vpc, config)
    gw = get_gw(ec2, vpc, config, resources)
    (dmz,priv) = get_subnets(vpc, config)
    enic = get_enic(ec2, dmz, config, resources)
    rt = get_inet_rt(ec2, vpc, gw, dmz, config, resources)
    rp = get_reverse_proxy(ec2, vpc, priv, enic, config)

def destroy(client, ec2, resources):

    pprint(resources)

    if 'instance' in resources:
        client.terminate_instances(InstanceIds = resources['instance'])
        for i in resources['instance']:
            print('Waiting for %s to go down' % i)
            inst = ec2.Instance(i)
            inst.wait_until_terminated()
    if 'network-interface' in resources:
        for i in resources['network-interface']:
            nic = ec2.NetworkInterface(i)
            if nic.association is not None:
                nic.association.delete()
                nic.association.address.release()
            client.delete_network_interface(NetworkInterfaceId = i)
    if 'route-table' in resources:
        for i in resources['route-table']:
            r = ec2.RouteTable(i)
            for j in r.associations.all():
                j.delete()
            client.delete_route_table(RouteTableId = i)
    if 'internet-gateway' in resources:
        for i in resources['internet-gateway']:
            gw = ec2.InternetGateway(i)
            for j in gw.attachments:
                gw.detach_from_vpc(VpcId = j['VpcId'])
            client.delete_internet_gateway(InternetGatewayId = i)
    if 'subnet' in resources:
        for i in resources['subnet']:
            client.delete_subnet(SubnetId = i)
    if 'vpc' in resources:
        for i in resources['vpc']:
            client.delete_vpc(VpcId = i)



if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('-c', '--config', dest = 'config',
        help = "configuration file", default = cfg_file)
    parser.add_option('-f', '--force', dest = 'force',
        help = "do things anyway", default = False, action = 'store_true')
    parser.add_option('-C', '--cleanup', dest = 'cleanup',
        help = "kill'em all", default = False, action = 'store_true')
    parser.add_option('-n', '--noconfig', dest = 'noconfig',
        help = "Do not write inventory into config", default = True, action = 'store_false')

    (options, args) = parser.parse_args()


    config = get_conf(options.config, defaults)
    ec2    = get_ec2(config)
    client = boto3.client('ec2')
    resources = get_tagged(client, config['tag'])


    if options.cleanup:
        destroy(client, ec2, resources)
        sys.exit(0)

    mk_net(ec2, config, resources)

#    mk_subnets(ec2, vpc, config)
#    gw  = get_inet_gw(ec2, config)
#    if vpc.id not in [a['VpcId'] for a in gw.attachments]:
#        gw.attach_to_vpc(VpcId = vpc.id)
#
#    if options.noconfig:
#        f = open(cfg_file, 'w')
#        yaml.dump(config, f)
#        f.close()
#    else:
#        print(yaml.dump(config))

#    ec2.create_instances(**instance_defaults)






