from setuptools import setup, find_packages

from pip.req import parse_requirements
install_reqs = parse_requirements("requirements.txt", session=False)
reqs = [str(ir.req) for ir in install_reqs]


setup(
    name='numeric-labelling',
    version='0.1',
    packages=find_packages(),
    install_requires=reqs,
    url='https://github.com/sebneu/number_labelling',
    license='Apache License Version 2.0',
    author='Sebastian Neumaier',
    author_email='seb.neumaier@gmail.com',
    description='Multi-level semantic labelling of numerical values.'
)
