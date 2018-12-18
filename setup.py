from setuptools import setup, find_packages

setup(author="CCG, Murdoch University",
      author_email="info@ccg.murdoch.edu.au",
      description="Upload SRA data to the NCBI",
      license="GPL3",
      keywords="",
      url="https://github.com/muccg/bpa-submission-generator",
      name="bpa_ncbi_upload",
      version="0.2.1",
      packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
      entry_points={
          'console_scripts': [
              'bpa-ncbi-upload=bpa_ncbi_upload.cli:main',
          ],
      })
