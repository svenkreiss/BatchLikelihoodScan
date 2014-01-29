from distutils.core import setup
 
setup(
    name='BatchLikelihoodScan',
    version='1.0.3',
    packages=['BatchLikelihoodScan', 'BatchLikelihoodScan.Plugins'],
    license='LICENSE',
    description='Creates (profile) likelihood scans of RooFit/RooStats models in any dimension locally or on batch systems.',
    long_description=open('README.md').read(),
    author='Sven Kreiss, Kyle Cranmer',
    author_email='sk@svenkreiss.com',

    dependency_links= [
        'https://github.com/svenkreiss/PyROOTUtils/tarball/master#egg=PyROOTUtils-1.0.1',
    ],
    install_requires= ['PyROOTUtils'],

    entry_points={
        'console_scripts': [
            'batch_likelihood_scan = BatchLikelihoodScan.scan:main',
            'batch_likelihood_plot = BatchLikelihoodScan.plot:main',
        ]
    }
)
