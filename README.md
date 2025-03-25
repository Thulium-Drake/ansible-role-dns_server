# Ansible role to configure an authoratative nameserver for local domains
This role will provide a means to install, configure and update a local DNS
server with information for systems in the network.

Check the defaults if you want to make changes.

This role uses PowerDNS 4.9+ as the server and can be used for deployment of
Active Directory.

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
