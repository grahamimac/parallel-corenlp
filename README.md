# Run CoreNLP in Parallel with Spark

A relatively quick, easy, and effective way to spin up a Spark cluster with the [Stanford CoreNLP Server 3.6.0](http://stanfordnlp.github.io/CoreNLP/download.html) installed and running on all nodes.

### Setup

Before we begin, we'll need to install Spark, the Spark EC2 package, Fabric, and make a small edit.

1. Install Spark. Go to the [Spark download page](http://spark.apache.org/downloads.html), select the most recent version, and download the file, either manually or using the relevant `wget` or `curl` command for your system. Then unzip the file manually or via command-line using `tar`. The procedure may look something like:
	
	```bash
	curl -o http://d3kbcqa49mib13.cloudfront.net/spark-2.0.1-bin-hadoop2.7.tgz
	tar -xvzf spark-2.0.1-bin-hadoop2.7.tgz
	```

2. Clone a copy of Spark EC2 into a directory called ec2 within the spark folder you just unpacked. If you don't have git, you'll need to install it according to the [instructions here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git). The procedure looks something like:
	
	```bash
	cd spark-2.0.1-bin-hadoop2.7
	git clone https://github.com/amplab/spark-ec2.git
	mv spark-ec2 ec2
	```

3. In the ec2 (or if you didn't rename it, spark-ec2) folder you just downloaded, open the file spark_ec2.py. Within the file, find the function get_spark_ami, which should look something like `def get_spark_ami(opts):`. At the end of the function, replace
	
	```python
	    print("Spark AMI: " + ami)
	    return ami
	```

	with 

	```python
		ami = "ami-010f4e16"
		print("Spark AMI: " + ami)
		return ami
	```

	This hardcodes the AMI used by the script to a Spark EC2 AMI with more recent updates, Docker, and CoreNLP installed.

4. Install Fabric, which will parallelize starting the docker service when the cluster starts up. Install Fabric according to the [instructions here](http://www.fabfile.org/installing.html). Copy the fabfile.py file from this repo to your ec2 directory, which looks like:

	```bash
	cd spark-2.0.1-bin-hadoop2.7/ec2/
	git clone https://github.com/grahamimac/parallel-corenlp.git
	```

### Running

Now we're ready to spin up the cluster on EC2. Before you start, make sure you read and understand the sections **Before You Start** and **Launching a Cluster** on the [Spark-EC2 github page's README](https://github.com/amplab/spark-ec2/tree/branch-2.0).

1. Start up the cluster. The procedure looks something like:

	```bash
	cd spark-2.0.1-bin-hadoop2.7/ec2/
	./spark-ec2 --key-pair=keypairname --identity-file=keypairname.pem -s 10 --instance-type=m3.large --spot-price=0.05 --user root launch test-cluster
	```

	You may wait a few minutes as the EC2 instances start up, enter SSH ready mode, and see all the Spark requirements installed.

2. Ensure the CoreNLP server is running on Docker on all nodes using Fabric. WARNING: If you have other instances running on AWS not part of this procedure, be sure to include their names in the list in fabfile.py line 51, `notin_names = ["Testing Twitter"]`. So, for example, if you have two instances, named "Instance-1" and "Another Instance", line 51 in fabfile.py would look like `notin-names = ["Instance-1", "Another Instance"]`. The command is:

	```bash
	fab set_hosts:us-east-1,False run_docker_CoreNLP
	```

	You may wait a few seconds as this command executes on all instances on AWS. 

3. Run your CoreNLP program using Spark! The cluster should now be ready to accept HTTP requests to the CoreNLP Server over local IP address 172.17.0.2 and port 9000 on each node. EXAMPLE: In python, a map function to request CoreNLP sentiment analysis might look like:

	```python
	def map_sentiment(dataline):
		import requests
		import json
		url = 'http://172.17.0.2:9000/?properties=%7B%22annotators%22:%22tokenize,ssplit,sentiment%22,%22outputFormat%22:%22json%22%7D'
		datatext = dataline[0][2]
		data = requests.post(url, data={"q":datatext}, timeout=60).text
		json_data = json.loads(data)
		sents = [int(x['sentimentValue']) for x in json_data['sentences'] if x['sentimentValue'] is not None]
		sentVal = float(sum(sents))/len(sents)
		return datatext, sentVal
	```

	The function allows each node to make a local request to the CoreNLP service installed on the node, which allows data analysts to parallelize complex NLP processes such as sentiment across multiple nodes with Spark. One note: be sure the Spark process does not take up all the available memory on each node - the CoreNLP server should be allowed at least 2 GB of free memory to function effectively.