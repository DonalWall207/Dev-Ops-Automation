# Import necessary Python libraries

import boto3
import webbrowser
import logging
import time
import json
import uuid
import subprocess
import requests

# Configuring a log file  to write all the information logged to this file

logging.basicConfig(filename='logfile.log',format='%(asctime)s %(levelname)-8s %(message)s',level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S')

logging.info("Program Started")

try:
    ec2 = boto3.resource('ec2')
    
    # Create a new EC2 instance with specific configurations
    
    new_instances = ec2.create_instances(
    TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': 'Web Server'
                            },
                            ]
                            },
                        ],
    ImageId='ami-0bb4c991fa89d4b9b',
    MinCount=1,
    MaxCount=1,
    InstanceType='t2.nano',
    UserData="""#!/bin/bash
    yum install httpd -y
    systemctl enable httpd
    systemctl start httpd

    echo "<?php echo '<p>Hello Welcome to My EC2 Instance Page</p>'; ?>" >> test.php

    echo '<html>' > index.html

    echo 'Private IP address: ' >> index.html
    curl http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html 

    echo '<br>' >> index.html

    echo " Public IP address" >> index.html
    curl http://169.254.169.254/latest/meta-data/public-ipv4 >> index.html 

    echo '<br>' >> index.html

    echo " Instance Type " >> index.html
    curl http://169.254.169.254/latest/meta-data/instance-type >> index.html

    echo '<br>' >> index.html

    echo " Availability Zone " >> index.html
    curl http://169.254.169.254/latest/meta-data/placement/availability-zone >> index.html

    echo '<br>' >> index.html

    echo " Instance AMI " >> index.html
    curl http://169.254.169.254/latest/meta-data/ami-id >> index.html

    echo '<br>' >> index.html

    echo " Security Group " >> index.html
    curl http://169.254.169.254/latest/meta-data/security-groups >> index.html    

    cp index.html /var/www/html/index.html""",
    SecurityGroupIds=[
            'sg-03162d7e0fc2588c7',
        ],
    KeyName="MyKey")
    
 # Wait for the EC2 instance to be in the "running" state
    new_instances[0].wait_until_running()
    time.sleep(10)
    
    # Reload the instance information
    new_instances[0].reload()
    
    # Print messages indicating that the instance is running and its public IP address
    print("Done Waiting")
    print("Instance is now running:" + str((new_instances[0].public_ip_address)))
    print (new_instances[0].id)
    
    logging.info("Instance " + new_instances[0].public_ip_address + "  has been created and is now running")
    
    # Open a web browser tab with the public IP address of the EC2 instance
    
    webpage = f"http://{new_instances[0].public_ip_address}/"
    webbrowser.open_new_tab(webpage)
except Exception as e:
    print(f"An error occurred: {e}")
    logging.error("Instance has failed to be created")
    
try:    
    s3 = boto3.resource("s3")
    # Generate a random bucket name
    bucket_name = f"{uuid.uuid4().hex[:5]}-dwall"
    # Create the S3 bucket with the generated name
    s3.create_bucket(Bucket=bucket_name)
    
    logging.info(bucket_name + " Bucket has been created")
    print("Bucket has been created")
    
    #Updating the bucket policy to allow public access to it

    s3client = boto3.client("s3")
    s3client.delete_public_access_block(Bucket=bucket_name)   
    bucket_policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                    {
                        "Sid": "PublicReadGetObject",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": ["s3:GetObject"],
                        "Resource": f"arn:aws:s3:::{bucket_name}/*"
                    }
                    ]
            }
    s3.Bucket(bucket_name).Policy().put(Policy=json.dumps(bucket_policy))
    
    # Configure the S3 bucket as a static website with error and index documents
    
    website_configuration = {
        'ErrorDocument': {'Key': 'error.html'},
        'IndexDocument': {'Suffix': 'index.html'},
        }

    bucket_website = s3.BucketWebsite(bucket_name)
    response = bucket_website.put(WebsiteConfiguration=website_configuration)

    
    # Define object names
    
    object_name='index.html'
    object_name2= 'logo.jpg'
    
    # Upload the HTML and image files to the S3 bucket
    
    s3.Object(bucket_name, object_name).put(Body=open(object_name, 'rb'),ContentType="text/html")
    s3.Object(bucket_name, object_name2).put(Body=open(object_name2, 'rb'),ContentType="image/jpeg")
except Exception as e:
    print(f"An error occurred: {e}")


try:
    # Generate the URL of the S3 website and open it in a web browser tab
    
    website_url = f"http://{bucket_name}.s3-website-{s3.meta.client.meta.region_name}.amazonaws.com"
    logging.info("Website has been Launched")
    webbrowser.open_new_tab(website_url)
    print("S3 Website has been launched")
    
except Exception as e:
    print(f"An error occurred while opening the S3 website: {e}")
    
try:
    # Prepare for running shell commands on the EC2 instance
        subprocess.run("chmod 400 MyKey.pem", shell=True)
        subprocess.run("scp -i MyKey.pem monitoring.sh ec2-user@" +
        str(new_instances[0].public_ip_address) + ":.",shell=True)
        print("scp check")
        
        subprocess.run("ssh -i MyKey.pem ec2-user@" + str(new_instances[0].public_ip_address) +
        " 'chmod 700 monitoring.sh'",shell=True)
        print("ssh check")
        
        subprocess.run("ssh -i MyKey.pem  ec2-user@" + str(new_instances[0].public_ip_address)
        + " ' ./monitoring.sh'",shell=True)
except Exception as e:
   print(e)