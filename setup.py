from setuptools import setup, find_packages

setup(
    name='BuildingLinkLink',
    version='0.0.1',
    packages=find_packages('buildinglink_link'),
    package_data={"": ["config/*"]},
    long_description=open('README.md').read(),
    entry_points={
        'console_scripts': ['run_bll=buildinglink_link.main:main']
    }
)