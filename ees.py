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
        'region_name': 'eu-central-1',
        'vpc_cidr_block': '10.0.0.0/24',
        'network': {
            'fe': {
                'cidr': '10.0.0.0/26',
                'id': None,
                'zone': 'eu-central-1a',
                },
            'be': {
                'cidr': '10.0.0.64/26',
                'id': None,
                'zone': 'eu-central-1a',
                },
            },
        'internet_gateway': None,
        }

instance_defaults = {
        'ImageId': 'ami-accff2b1',
        'MinCount': 1,
        'MaxCount': 1,
        'KeyName': 'es_cluster',
        'InstanceType': 't2.micro',
        'Placement': {
            'AvailabilityZone': 'eu-central-1a',
            'Tenancy': 'default',
            },
        'SubnetId': 'subnet-ba4e2ed3',
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

def get_vpc(ec2, config, force):

    if 'vpc_id' in config and config['vpc_id'] is not None:
        for v in ec2.vpcs.all():
            if config['vpc_id'] == v.id:
                print("vpc %s exists, resting" % v.id)
                return v

    vpc = ec2.create_vpc(
            DryRun = False,
            CidrBlock = config['vpc_cidr_block'],
            InstanceTenancy = 'default'
            )
    config['vpc_id'] = vpc.id
    print "created new %s vpc: %s" % (n, s.id)


    return vpc


def mk_subnets(ec2, vpc, config):

    subnets = [ s.id for s in vpc.subnets.all() ]

    for n in ['fe', 'be']:
        if config['network'][n]['id'] is None or config['network'][n]['id'] not in subnets:
               s = vpc.create_subnet(
                    DryRun = False,
                    CidrBlock = config['network'][n]['cidr'],
                    AvailabilityZone = config['network'][n]['zone']
                    )
               print "created new %s subnet: %s" % (n, s.id)
               config['network'][n]['id'] = s.id
        else:
            print "%s subnet %s exists, resting" % (n, config['network'][n]['id'])

def get_inet_gw(ec2, config):

    gws = [ g for g in ec2.internet_gateways.all()]
    for gw in gws:
        if gw.id == config['internet_gateway']:
            print("internet gateway %s exists, resting" % config['internet_gateway'])
            return gw
    gw = ec2.create_internet_gateway()
    config['internet_gateway'] = gw.id
    print("Created internet gateway %s" % gw.id)
    return gw



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

    if options.cleanup:
        for v in ec2.vpcs.all():
            if not v.is_default:
                print "removing VCS %s" % v.id
                for s in v.subnets.all():
                    print "   removing subnet %s" % s.id
                    s.delete()
                v.delete()
        sys.exit(0)

    if ec2 is None:
        print("Cannot create EC2 resource")
        sys.exit(100)

    vpc = get_vpc(ec2, config, options.force)
    mk_subnets(ec2, vpc, config)
    gw  = get_inet_gw(ec2, config)
    if vpc.id not in [a['VpcId'] for a in gw.attachments]:
        gw.attach_to_vpc(VpcId = vpc.id)

    if options.noconfig:
        f = open(cfg_file, 'w')
        yaml.dump(config, f)
        f.close()
    else:
        print(yaml.dump(config))

#    ec2.create_instances(**instance_defaults)






