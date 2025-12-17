# README: MystMD Website Deployment Instruction

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.1.0  
Birth: 2025-12-17  
Modified: 2025-12-18

-----

This guide outlines how to set up an automated documentation pipeline using **MyST Markdown**, **GitHub Actions**, **Podman**, and **Traefik**.

> It is supposed that you have already:
> - configured the server with rootless Podman and the traefik service (in container),
> - created a Git repository with .md or .ipynb files.

---

## Step 1: Initialize MyST Locally

Before the automation can work, your repository needs to be recognized as a MyST project.

1. Open your terminal in the root of your local repository.
2. Run `myst init`. Follow the prompts to set your project title and identify your main entry point (e.g., `index.md`).
3. **Crucial:** Open your `.gitignore` file. If `myst.yml` was added there, **remove it**. You must track `myst.yml` in Git, while keeping the `_build/` folder ignored.
4. Commit and push the `myst.yml` to your repo.

---

## Step 2: Configure GitHub Secrets

To allow GitHub to deploy files to your server, you must store your credentials securely.

1. In your GitHub Repo, go to **Settings > Secrets and variables > Actions**.
2. Add the following **Repository secrets**:
    - `SERVER_IP`: Your server’s public IP or domain.
    - `SERVER_USER`: The SSH username (e.g., `root` or a deploy user).
    - `SERVER_PORT`: Your custom SSH port (e.g., `2222`).
    - `SSH_PRIVATE_KEY`: The private key whose public counterpart is in the server's `authorized_keys`.

---

## Step 3: Prepare the Server Environment

Your server needs `rsync` installed to receive the files, and the directory structure must match your manifests.

1. **Install rsync:** Run `sudo apt install rsync` (or equivalent for your OS).
2. **Create Directories:**

```bash
mkdir -p /home/containers/website/html
```

3. **Set Permissions:** Ensure your SSH user owns the directory:
```bash
sudo chown -R $USER:$USER /home/containers/website
```

4. **Place Config:** Move your `nginx.conf` to `/home/containers/website/nginx.conf`.

---

## Step 4: Deploy the Podman Pod as a Systemd Service

Instead of running the pod manually, we will use Podman’s native integration with **systemd**. This ensures your website starts automatically after a reboot and is managed as a background service.

### 1. Generate the Systemd Escape Path

Systemd requires a specifically formatted "escaped" path to reference the Kubernetes manifest file. Generate this by running:

```bash
systemd-escape /home/containers/website/myst-pod.yaml

```

*Copy the output of this command (e.g., `home-containers-website-myst.pod.yaml`).*

### 2. Configure the Environment Variable

To make service management easier, we will store the service name in your `.bashrc`.

1. Open your bash configuration:
```bash
vi ~/.bashrc

```

2. Add the following line at the end of the file, replacing `<escaped_path>` with the result from the previous step:

```bash
export MYST_WEBSITE_SERVICE="podman-kube@<escaped_path>.service"
```


3. Apply the changes:

```bash
source ~/.bashrc
```

### 3. Enable and Start the Service

Now, you can manage your MyST website using standard systemd commands. This will launch the Nginx container and serve the files synchronized by GitHub.

```bash
# Reload systemd to recognize the changes
systemctl --user daemon-reload

# Enable the service to start on boot
systemctl --user enable $MYST_WEBSITE_SERVICE

# Start the service immediately
systemctl --user start $MYST_WEBSITE_SERVICE
```

### 4. Verify the Deployment

Check the status of your service to ensure the Nginx container is running correctly:

```bash
systemctl --user status $MYST_WEBSITE_SERVICE
```

---

## Step 5: Configure Traefik Routing

Traefik acts as the entry point, handling SSL/TLS and routing traffic from your domain to the Podman container.

1. Add the **Router** and **Service** to your Traefik dynamic configuration.
2. Ensure the `loadBalancer` URL points to the host's IP and the `hostPort` defined in your pod manifest (e.g., `http://127.0.0.1:8080`).

---

## Step 6: Enable the GitHub Action

Your workflow file (`.github/workflows/deploy.yml`) automates the "Build and Sync" process.

1. Push your changes to the `main` branch.
2. Navigate to the **Actions** tab on GitHub to monitor the progress.
3. The workflow will:
* Install `mystmd`.
* Build the Markdown into static HTML.
* Use `rsync` over the custom SSH port to move the HTML into `/home/containers/website/html`.

---

## Troubleshooting Checklist

* **404 Error:** Ensure Nginx is listening on port `80` inside the container and the Pod manifest maps `containerPort: 80` to your `hostPort`.
* **Permission Denied:** Check that the GitHub SSH user has write access to the target folder on the server.
* **No Site Config:** Ensure `myst.yml` is present in the root of your GitHub repository.
* **Traefik Issues:** Check the Traefik dashboard to ensure the service is "Healthy" and the URL matches the host's listener.

---

### Appendix: Configuration Files

*See attached files for `nginx.conf`, Traefik YAML, and the Kubernetes/Podman manifest.*
