from setuptools import setup
from twitchobserver import __version__

setup(name="twitchobserver",
      version=__version__,
      description="Turn Twitch chatter into Python events.",
      url="https://github.com/JoshuaSkelly/twitch-observer",
      author="Joshua Skelton",
      author_email="joshua.skelton@gmail.com",
      license="MIT",
      packages=["twitchobserver"])