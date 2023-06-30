from __future__ import print_function

import glob
import os
import subprocess

from setuptools import setup
from distutils.command.build_py import build_py
from distutils.command.clean import clean
from distutils.command.sdist import sdist
from distutils.spawn import find_executable
from distutils.dir_util import remove_tree


# find protobuf compiler
if 'PROTOC' in os.environ and os.path.exists(os.environ['PROTOC']):
    protoc = os.environ['PROTOC']
else:
    protoc = find_executable("protoc")


protobuf_dir = 'protobuf'
protobuf_package_dir = 'asmp'
init_file_tpl = "from .{subpackage} import {module}\n"


def compile_proto_dir(proto_dir, output_dir, start_init_files_at=0):
    assert protoc is not None, "protoc binary not specified or found"
    # ensure output_dir (asmp/asmp) exists
    os.makedirs(output_dir + "/asmp", exist_ok=True)
    for dirpath, subdirs, files in os.walk(proto_dir):
        proto_files = [f for f in files if f.endswith('.proto')]
        if proto_files:
            protoc_call = [protoc,
                           '--proto_path=' + proto_dir,
                           '--python_out=' + output_dir]
            for proto_file in proto_files:
                protoc_call.append(os.path.join(dirpath, proto_file))
            print(subprocess.list2cmdline(protoc_call))
            subprocess.check_call(protoc_call)
            if (
                    len(
                        os.path.relpath(
                            dirpath,
                            start=proto_dir
                        ).split(os.path.sep)
                    )
                    > start_init_files_at
            ):
                init_name = os.path.join(
                    output_dir,
                    os.path.relpath(dirpath, start=proto_dir),
                    '__init__.py'
                )
                print('Creating INIT file:', init_name, 'subdirs:', subdirs)
                with open(init_name, 'w') as f:
                    for subpackage in subdirs:
                        for protofile in glob.glob(
                                os.path.join(
                                    dirpath,
                                    subpackage,
                                    '*.proto'
                                )):
                            f.write(
                                init_file_tpl.format(
                                    subpackage=subpackage,
                                    module=os.path.basename(
                                        protofile.replace('.proto', '_pb2'))
                                )
                            )


# protobuf helper classes
class ProtocBuildPy(build_py):
    def run(self):
        # first generate python files from .proto files
        compile_proto_dir(
            proto_dir=protobuf_dir,
            output_dir=protobuf_package_dir,
        )
        # then continue with the usual build
        build_py.run(self)


class ProtocClean(clean):
    def run(self):
        # first delete generated python files
        remove_tree(protobuf_package_dir)
        remove_tree("build")
        remove_tree("dist")
        # then continue with the usual clean
        clean.run(self)


class ProtoSdist(sdist):
    def run(self):
        print("Hello from sdist")
        # first generate python files from .proto files
        compile_proto_dir(protobuf_dir, protobuf_package_dir)
        # then continue with the usual sdist
        sdist.run(self)


setup(name='evi-asm-protocol',
      version='0.18.0',
      description='protocol bridge to ASM for the Veins ego vehicle interface (evi)',
      maintainer='Dominik S. Buse',
      maintainer_email='buse@ccs-labs.org',
      url='http://www.hy-nets.org',
      packages=['asmp', 'asmp.asmp'],
      cmdclass={
          'clean': ProtocClean,
          'build_py': ProtocBuildPy,
          'sdist': ProtoSdist,
      })
