[![Build Status](https://drone.element-networks.nl/api/badges/Element-Networks/ansible-role-dns_server/status.svg)](https://drone.element-networks.nl/Element-Networks/ansible-role-dns_server)

# Ansible role to configure an authoratative nameserver for local domains
This role will provide a means to install, configure and update a local DNS
server with information for systems in the network.

It can also configure a recursor on the same machine. By default, this looks like:

* PDNS-recursor : port 53 on 0.0.0.0
* PDNS-server   : port 5300 on 127.0.0.1

Check the defaults if you want to make changes.

This role uses PowerDNS as the server and can be used for deployment of
Active Directory.

The only supported OS for this role (for now) is Debian, as I did not have
an environment with CentOS/RHEL on hand when developing this.

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
        zone: "{{ zone }}"
        record: 'host'
        value: '192.168.1.1'
        type: 'A'
      register: 'dns_updated'
      retries: 3
      delay: 3
      until: not dns_updated.failed
```
