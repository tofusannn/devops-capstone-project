# Tekton v1.18 / Docker Desktop (local capstone lab)

This workflow performs a **real** Git clone, Kaniko Dockerfile build/push to GHCR, then Kubernetes deployment and rollout verification. It intentionally does **not** mount the Docker daemon socket.

**Only use this on your own authorized local lab cluster.** The credentials below are written to a Kubernetes Secret. Use a dedicated, short-lived GitHub personal access token (classic) with the minimum required `write:packages` and `read:packages` scopes. Avoid reusing a broadly privileged GitHub CLI authentication token.

Prerequisites: Docker Desktop Kubernetes node Ready; existing `deployment/accounts` and `deployment/postgresql` Ready; Tekton controller/webhook Running; `tkn version` reports Pipeline v1.18 or compatible; Homebrew `tkn` installed; repo is public for clone.

## Step 1: Sync and install namespace-limited RBAC

```bash
cd ~/Downloads/devops-capstone-project
git pull --ff-only
kubectl config current-context
kubectl get deployment accounts postgresql
kubectl apply -f tekton/docker-desktop/rbac.yaml
kubectl auth can-i patch deployments --as=system:serviceaccount:default:capstone-tekton -n default
```

## Step 2: Create GHCR credentials safely

In GitHub Settings > Developer settings > Personal access tokens > Tokens (classic), create a **temporary** PAT for GHCR with `write:packages` and `read:packages`. Do not paste it in chat or commit it. Enter it interactively at the prompt below.

```bash
python3 - <<'PY' | kubectl apply -f -
import base64
import getpass
import json

username = "tofusannn"
token = getpass.getpass("Temporary GHCR PAT (hidden input): ").strip()
if not token:
    raise SystemExit("No token provided")
auth = base64.b64encode((username + ":" + token).encode()).decode()
docker_config = json.dumps({"auths": {"ghcr.io": {"auth": auth}}}).encode()
secret = {
    "apiVersion": "v1",
    "kind": "Secret",
    "metadata": {"name": "capstone-ghcr-auth", "namespace": "default"},
    "type": "kubernetes.io/dockerconfigjson",
    "data": {".dockerconfigjson": base64.b64encode(docker_config).decode()},
}
print(json.dumps(secret))
PY

# Do not print or decode the Secret.
kubectl get secret capstone-ghcr-auth
```

The package is uploaded to `ghcr.io/tofusannn/devops-capstone-project:tekton`. Newly created packages may be private; the Pipeline configures `imagePullSecrets` to allow the Kubernetes deployment to pull it. Revoke the temporary PAT and delete the Secret after finishing the lab.

## Step 3: Install the local Tasks and Pipeline, run it

```bash
kubectl apply -f tekton/docker-desktop/pipeline.yaml
kubectl get tasks.tekton.dev
kubectl get pipelines.tekton.dev capstone-cd-local

kubectl create -f tekton/docker-desktop/run.yaml
tkn pipelinerun list
```

The single PipelineRun should execute **clone -> build (Kaniko push GHCR) -> deploy (kubectl rollout)**. All workspaces use the Docker Desktop `hostpath` StorageClass via an auto-created RWO PVC, rather than the Coursera-only `skills-network-learner` class.

## Step 4: Genuine Task 32 log

Once the run has finished and shows `Succeeded`, capture the real log (do not fabricate it):

```bash
cd ~/Downloads/devops_capstone_step_by_step
tkn pipelinerun logs --last --all > evidence/pipelinerun.txt
tkn pipelinerun list
kubectl get deployment accounts
kubectl get pods -l app=accounts
```

If it is still running, inspect with `tkn pipelinerun logs --last --all -f`; capture the final output only when the run completes successfully.

In case of a failure:

```bash
tkn pipelinerun list
tkn pipelinerun describe --last
kubectl get pods -l tekton.dev/pipelineRun -o wide
```

### Important limitations

- GHCR must accept your PAT and allow image push. An expired token or unavailable image gives an authentication/image-pull failure; inspect the actual logs.
- This uses the latest available unmaintained Kaniko release for a self-contained course exercise. For production use a maintained builder, immutable digests, scoped credentials, registry policies, and a separate migration step.
- `capstone-deploy` expects the existing lab `deployment/accounts` created from `deploy/local/accounts.yaml`, with the accounts container as the first container and name `accounts`.
- The training DB from `deploy/local/postgresql.yaml` uses ephemeral storage.
