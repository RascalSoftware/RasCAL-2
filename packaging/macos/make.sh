#!/bin/bash

RASCAL_PATH="../bundle/rascal.app"
VER_NAME=$1
ARCH_NAME=$2
DEV_TEAM_ID=$3
API_CONNECT_ISSUER=$4
API_CONNECT_KEY_ID=$5
VER="main"

if [[ ${VER_NAME:0:1} == 'v' ]]; then
    VER=${VER:1}
fi

if [[ ${VER} == 'main' ]]; then
    NAME="RasCAL-2-macos-${ARCH_NAME}.pkg"
else
    NAME="RasCAL-2-${VER}-macos-${ARCH_NAME}.pkg"
fi

# Sign code
codesign -v --deep --force --timestamp --options=runtime --entitlements ./entitlements.plist --sign ${DEV_TEAM_ID} ${RASCAL_PATH}/Contents/Resources/*.dylib
codesign -v --deep --force --timestamp --options=runtime --entitlements ./entitlements.plist --sign ${DEV_TEAM_ID} ${RASCAL_PATH}

# Build Pkg
sed -e "s/@VERSION_NAME@/${VER_NAME}/g" -e "s/@VERSION@/${VER}/g" distribution.xml.in > distribution.xml
pkgbuild --root ${RASCAL_PATH} --identifier com.rascal2.rascal.pkg --version ${VER} --install-location "/Applications/rascal.app" rascal.pkg
productbuild --sign ${DEV_TEAM_ID} --timestamp --distribution distribution.xml --resources . ${NAME}

# Notarise and staple
xcrun notarytool submit --issuer ${API_CONNECT_ISSUER} --key-id ${API_CONNECT_KEY_ID} --key ./auth_key.p8 --wait ${NAME}
xcrun stapler staple ${NAME}
