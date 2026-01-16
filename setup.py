"""Setup script for vm-verifier"""

from setuptools import setup, find_packages

setup(
    name="vm-verifier",
    version="0.1.0",
    description="Data generator verification tool for VM dataset project",
    packages=find_packages(),
    install_requires=[
        "pydantic==2.10.5",
        "numpy==1.26.4",
        "opencv-python-headless==4.9.0.80",
    ],
    entry_points={
        'console_scripts': [
            'vm-verify=vm_verify:main',
        ],
    },
    python_requires=">=3.8",
)
