# Capstone evidence capture

These commands must be run in a real lab environment. Do **not** submit
template output, staged sample results, or screenshots unrelated to your board.

## REST evidence (Tasks 13–17)

Start PostgreSQL and the Flask account service, then run:

```bash
BASE_URL=http://localhost:8080 bash bin/capture-rest-evidence.sh
```

The script saves real HTTP responses in `evidence/rest-*-done`. Review the
HTTP status codes and JSON content before pasting into the grader.

## CI and security (Tasks 19, 23)

On GitHub, open Actions > CI Build and use the completed successful job's
step logs as `ci-workflow-done`. For security, after installing the
dependencies in the Lab, run:

```bash
nosetests -v --with-coverage --cover-package=service |& tee security-headers-done
coverage report -m --fail-under=95
```

## Docker and Kubernetes (Tasks 26, 30–31)

The deployment assumes a PostgreSQL database reachable at service hostname
`postgresql`. Configure a real database and image before rollout.

```bash
docker build -t accounts:1.0 .
docker images | tee kube-images
kubectl apply -f deploy/deployment.yaml -f deploy/service.yaml
# Push and set an image accessible inside your Kubernetes cluster.
kubectl set image deployment/accounts accounts=YOUR_REGISTRY/accounts:1.0
kubectl rollout status deployment/accounts
kubectl get deployments,pods,replicasets,services -o wide | tee kube-deploy-accounts
kubectl port-forward service/accounts 8080:8080
curl -s http://localhost:8080/ | tee kube-app-output
```

In `kube-app-output`, retain the JSON that **actually appeared** in your browser
or terminal; it should not be simulated or manually fabricated.

## Tekton (Task 32)

The CD Pipeline expects Tekton `git-clone`, `buildah` ClusterTask, registry
push access, PVC `pipelinerun-pvc`, and Kubernetes deployment RBAC. Adapt the
image registry and cluster-specific permissions to the supplied lab.

```bash
kubectl apply -f tekton/tasks.yaml
kubectl apply -f tekton/pvc.yaml
kubectl apply -f tekton/pipeline.yaml
# Set the correct image and repository before starting a PipelineRun.
kubectl create -f tekton/pipelinerun.yaml
tkn pipelinerun list
tkn pipelinerun logs PIPELINERUN_NAME --all | tee pipelinerun.txt
```

For screenshot tasks, navigate the **actual** GitHub Project board and move
each story through its required status before recording the named images.
The GitHub issue's closed state is not the same as the Projects board's Done
column. See the original assignment for exact file names.
