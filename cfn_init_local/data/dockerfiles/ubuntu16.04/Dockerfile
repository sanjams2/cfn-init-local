FROM ubuntu:16.04

RUN apt-get update
RUN apt-get -y install python-setuptools wget python3-pip iptables
RUN wget https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz
RUN easy_install --script-dir /opt/aws/bin aws-cfn-bootstrap-latest.tar.gz