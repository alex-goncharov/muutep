# muutep

Poking around AWS

## Tasks

1. Provide a tool that can create AWS VPC, wich is capable of hosting ElasticSearch cluster
2. Provide a toolset that installs and configures ElasticSearch cluster in AWS instance above
  a. Cluster should be a cluster: multinode etc
  b. Cluster can be accessed in a secure maner
  c. Cluster shoud have RBAC configured
3. Provide means of the monitoring for the solution
4. Explore the possibility of using OAuth in addition to local user database
5. Document all above
6. Provide an interesting blah-blah on the matter.

## A short solution plan

1. Two tier network built to host frontend and backend services.
  a. fronted - reverse proxy on nginx, this will do ssl termination and aaa
  b. backend - will host elastic search cluster, which is reachable via REST through 1.a.
2. There is a need for a jump/bastion host to reach solution with ansible
3. As quick and dirty path, nginx will hold all ES nodes in upstream configuration, unless AWS LB can be configured quick
4. ES metrics and alarms are quite extensive, will need to look if they can be added to AWS dashboard, or can spinof ganglia instance quickly


## Tools and usage

### ees.py

**Aka elastic elasticsearch**

This python utility will provide easy cli to accomplish task 1 and 2. It should also have managerial capabilities like cleanup, add/remove pieces, etc.

ATM confiugres network and starts and instance. It looks like everything is in place, still I cannot reach it yet for some reason.

#### Requires

YOU WANT TO BE CAREFUL WITH "-C" FLAG

Python 2.7
Boto3 https://boto3.readthedocs.org (configured)
SSH keys configured to access instances
AWS access, keys and all.


#### Used stuff

http://boto3.readthedocs.org/en/latest/index.html
http://docs.aws.amazon.com/AWSEC2/latest/UserGuide
http://chairnerd.seatgeek.com/oauth-support-for-nginx-with-lua/
https://www.elastic.co/guide/en/elasticsearch/guide/current/index.html
http://docs.ansible.com/
https://github.com/bitly/oauth2_proxy

##### es rbac
https://www.elastic.co/blog/playing-http-tricks-nginx
https://github.com/Asquera/elasticsearch-http-basic

## Interesting blah-blah

### Ansible

I have mentioned, that I do not like Ansible, now I remember why: it has push based architecture, which means, that is has to know all servers it is managing and must have a way of accessing them. First is not a problem really (althouhg i must admit, that discovery delay is quite annoying) and can be worked around: have a separate discovery service, for example. Second, however, can present challenges, which can lead to security compromises. Normally, a service would run in a sort of a bubble, which limits incoming requests to a load balanced VIP or something of the sort. This ensures that every service user (be that human or application) can access the service throuhg a single address and "knowledge" about service infrastructure is limited to a service bubble. With push architecrture, managing servers should reside in the same address space and must be able to access each server. Pull architecture is more flexible in this matter - it allows managemnet servers to sit in the management service bubble and being accessed like a usual service. The difficulties increase when east-west traffic limitations are in place in addition to usual north-south.

It's pretty neat to replace 'for i in ..;do ssh' when compared to mCollective, which looks a bit monstrous if you have a lot of small groups of servers. Although for a usual web farm i would prefer
MCO any day mainly because of it's pub-sub architecture - it's much much much quicker

Just run Ansible kick in debug mode - scared the hell out of me - 3 and I kid you not, 3! ssh sessions to manage one item on one server, that's looks like a waste.



### AWS 

It's lovely, I though it is, but it's even better. Just need to get hands properly dirty with it.


