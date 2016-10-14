# Modified from https://abhishek-tiwari.com/hacking/interacting-with-tagged-ec2-instances-using-fabric

import boto, urllib2
from boto.ec2 import connect_to_region
from fabric.api import env, run, cd, settings, sudo
from fabric.api import parallel
import os
import sys

REGION = "us-east-1"
MASTER = "False"

# Server user, normally AWS Ubuntu instances have default user "ubuntu"
env.user = "root"

# List of AWS private key Files
env.key_filename = ["/path/to/keypair.pem"]

# fab set_hosts:us-east-1,False run_docker_CoreNLP
@parallel
def run_docker_CoreNLP():
	run('service docker stop')
	run('service docker start')
	run('docker start corenlp_test')

# Fabric task to set env.hosts based on tag key-value pair
def set_hosts(region=REGION,master=MASTER):
	env.hosts = _get_public_dns(region,master)

# Private method to get public DNS name for instance with given tag key and value pair
def _get_public_dns(region,master):
	notin_names = ["Testing Twitter"]
	public_dns = []
	connection = _create_connection(region)
	reservations = connection.get_all_instances()
	for reservation in reservations:
		for instance in reservation.instances:
			if "Name" in instance.tags and instance.update() == 'running':
				if master == "False":
					if instance.tags["Name"] not in notin_names and "master" not in instance.tags["Name"]:
						print "Instance", instance.public_dns_name
						public_dns.append(str(instance.public_dns_name))
				elif master == "True":
					if "master" in instance.tags["Name"]:
						print "Instance", instance.public_dns_name
						public_dns.append(str(instance.public_dns_name))
				elif master == "all":
					if instance.tags["Name"] != "Testing Twitter":
						print "Instance", instance.public_dns_name
						public_dns.append(str(instance.public_dns_name))										
	return public_dns

# Private method for getting AWS connection
def _create_connection(region):
	print "Connecting to ", region

	conn = connect_to_region(
		region_name = region, 
		aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"), 
		aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
	)

	print "Connection with AWS established"
	return conn