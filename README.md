![staging](https://github.com/aliassisi/aliassisi.it/workflows/publish%20staging/badge.svg?branch=master)
![production](https://github.com/aliassisi/aliassisi.it/workflows/publish%20production/badge.svg?branch=prd)

# ALIA Website

This repo contains the source code, theme and contents to build the static website at https://aliassisi.it
using [Hugo](https://gohugo.io/).

## Requirements

Before start working on the project, please install [brew](https://brew.sh/), available for OSX and Linux.

Once `brew` is available on your system, clone this git repository and run from the root:

```sh
$ brew install
```

This will install [asdf](https://asdf-vm.com/), a command line tool we'll be using to keep track of the
right [Hugo](https://gohugo.io/) versions.

asdf requires a one-time setup to be able to install Hugo:

```sh
$ asdf plugin-add hugo https://github.com/beardix/asdf-hugo.git
```

Once installed the Hugo plugin for asdf, you can install Hugo by simply run:

```sh
$ adsf install
```

## Local development

To run the website locally and see the changes in real-time, start Hugo server from the root of the
repo:

```sh
$ hugo server
```

The website will be available pointing a web browser at http://localhost:1313/.

## Deployment

The build and deployment phases are completely automated. Every push to the `master` branch will build
and deploy the website to the staging area available at https://beta.aliassisi.it. To deploy the website
to the production area, a commit needs to be pushed to the `prd` branch, ideally by opening a Pull Request
to merge `master` into `prd`.
