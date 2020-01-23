[![Build Status](https://drone.element-networks.nl/api/badges/Element-Networks/ansible-role-dns_server/status.svg)](https://drone.element-networks.nl/Element-Networks/ansible-role-dns_server)

# Ansible role to configure an authoratative nameserver for a local domain
This role will provide a means to install, configure and update a local DNS
server with information for systems in the network.

It will also configure a recursor on the same machine. By default, this looks like:

* PDNS-recursor : port 53 on 0.0.0.0
* PDNS-server   : port 5300 on 127.0.0.1

Check the defaults if you want to make changes.

This role uses PowerDNS as the server and can be used for deployment of
Active Directory.

The only supported OS for this role (for now) is Debian, as I did not have
an environment with CentOS/RHEL on hand when developing this.

# Setup
This role uses JP Mens' pdns_zone module for Ansible, you can find it, and it's
documentation [on his Github](https://github.com/jpmens/ansible-m-pdns_zone)

NOTE: This module does not work with PDNS 4.1 or higher(all tests I have ran failed)

You need to install this module in your Ansible project by placing it in
```
ansible_root/modules/pdns_zone.py
```

# Deployment
After the initial deployment of the server, you'll need to create NS records
for the locally served subdomain pointing to this server.

Then make sure the intented clients are able to connect to this server.

# Registering records
Manipulating the contents of the created zone can be done using Ansible's
nsupdate module. The DNS server is configured to automatically accept any
updates coming from the localhost. You can update the zone with a play like
this:

```
- name: 'Update zone'
  host: 'ns-sub.example.com'
  tasks:
    - nsupdate:
        server: "{{ dns_server_address }}"
        port: "{{ dns_server_port }}"
        ttl: '60'
        zone: "{{ dns_server_zone }}"
        record: 'host'
        value: '192.168.1.1'
        type: 'A'
      register: 'dns_updated'
      retries: 3
      delay: 3
      until: not dns_updated.failed
```
