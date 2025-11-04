#!/bin/bash

RASCAL_PATH="../bundle/rascal.app"
VER_NAME=$1
ARCH_NAME=$2
VER=$VER_NAME

if [[ ${VER_NAME:0:1} == 'v' ]]; then
    VER=${VER:1}
fi

# Build Pkg
sed -e "s/@VERSION_NAME@/${VER_NAME}/g" -e "s/@VERSION@/${VER}/g" distribution.xml.in > distribution.xml
pkgbuild --root ${RASCAL_PATH} --identifier com.rascal2.rascal.pkg --version ${VER} --install-location "/Applications/rascal.app" rascal.pkg
productbuild --distribution distribution.xml --resources . "rascal2-${VER}-${ARCH_NAME}.pkg"
