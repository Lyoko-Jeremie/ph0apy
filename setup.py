import setuptools

setuptools.setup(
  name = "ph0apy",
  version = "0.0.1",
  description = "A polyfill version FH0Apy for run in pyodide package",
  # https://stackoverflow.com/questions/51286928/what-is-where-argument-for-in-setuptools-find-packages
  # DO NOT pack mock (like js) into output
  packages = setuptools.find_packages(where = 'src'),
  # special the root
  package_dir = {
    '': 'src',
  },
  classifiers = [
  ],
  author = 'Jeremie',
  author_email = 'lucheng989898@protonmail.com',
  python_requires = '>=3.6',
)

# pip install mypy
# mypy src/ph0apy/fh0a.py
# stubgen src/ph0apy/fh0a.py

# pip install wheel
# python setup.py bdist_wheel
