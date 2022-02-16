from setuptools import setup, find_packages

from components import __version__

extra_test = [
    'pytest>=7.0.0',
    'pytest-cov>=3.0.0',
    'pytest-env>=0.6.2'
]

setup(
    name='kfp_components',
    version=__version__,
    description='custom kubeflow components',
    long_description=open('README.md').read(),

    url='https://github.com/anifort/kfp_components',
    author='Christos Aniftos',
    author_email='aniftos@gmail.com',

    packages=find_packages(exclude=['tests*']),

    install_requires=["google-cloud-aiplatform==1.10.0",
                      "google-cloud-bigquery==2.32.0",
                      "kfp==1.8.11"],

    keywords=['python', 'kfp', 'components'],

    #extras_require={
    #    'test': extra_test,
    #},

#    entry_points={
#        'console_scripts': [
#            'add=kfp_components.featurestore.export:__main__',
#        ],
#    },

    classifiers=[
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
)