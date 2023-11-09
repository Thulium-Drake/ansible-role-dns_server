#!/usr/bin/env python3
"""
Generate DNS PTR zones based on the contents of a forward zone in PowerDNS.

It has been tailored to be used in tandem with a PowerDNS server configured
by the Ansible role.

This file is managed by Ansible, YOUR CHANGES WILL BE LOST!
"""
import sys
import os
import configparser
import json
import subprocess

try:
    import dns.reversename
    import dns.rdata
except ImportError:
    print('ERROR: requires dnspython!')
    sys.exit(1)

try:
    import requests
except ImportError:
    print('ERROR: requires requests!')
    sys.exit(1)

conf_found = False

try:
    with open("/etc/powerdns/pdns.d/ansible_pdns.conf", "r") as f:
        config_string = '[pdns]\n' + f.read()
        conf_found = True
except (FileNotFoundError, IOError):
    conf_found = False

if not conf_found:
    try:
        with open("/etc/pdns/pdns.d/ansible_pdns.conf", "r") as f:
            config_string = '[pdns]\n' + f.read()
            conf_found = True
    except (FileNotFoundError, IOError):
        conf_found = False

if not conf_found:
    print('ERROR: PowerDNS config not found, please run Ansible role again')
    sys.exit(1)

config = configparser.ConfigParser()
config.read_string(config_string)

api_auth_header = {'X-API-KEY': config['pdns']['api-key']}
api_baseurl = 'http://' + config['pdns']['webserver-address'] + ':' + config['pdns']['webserver-port'] + '/api/v1/servers/localhost/'

zones_url = api_baseurl + 'zones'
zones_r = requests.get(zones_url, headers=api_auth_header)
zones_json = zones_r.json()

arpa_zone_contents = []
soa_record_found = False
ns_record_found = False

for zone_dict in zones_json:
    zone_content_url = zones_url + '/' + zone_dict['id']
    zone_content_r = requests.get(zone_content_url, headers=api_auth_header)
    zone_content_json = zone_content_r.json()
    for record in zone_content_json['rrsets']:
        if zone_dict['id'] == 'arpa.':
            if record['type'] == 'NS':
                ns_record_found = True
                ns_record_data = "arpa. {ttl} IN NS {value}".format(
                        ttl=record['ttl'],
                        value=record['records'][0]['content'])
                arpa_zone_contents.append(ns_record_data)
            if record['type'] == 'SOA':
                soa_record_found = True
                soa_record_data = dns.rdata.from_text(dns.rdataclass.IN, dns.rdatatype.SOA, record['records'][0]['content'])
                new_serial = soa_record_data.serial + 1
                new_soa_record = "arpa. 300 IN SOA {mname} {rname} {serial} {refresh} {retry} {expire} {minimum}".format(
                        mname=str(soa_record_data.mname),
                        rname=str(soa_record_data.rname),
                        serial=new_serial,
                        refresh=soa_record_data.refresh,
                        retry=soa_record_data.retry,
                        expire=soa_record_data.expire,
                        minimum=soa_record_data.minimum)

                arpa_zone_contents.append(new_soa_record)
        else:
            if record['type'] == 'A' or record['type'] == 'AAAA':
                ptr_host = record['name']
                if ptr_host.startswith('ipa-ca'):
                    # Skip processing for records named ipa-ca, as this breaks FreeIPA domains
                    continue
                ptr_ip = record['records'][0]['content']
                ptr_record = dns.reversename.from_address(ptr_ip)
                arpa_zone_contents.append(str(ptr_record) + ' 300 IN PTR ' + ptr_host)

if not soa_record_found:
    default_soa_record = "arpa. 300 IN SOA {hostname} hostmaster.arpa 20200101 10800 3600 604800 3600".format(
            hostname=os.uname().nodename + '.')
    arpa_zone_contents.append(default_soa_record)

if not ns_record_found:
    default_ns_record = "arpa. 300 IN NS {hostname}".format(
            hostname=os.uname().nodename + '.')
    arpa_zone_contents.append(default_ns_record)

with open("/tmp/reverse.zone", "w+") as z:
    z.truncate()
    for line in arpa_zone_contents:
        z.write(line + "\n")

# TODO: investigate if this can be handled through the API
with open(os.devnull, 'wb') as devnull:
    subprocess.check_call(["/usr/bin/pdnsutil", "load-zone", "arpa", "/tmp/reverse.zone"], stdout=devnull, stderr=subprocess.STDOUT)
    os.remove("/tmp/reverse.zone")
