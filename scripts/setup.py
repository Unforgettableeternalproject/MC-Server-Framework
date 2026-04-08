"""
setup.py - 將框架打包成 Python 套件
"""

from setuptools import setup, find_packages
from pathlib import Path

# 讀取 README
readme_file = Path(__file__).parent / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

# 讀取版本號
version = '0.1.0'

setup(
    name='mc-server-framework',
    version=version,
    description='Minecraft 本機伺服器宿主管理框架',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='MC-Server-Framework Team',
    url='https://github.com/your-username/MC-Server-Framework',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'typer[all]>=0.9.0',
        'rich>=13.0.0',
        'PyYAML>=6.0',
        'requests>=2.31.0',
        'psutil>=5.9.0',
        'python-dateutil>=2.8.2',
    ],
    entry_points={
        'console_scripts': [
            'mc-host=app.cli.commands:app',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Topic :: Games/Entertainment',
        'Topic :: System :: Systems Administration',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
    ],
    python_requires='>=3.8',
    keywords='minecraft server management dns cloudflare forge',
    project_urls={
        'Bug Reports': 'https://github.com/your-username/MC-Server-Framework/issues',
        'Documentation': 'https://github.com/your-username/MC-Server-Framework/wiki',
        'Source': 'https://github.com/your-username/MC-Server-Framework',
    },
)
