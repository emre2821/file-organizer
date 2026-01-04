"""Setup script for file-organizer."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text() if readme_file.exists() else ''

setup(
    name='file-organizer',
    version='1.0.0',
    author='Emre',
    description='Organize files from multiple sources with customizable schemas',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/emre2821/file-organizer',
    packages=find_packages(),
    install_requires=[
        'click>=8.1.0',
        'pyyaml>=6.0',
        'rich>=13.0.0',
        'google-api-python-client>=2.0.0',
        'google-auth-httplib2>=0.1.0',
        'google-auth-oauthlib>=1.0.0',
        'PyGithub>=2.0.0',
        'python-dateutil>=2.8.0',
    ],
    entry_points={
        'console_scripts': [
            'file-organizer=file_organizer.cli:cli',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'Topic :: System :: Filesystems',
        'Topic :: Utilities',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
    python_requires='>=3.8',
    keywords='file organization filesystem github google-drive automation',
)
