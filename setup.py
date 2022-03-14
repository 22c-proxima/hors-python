from sys import version_info

from setuptools import setup, find_packages


MINIMAL_PY_VERSION = (3, 6)
MINIMAL_PY_VERSION_STR = '.'.join(map(str, MINIMAL_PY_VERSION))
if version_info < MINIMAL_PY_VERSION:
    raise RuntimeError('hors works only with Python {}+'.format(MINIMAL_PY_VERSION_STR))

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()
setup(
    name='hors',
    version='0.1.0',
    python_requires='>=' + MINIMAL_PY_VERSION_STR,
    description='Разбор дат в строке. Порт на python проекта https://github.com/DenisNP/Hors',
    author='Владимир Шомин, автор оригинала: Денис Пешехонов',
    author_email='22c.proxima@gmail.com',
    packages=find_packages(exclude=('tests',)),
    package_data={'hors': ['dict/time_words.txt']},
    license='MIT',
    long_description=long_description
)
