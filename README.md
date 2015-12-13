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

Requirements can be found in project [wiki](https://github.com/alex-goncharov/muutep/wiki/Requirements).

#### Used stuff

List of used documentaion and other resources can be found in project [wiki](https://github.com/alex-goncharov/muutep/wiki/Docs-and-References).

## [General Talk](https://github.com/alex-goncharov/muutep/wiki/General-talk)


