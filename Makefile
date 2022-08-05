
.PHONY: build setup test

run: clean build install

clean:
	pip3 uninstall -y cfn-init-local

build:
	python3 setup.py sdist bdist_wheel

install:
	pip3 install --user dist/cfn*.whl

setup:
	python3 -m pip install --user --upgrade setuptools wheel

local:
	pip3 install --user -e .

test-image:
	docker build -t cfn-init-local -f cfn_init_local/data/dockerfiles/alinux2/Dockerfile .

example: test-image
	cfn-init-local --template-name SomeTemplate --template-body cfn_init_local/data/test/test_template.json --image cfn-init-local

test:
	python3 -m unittest

install-remote:
	 pip3 install --user git+https://gitlab.com/sanjams/cfn-init-local