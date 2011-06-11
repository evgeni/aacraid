from setuptools import setup

setup(
    name = "aacraid",
    version = "0.1",
    description = "monitor Adaptec RAID controllers",
    author = "Evgeni Golov",
    author_email = "evgeni@golov.de",
    url = "http://www.die-welt.net",
    license = "BSD",
    py_modules = ['aacraid'],
    scripts = ['aacraid-status', 'aacraidd'],
    zip_safe = False,
    install_requires=['python-daemon'],
    data_files = [('/etc/aacraidd', ['aacraidd.conf'])]
)
