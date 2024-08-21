#!/bin/bash

function download {
  if hash curl >/dev/null 2>&1; then
    curl $1 -o $2 -fsSL --compressed ${CURL_OPTS:-}
  elif hash wget >/dev/null 2>&1; then
    wget ${WGET_OPTS:-} -qO $2 $1
  else
    echo "Neither curl nor wget was found" >&2
    exit 1
  fi
}

function get_enviroment_name {
  echo $(sed -n -e 's/^.*name:\s*//p' $1)
}


# Variables
PACKAGE_NAME="spyder-remote-services"
VERSION=${1:-latest}

SERVER_ENV="spyder-remote"
KERNEL_ENV="spyder-kernel"

MICROMAMBA_VERSION="latest"
BIN_FOLDER="${HOME}/.local/bin"
PREFIX_LOCATION="${HOME}/micromamba"

PYTHON_VERSION="3.12"


# Detecting platform
case "$(uname)" in
  Linux)
    PLATFORM="linux" ;;
  Darwin)
    PLATFORM="osx" ;;
  *NT*)
    PLATFORM="win" ;;
esac

ARCH="$(uname -m)"
case "$ARCH" in
  aarch64|ppc64le|arm64)
      ;;  # pass
  *)
    ARCH="64" ;;
esac

case "$PLATFORM-$ARCH" in
  linux-aarch64|linux-ppc64le|linux-64|osx-arm64|osx-64|win-64)
      ;;  # pass
  *)
    echo "Failed to detect your OS" >&2
    exit 1
    ;;
esac


# Install micromamba
RELEASE_URL="https://github.com/mamba-org/micromamba-releases/releases/${MICROMAMBA_VERSION}/download/micromamba-${PLATFORM}-${ARCH}"

mkdir -p "${BIN_FOLDER}"
download "${RELEASE_URL}" "${BIN_FOLDER}/micromamba"
chmod +x "${BIN_FOLDER}/micromamba"

eval "$("${BIN_FOLDER}/micromamba" shell hook --shell bash)"


# Install spyder-remote-services
micromamba create -y -n $SERVER_ENV -c conda-forge "python=${PYTHON_VERSION}" pip

if [ $VERSION == "latest" ]; then
  micromamba run -n $SERVER_ENV pip install ${PACKAGE_NAME}
elif [[ $VERSION != *"=="* ]] && [[ $VERSION != *">="* ]] && [[ $VERSION != *"<="* ]] && [[ $VERSION != *">"* ]] && [[ $VERSION != *"<"* ]]; then
  micromamba run -n $SERVER_ENV pip install ${PACKAGE_NAME}==$VERSION
else
  micromamba run -n $SERVER_ENV pip install ${PACKAGE_NAME}${VERSION}
fi


# Install spyder-kernel
micromamba create -y -n $KERNEL_ENV -c conda-forge -c conda-forge/label/spyder_kernels_rc "python=${PYTHON_VERSION}" spyder-kernels

micromamba run -n $KERNEL_ENV python -m ipykernel install --user --name $KERNEL_ENV
