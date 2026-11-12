#!/usr/bin/env python3
"""Safely configure GHCR credentials in the local Docker Desktop Kubernetes lab.

Run: python3 bin/setup-ghcr-secret.py
Never paste or commit the GitHub token; this script reads it without echo
and sends only the Kubernetes Secret object via kubectl stdin.
"""
import base64
import getpass
import json
import subprocess
import sys


SECRET_NAME = "capstone-ghcr-auth"
NAMESPACE = "default"
EXPECTED_CONTEXT = "docker-desktop"
USERNAME = "tofusannn"


def run_cmd(command, **kwargs):
    """Invoke command without a shell, avoiding secrets in process arguments."""
    return subprocess.run(command, text=True, capture_output=True, **kwargs)


def main():
    context = run_cmd(["kubectl", "config", "current-context"])
    if context.returncode or context.stdout.strip() != EXPECTED_CONTEXT:
        sys.exit(
            "ERROR: Kubernetes context must be 'docker-desktop'. "
            "Use: kubectl config use-context docker-desktop"
        )

    print("Kubernetes context: docker-desktop")
    print("Target: default/" + SECRET_NAME)
    print("Use a short-lived GitHub personal access token (classic) with write:packages.")
    print("The token will not be displayed, saved in a file, or committed.")
    token = getpass.getpass("Paste GHCR PAT (hidden input), then Enter: ").strip()
    if not token:
        sys.exit("ERROR: Empty token. Secret not created.")

    auth = base64.b64encode((USERNAME + ":" + token).encode("utf-8")).decode("ascii")
    docker_config = json.dumps({"auths": {"ghcr.io": {"auth": auth}}}, separators=(",", ":"))
    secret = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": SECRET_NAME, "namespace": NAMESPACE},
        "type": "kubernetes.io/dockerconfigjson",
        "data": {
            ".dockerconfigjson": base64.b64encode(
                docker_config.encode("utf-8")
            ).decode("ascii")
        },
    }
    del token, auth, docker_config

    try:
        apply_result = run_cmd(
            ["kubectl", "apply", "-n", NAMESPACE, "-f", "-"],
            input=json.dumps(secret),
        )
    except FileNotFoundError:
        sys.exit("ERROR: kubectl not installed.")
    finally:
        del secret

    if apply_result.returncode:
        print("ERROR: kubectl could not create Secret.", file=sys.stderr)
        # Avoid echoing untrusted server text because it could contain credential material.
        sys.exit(1)

    verify = run_cmd(
        [
            "kubectl", "-n", NAMESPACE, "get", "secret", SECRET_NAME,
            "-o", "jsonpath={.type}",
        ]
    )
    if verify.returncode or verify.stdout.strip() != "kubernetes.io/dockerconfigjson":
        sys.exit("ERROR: Secret type verification failed.")

    print("OK: default/" + SECRET_NAME + " exists.")
    print("Type: kubernetes.io/dockerconfigjson")
    print("The registry has NOT been tested yet; a real PipelineRun will verify push and pull.")
    print("Revoke the temporary PAT and remove the secret after this lab.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCancelled; no new Secret was created.")
        sys.exit(130)
