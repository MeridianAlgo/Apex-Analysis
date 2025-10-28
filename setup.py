from setuptools import setup, find_packages

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name="apex_analysis",
    version="1.0.0",
    packages=find_packages(include=['src', 'src.*']),
    package_dir={'': '.'},
    install_requires=required,
    entry_points={
        'console_scripts': [
            'apex-analysis=src.ui:run_cli',
        ],
    },
    python_requires='>=3.8',
    author="Your Name",
    author_email="your.email@example.com",
    description="Apex Analysis - Stock market analysis tool with sentiment analysis",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/apex-analysis",
    include_package_data=True,
    package_data={
        '': ['*.txt', '*.md', '*.json'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
