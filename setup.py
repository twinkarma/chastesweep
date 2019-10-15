import setuptools
with open("README.md", "r") as fh:
    long_description = fh.read()
setuptools.setup(
     name='chastesweep',
     version='0.1',
     scripts=['chastesweep_genmain'],
     author="Twin Karmakharm",
     author_email="t.karmakharm@sheffield.ac.uk",
     description="Parameter Sweeper for Chaste",
     package_data={'chastesweep.templates': ['templates/*']},
     long_description=long_description,
   long_description_content_type="text/markdown",
     url="https://github.com/twinkarma/chastesweep",
     packages=setuptools.find_packages(),
     classifiers=[
         "Programming Language :: Python :: 2",
         "License :: OSI Approved :: MIT License",
         "Operating System :: OS Independent",
     ],
 )