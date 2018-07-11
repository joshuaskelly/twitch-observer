from setuptools import setup
from twitchobserver import __version__

with open('README.md') as f:
    long_description = f.read()

setup(name='twitchobserver',
      version=__version__,
      description='Turn Twitch chatter into Python events.',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/JoshuaSkelly/twitch-observer',
      author='Joshua Skelton',
      author_email='joshua.skelton@gmail.com',
      license='MIT',
      packages=['twitchobserver'], 
      keywords=['twitch.tv', 'twitch', 'video games', 'chatbot'],
      classifiers=[
            'Intended Audience :: Developers',
            'License :: OSI Approved :: MIT License',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 3',
            'Topic :: Software Development :: Libraries :: Python Modules'
      ])

