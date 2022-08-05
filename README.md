# cfn-init-local
## Preface
My first OSS project. 

## Overview
Package designed to help with testing [CloudFormation Init](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-init.html) 
locally via [Docker](https://www.docker.com/) containers.

The problem is that testing CloudFormation Init for EC2 instances can be cumbersome. It requires deploying the CFN template,
logging onto the instance, investigating logs, fixing the issues and repeating. That process can take hours which makes it
especially annoying when errors are small things like syntax errors. Enter cfn-init-local. cfn-init-local is designed
to mimic the CloudFormation Init process but doing so locally using containers. This can reduce the validation and 
testing of your CloudFormation Init stanzas to seconds.

## Getting started
### Installation
```bash
pip3 install --user git+https://github.com/jsanders67/cfn-init-local
```

### Example 
Build the `cfn-init-local` example docker image:

```bash
location=$(pip3 show cfn-init-local | grep Location | cut -d' ' -f2)/cfn_init_local \
    && docker build -t cfn-init-local -f $location/data/dockerfiles/alinux2/Dockerfile $location
```

Then run cfn-init-local:

```bash
cfn-init-local \
    --template-name SomeTemplate \
    --template-body $location/data/test/test_template.json \
    --image cfn-init-local
```

If you get errors like: ```command not found: cfn-init-local``` ensure your user-specific Python bin directory is 
on your path. On macOS that looks like ```$HOME/Library/Python/3.7/bin``` for Python3.7.

### Usage:
Run
```bash
cfn-init-local --help
```

### Building Docker Images
Users will likely need to build their own Docker images that mimic the OS they will be launching their EC2 instances
with. The docker images must have the following:
- `aws-cfn-bootstrap` installed
- `iptables` installed
- `python3` installed

Some examples of a minimal Dockerfiles that do this can be found [here](cfn_init_local/data/dockerfiles/). 
I understand at the moment this is slightly cumbersome and puts more work on the user. 
I am working on making this process easier so that users can simply bring their image and the necessary
libraries will be installed at runtime.   

## Features
### Metadata Server
cfn-init-local ships with a mock EC2 metadata server 
(see: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html). This server can be run by executing 
`python3 cfn_init_local/http/server.py --metadata "$(cat data/default/default_metadata.json)"`. 
If you require updating the IP address to match that of metadata servers actually running in EC2 (i.e. 169.254.169.254), 
you can run the server in `--container-mode`. Which will set the appropriate routes via `iptables`.

### CFN Resource Server
Not as much of a feature, but cfn-init-local also ships with a CloudFormation Resource metadata server. 
This literally just servers the json you specify at runtime back when it receives a GET request.
You can use this in conjunction with the default mock response included in this package to form a 
Mock CFN GetStackResource server. Run this by executing
`python3 cfn_init_local/http/server.py --cfn-resource "$(cat data/test/test_describe_stack_resource_response.json)"`.
This was reverse engineered from what CloudFormation returns on a 
[describe stack resource](https://docs.aws.amazon.com/cli/latest/reference/cloudformation/describe-stack-resources.html) 
request. It is not documented by CloudFormation so this just servers as a best effort, 
but could theoretically be used outside of cfn-init-local for other testing purposes.

## Current Limitations
### Docker Containers
Using Docker containers enables higher testing velocity but sacrifices environment fidelity. 
Therefore, the onus is on the user to properly configure their docker images to emulate the OS 
images they are using for their EC2 instances. cfn-init-local ships with a Dockerfile that can 
be used to create a bare-bones image with the minimum necessary requirements to use cfn-init-local.
One can use this as a starting place.

### No Template Evaluation
Today, this framework does not parse your template and evaluate it as CloudFormation would. 
Meaning, it does not execute the CloudFormation functions you may have specified or insert variables appropriately. 
This forces the user to modify the template to be what they expect from CloudFormation after 
it is processed. Adding basic evaluation functionality is being worked on

## TODOs:
- Simplify building docker images. Find a way to dynamically install necessary dependencies or attach them.
- Template Evaluation
- Complete documentation
