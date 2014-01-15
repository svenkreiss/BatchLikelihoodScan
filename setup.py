from distutils.core import setup
 
setup(
    name='BatchLikelihoodScan',
    version='1.0',
    packages=['BatchLikelihoodScan', ],
    license='LICENSE',
    description='Creates (profile) likelihood scans of RooFit/RooStats models in any dimension locally or on batch systems.',
    long_description=open('README.md').read(),
    author='Sven Kreiss, Kyle Cranmer',
    author_email='sk@svenkreiss.com',
    install_requires=[], #['PyROOTUtils'],
    entry_points={
        'console_scripts': [
            'batchLikelihoodScan = BatchLikelihoodScan.scan:main',
            'batchLikelihoodPlot = BatchLikelihoodScan.plot:main',
        ]
    }
)
