from setuptools import setup, find_packages
from os import name as osn

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='vk_captchasolver',
    version='1.0.5',
    author='comissor',
    author_email='None',
    description='VKontakte captcha solver with 91% accuracy right /// aiohttp',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='None',
    project_urls={
        'TG': 'vladikmakarov',
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    packages=find_packages(),
    include_package_data = True,
	install_requires = ['Pillow', 'numpy', 'requests', 'onnxruntime==1.19.2' if osn == 'nt' else 'onnxruntime>=1.19.2'],
    python_requires='>=3.6'
)