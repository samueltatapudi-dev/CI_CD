# Kubernetes Deployment

This directory contains Kubernetes manifests to deploy the Dockerized app and select which Flask variant to run via the `APP_VERSION` environment variable.

## Image

The manifests reference `ghcr.io/samueltatapudi-dev/ci_cd:latest`.

- If using a public cluster, ensure the image exists in GHCR (see the optional GitHub Action below).
- For local clusters (minikube, Docker Desktop), you can build locally and change the `image:` to `fitness-app:latest`, then:
  - `docker build -t fitness-app:latest ..`
  - `kubectl apply -k .`

## Deploy

Apply all resources (Deployment + Service):

```
kubectl apply -k k8s
```

Check status:

```
kubectl get deploy,svc
```

## Select Version

Update the running version by setting `APP_VERSION` on the Deployment:

```
kubectl set env deployment/fitness-app APP_VERSION=ACEest_Fitness-V1.2.3
```

Available values (folder names under `flask_apps/`):

- ACEest_Fitness
- ACEest_Fitness-V1.1
- ACEest_Fitness-V1.2
- ACEest_Fitness-V1.2.1
- ACEest_Fitness-V1.2.2
- ACEest_Fitness-V1.2.3

## Ingress (optional)

An example `Ingress` is provided (`ingress.yaml`) for an NGINX Ingress controller. Enable it by uncommenting in `k8s/kustomization.yaml` and set your desired host. Then map the host in `/etc/hosts` to your ingress controller IP.

