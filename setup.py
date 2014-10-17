from setuptools import setup, find_packages


setup(
    name='ajax',
    version='1.2.0',
    description='A simple framework for creating AJAX endpoints in Django.',
    long_description='',
    keywords='django, ajax',
    author='Joseph C. Stump',
    author_email='joe@stu.mp',
    url='https://github.com/joestump/django-ajax',
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    install_requires=[
        'decorator',
        'django-appconf==0.6',
    ],
    extras_require={
        'Tagging': ['taggit']
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: Django",
        "Environment :: Web Environment",
    ]
)
