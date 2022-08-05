import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="cfn-init-local",
    version="0.0.1",
    author="sanjams",
    author_email="james3sanders@gmail.com",
    description="A helper CLI for testing CloudFormation Init locally",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'docker'
    ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'cfn-init-local = cfn_init_local.cli:main'
        ]
    })
