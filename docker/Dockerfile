#! Defined outside of the stages, so it can be accessed from all stages.
ARG PYTHON_VERSION_MAJOR="3"
ARG PYTHON_VERSION_MINOR="10"
ARG PYTHON_VERSION_PATCH="8"

###########################################
# Stage 1: Build Blender as a Python module
###########################################
FROM nvidia/cudagl:11.4.2-devel-ubuntu20.04 as bpy-builder

ARG BLENDER_VERSION="v3.3.2"
ARG BLENDER_LIBRARY_VERSION="3.3"

ARG PYTHON_VERSION_MAJOR
ARG PYTHON_VERSION_MINOR
ARG PYTHON_VERSION_PATCH

ARG PYTHON_VERSION=${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}

ARG DEBIAN_FRONTEND=noninteractive

# Update and upgrade packages
RUN apt-get update && apt-get upgrade -y

# Basic requirements (see https://wiki.blender.org/wiki/Building_Blender/Linux/Ubuntu#Quick_Setup)
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    subversion \
    cmake \
    libx11-dev \
    libxxf86vm-dev \
    libxcursor-dev \
    libxi-dev \
    libxrandr-dev \
    libxinerama-dev \
    libglew-dev

# Python requirements
RUN apt-get update && apt-get install -y \
    software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update && apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python3-distutils \
    python3-pip \
    python3-apt

# Clone a shallow copy of the blender sources
RUN mkdir -p /opt/blender-git/
WORKDIR /opt/blender-git/
RUN git clone https://github.com/blender/blender.git -c advice.detachedHead=false --depth 1 --branch ${BLENDER_VERSION}
WORKDIR /opt/blender-git/blender
RUN git checkout -b my-branch

## Clone submodules
RUN git submodule update --init --recursive

# Download a copy of the blender libraries
RUN mkdir -p /opt/blender-git/lib
WORKDIR /opt/blender-git/lib
RUN svn export https://svn.blender.org/svnroot/bf-blender/tags/blender-${BLENDER_LIBRARY_VERSION}-release/lib/linux_centos7_x86_64/

# Compile blender
## Replace build config
COPY bpy_module.cmake /opt/blender-git/blender/build_files/cmake/config

## Trigger compilation
WORKDIR /opt/blender-git/blender
RUN make update
RUN make bpy


###########################################
# Stage 2: Slim image for deployment
###########################################

FROM nvidia/cudagl:11.4.2-base-ubuntu20.04

ARG USER_NAME=user

ARG PYTHON_VERSION_MAJOR
ARG PYTHON_VERSION_MINOR
ARG PYTHON_VERSION_PATCH

ARG PYTHON_VERSION_XY=${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}
ARG PYTHON_VERSION_XYZ=${PYTHON_VERSION_XY}.${PYTHON_VERSION_PATCH}

ARG DEBIAN_FRONTEND=noninteractive

ENV LANGUAGE C.UTF-8
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# Update and upgrade packages
RUN apt-get update && apt-get upgrade -y

# Install Python
## Set up dependencies needed for pyenv
RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    ca-certificates \
    curl \
    llvm \
    libncurses5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    liblzma-dev \
    mecab-ipadic-utf8 \
    git

## Set up environment variabless for pyenv
ENV PYENV_ROOT /usr/local/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH

## Install pyenv
RUN set -ex \
    && curl https://pyenv.run | bash \
    && pyenv update \
    && pyenv install $PYTHON_VERSION_XYZ \
    && pyenv global $PYTHON_VERSION_XYZ \
    && pyenv rehash

# Copy blender python module
COPY --from=bpy-builder /opt/blender-git/lib/linux_centos7_x86_64/python/lib/python${PYTHON_VERSION_XY}/site-packages \
    /opt/bpy/lib/python${PYTHON_VERSION_XY}/site-packages
ENV PYTHONPATH="${PYTHONPATH}:/opt/bpy/lib/python${PYTHON_VERSION_XY}/site-packages"

# Install blender dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    libgomp1 \
    libxrender1

# Setup a virtual X server to enable Eevee and Workbench support
RUN apt-get update && apt-get install --no-install-recommends -y xvfb && \
    mkdir -p /tmp/.X11-unix && \
    chmod 1777 /tmp/.X11-unix
ENV DISPLAY=:1.0
ENV NVIDIA_DRIVER_CAPABILITIES=all

# Install other dependencies
## apt
RUN apt-get update && apt-get install --no-install-recommends -y \
    git \
    liboctomap-dev \
    libfcl-dev

## pip
RUN pip install pipenv==2022.1.8
ARG DEV
COPY Pipfile* ./
RUN pipenv install --system ${DEV}

RUN pyenv rehash

# Add a non-root user
RUN useradd -ms /bin/bash ${USER_NAME}
USER ${USER_NAME}

# Start in app folder.
RUN mkdir /home/${USER_NAME}/app
WORKDIR /home/${USER_NAME}/app

# Add scripts to perform actions on container start.
ADD --chown=${USER_NAME}:${USER_NAME} entrypoint.sh /home/${USER_NAME}
ENTRYPOINT /home/user/entrypoint.sh && /bin/bash
