# -*- coding: utf-8 -*-

from distutils.core import setup

def _main():
    setup(name="klupu",
          version="0.1",
          description="scrape meeting minutes of governing bodies of city of Jyväskylä",
          author="Tuomas Jorma Juhani Räsänen",
          author_email="tuomasjjrasanen@tjjr.fi",
          url="http://tjjr.fi/sw/klupu/",
          scripts=["bin/klupu", "bin/klupu-clean", "bin/klupu-draw"],
          packages=["klupu"],
          package_dir={"klupu": "src"},
          license="GPLv3+",
          platforms=["Linux"],
          requires=["bs4", "matplotlib"],
          classifiers=[
            "Development Status :: 1 - Planning",
            "Environment :: Console",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: GNU General Public License (GPL)",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.2",
            "Topic :: Scientific/Engineering :: Information Analysis",
            ],
          long_description="""
Klupu is a report mining tool designed for extracting interesting data from
meeting minutes of governing bodies of city of Jyväskylä. Klupu is a
Finnish word for flail which is a tool used for separating grains from
husks. Grains of knowledge, in this case.
""",
          )

if __name__ == "__main__":
    _main()
