# Superset Development with GitHub Codespaces

This devcontainer is configured to use a **pre-built image** (`ghcr.io/apache/superset:devcontainer-base`) so Codespaces does not build a container image as part of workspace creation.

If you need to rebuild/push the base image for caching purposes, use `.devcontainer/build-and-push-image.sh`.

For complete documentation on using GitHub Codespaces with Apache Superset, please see:

**[Setting up a Development Environment - GitHub Codespaces](https://superset.apache.org/docs/contributing/development#github-codespaces-cloud-development)**
