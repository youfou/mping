import logging

from setuptools import setup, find_packages

readme_file = 'README.md'

try:
    import pypandoc

    long_description = pypandoc.convert(readme_file, to='rst')
except ImportError:
    logging.warning('pypandoc module not found, long_description will be the raw text instead.')
    with open(readme_file, encoding='utf-8') as fp:
        long_description = fp.read()

setup(
    name='mping',
    version='0.1.1',
    packages=find_packages(),
    package_data={
        '': ['*.md'],
    },
    include_package_data=True,

    entry_points={
        'console_scripts': [
            'mping = mping.mping:main'
        ]
    },

    url='https://github.com/youfou/mping',
    license='Apache 2.0',
    author='Youfou',
    author_email='youfou@qq.com',
    description='Ping multiple hosts concurrently and find the fastest to you.',
    long_description=long_description,
    keywords=[
        'ping',
        'host',
        'monitor'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Networking :: Monitoring',
        'Topic :: Utilities',
    ]
)
