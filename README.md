# muutep

A test assignment given by a company that is in search for a seasoned devops.

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

## Tools and usage

### ees.py

**Aka elastic elasticsearch**

This python utility will provide easy cli to accomplish task 1 and 2. It should also have managerial capabilities like cleanup, add/remove pieces, etc.

#### Requires

Python 2.7
Boto 3 https://boto3.readthedocs.org (configured)
AWS access, keys and all.



## Interesting blah-blah

### Ansible

I have mentioned on our interview, that I do not like Ansible, now I remember why: it has push based architecture, which means, that is has to know all servers it is managing and must have a way of accessing them. First is not a problem really (althouhg i must admit, that discovery delay is quite annoying) and can be worked around: have a separate discovery service, for example. Second, however, can present challenges, which can lead to security compromises. Normally, a service would run in a sort of a bubble, which limits incoming requests to a load balanced VIP or something of the sort. This ensures that every service user (be that human or application) can access the service throuhg a single address and "knowledge" about service infrastructure is limited to a service bubble. With push architecrture, managing servers should reside in the same address space and must be able to access each server. Pull architecture is more flexible in this matter - it allows managemnet servers to sit in the management service bubble and being accessed like a usual service. The difficulties increase when east-west traffic limitations are in place in addition to usual north-south.  
