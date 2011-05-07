from setuptools import setup, find_packages
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'

setup(
    name='django-ajax',
    version='0.1.0',
    description='A simple framework for creating AJAX endpoints in Django.',
    long_description='',
    keywords='django, ajax',
    author='Joseph C. Stump',
    author_email='joe@stu.mp',
    url='https://github.com/joestump/django-ajax',
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    install_requires=['decorator',],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
        "Environment :: Web Environment",
    ],
    test_suite="tests",
    tests_require=['coverage', 'mock', 'django']
)
