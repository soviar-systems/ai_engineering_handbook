---
jupytext:
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.18.1
kernelspec:
  name: python3
  display_name: Python 3 (ipykernel)
  language: python
---

# README: MystMD Website Deployment Instruction

+++

-----

Owner: Vadim Rudakov, lefthand67@gmail.com  
Version: 0.3.1  
Birth: 2025-12-17  
Modified: 2026-01-06

-----

+++

This guide outlines how to set up an automated documentation pipeline using
- **MyST Markdown**,
- **GitHub Actions**,
- **Podman**, and
- **Traefik**.

:::{important}
It is supposed that you have already:
- configured the server with rootless Podman and the traefik service (in container),
- created a Git repository with `.md` or `.ipynb` files,
- requested a domain name for your website.
:::

+++

## Files to work with

+++

The list of files used for configuration:

1. Repository:
    1. Git
        - `.gitignore`
        - `.github/workflows/deploy.yml`
        - SSH keys
    1. MyST: `myst.yml`
1. Server:
    1. Nginx: `nginx.conf`
    1. Podman: `play_nginx.yaml`
    1. Traefik: `/home/user/.local/share/containers/storage/volumes/traefik-data/_data/dynamic/myst-website.yml`

+++

## **1. Local Repo Configuration**

+++

### 1.1 Initialize MyST Locally

+++

Before the automation can work, your repository needs to be recognized as a MyST project.

1. Open your terminal in the root of your local repository.
2. Run `myst init`. Follow the prompts if there are any.
3. **Crucial:** Open your `.gitignore` file. If `myst.yml` was added there, **remove it**. You must track `myst.yml` in Git, while keeping the `_build/` folder ignored.
4. Commit and push the `myst.yml` to your repo.

+++

### 1.2 Edit 'myst.yml'

+++

This file is an entry point for rendering your repo to html. Here you can:
- set the project's and site's title,
- set the link to the github project,
- set logo and favicon,
- **exclude some repo's paths** for rendering.

+++

:::{tip} `myst.yml` example
:class: dropdown
:open: false
```yaml
# See docs at: https://mystmd.org/guide/frontmatter
version: 1
project:
  id: <any_id>
  title: <your_project_title>
  description: <your_website_description>
  # keywords: []
  # authors: []
  github: <link_to_github>
  exclude:
    - "RELEASE_NOTES.*"
    - "in_progress/*"
    - "pr/*"
    # jupytext pairs md to ipynb
    - "*/**/*.md"
site:
  template: book-theme
  title: <your_site_title>
  options:
    logo: /path/to/logo.png
    logo_text: <test_for_logo>
    favicon: /path/to/favicon.png
```
:::

+++

As you can see, we exclude all `.md` files from rendering because we use [*jupytext ipynb-md pairing*](/tools/jupyter_and_markdown/semantic_notebook_versioning_ai_ready_jupyter_docs.ipynb).

+++

## **2. Github Side Preparation**

+++

### 2.1 Configure GitHub Secrets

+++

To allow GitHub to deploy files to your server, you must store your credentials securely.

1. In your GitHub Repo, go to **Settings > Secrets and variables > Actions**.
2. Add the following **Repository secrets**:
    - `SERVER_IP`: Your server’s public IP or domain.
    - `SERVER_USER`: The SSH username (e.g., `root` or a deploy user).
    - `SERVER_PORT`: Your custom SSH port (e.g., `2222`).
    - `SSH_PRIVATE_KEY`: The private key whose public counterpart is in the server's `authorized_keys`.

+++

### 2.2 Enable the GitHub Action

+++

Your workflow file (`.github/workflows/deploy.yml`) automates the "Build and Sync" process.

1. Push your changes to the `main` branch.
2. Navigate to the **Actions** tab on GitHub to monitor the progress.
3. The workflow will:
    * Install `mystmd`.
    * Build the Markdown into static HTML.
    * Use `rsync` over the custom SSH port to move the HTML into `/home/server-user/website/html`.

+++

:::{tip} ### `.github/workflows/deploy.yml` example
:class: dropdown
:open: false
```yaml
name: build-and-deploy

on:
  push:
    # Universal trigger for team validation
    branches: ["**"]
    paths-ignore:
      - 'in_progress/*'
      - 'research/slm_from_scratch/old/*'
      - 'RELEASE_NOTES.md'
  # Allows you to trigger the build manually from the Actions tab
  workflow_dispatch:

jobs:
  validate-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          # Fetches all history so jupytext can compare timestamps if needed
          fetch-depth: 0

      # --- 1. INTEGRITY CHECK (Enforced on all branches) ---
      - name: Install uv (Python package manager)
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: Restore project environment using uv.lock
        run: uv sync --frozen

      - name: Verify Notebook Synchronization
        run: |
          # Only validate notebooks with a .md pair (your source of truth)
          for md in **/*.md; do
            if [[ -f "${md%.md}.ipynb" ]]; then
              echo "Testing: $md"
              uv run jupytext --to ipynb --test "$md"
            fi
          done

      # --- 2. DEPLOYMENT STEPS (Only runs on Main) ---
      - name: Setup Node.js
        if: github.ref == 'refs/heads/main'
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install MyST and Build
        if: github.ref == 'refs/heads/main'
        run: |
          npm install -g mystmd
          myst build --html

      - name: Deploy to Server via RSYNC
        if: github.ref == 'refs/heads/main'
        uses: easingthemes/ssh-deploy@main
        with:
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
          # -v (verbose) and -i (itemize-changes) provide good logs in
          # GitHub Actions
          ARGS: "-rlgoDzvc -i --delete"
          SOURCE: "_build/html/"
          REMOTE_HOST: ${{ secrets.SERVER_IP }}
          REMOTE_USER: ${{ secrets.SERVER_USER }}
          REMOTE_PORT: ${{ secrets.SERVER_SSH_PORT }}
          TARGET: "/home/containers/website/book/html"
```
:::

+++

## **3. Server Side Configuration**

+++

### 3.1 Prepare the Server Environment

+++

Your server needs `rsync` installed to receive the files, and the directory structure must match your manifests.

1. **Install rsync:**
    - Run `sudo apt install rsync` (or equivalent for your OS).

1. **Create Directories:**

    ```bash
    mkdir -p /home/server-user/website/html
    ```

1. **Set Permissions:** Ensure your SSH user owns the directory:
    ```bash
    ls -l /home/server-user/website
    ```

    Set correct permissions if needed using:
    ```bash
    chown -R server-user:server-user /home/server-user/website
    ```

1. **Place Config:**
    - Move your `nginx.conf` to `/home/server-user/website/nginx.conf`.

+++

:::{tip} ### `nginx.conf` example
:class: dropdown
:open: false
```
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Corrected location block to prevent redirection cycles
    location / {
        # 1. Try serving the requested path as a file.
        # 2. Try serving the requested path with an index.html appended (e.g., /docs/ -> /docs/index.html)
        # 3. If neither is found, return a 404 (this stops the infinite loop)
        try_files $uri $uri/ =404;
    }

    # Cache control for production assets
    location ~* \.(css|js|gif|jpe?g|png|svg|json)$ {
        expires 1y;
        log_not_found off;
        access_log off;
        add_header Cache-Control "public";
    }
}
```
:::

+++

### 3.2 Deploy the Podman Pod as a Systemd Service

+++

Instead of running the pod manually, we will use Podman’s native integration with **systemd**. This ensures your website starts automatically after a reboot and is managed as a background service.

See the K8S YAML manifest example for the given website here: [*play_nginx.yaml*](/helpers/website/configs/play_nginx.yaml)

+++

:::{tip} ### `play_nginx.yaml` example
:class: dropdown
:open: false
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myst-docs-pod
  labels:
    app: myst-docs
spec:
  volumes:
    # Volume for the static HTML files (built by MyST)
    - name: myst-html-storage
      hostPath:
        path: /home/<your_user>/website/html
        type: Directory
    # Volume for custom nginx.conf
    - name: nginx-config
      hostPath:
        path: /home/<your_user>/website/nginx.conf
        type: File
    - name: localtime
      hostPath:
        path: /etc/localtime
        type: File
  containers:
    - name: myst-nginx-container
      image: docker.io/library/nginx:1.29.4
      ports:
        - containerPort: 80
          hostPort: <your_port>
          name: http
      volumeMounts:
        # Mount the MyST build output to the Nginx web root
        - mountPath: /usr/share/nginx/html
          name: myst-html-storage
          readOnly: true
        # Overwrite the default Nginx config with your custom one
        - mountPath: /etc/nginx/conf.d/default.conf
          name: nginx-config
          readOnly: true
        - mountPath: /etc/localtime
          name: localtime
          readOnly: true
  restartPolicy: Always
```
:::

+++

#### Generate the Systemd Escape Path

+++

Systemd requires a specifically formatted "escaped" path to reference the Kubernetes manifest file. Generate this by running:

```bash
systemd-escape /home/server-user/website/play_nginx.yaml
```

Copy the output of this command (e.g., `home-server-user-website-play-nginx.yaml`).

+++

#### Configure the Environment Variable

+++

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

+++

#### Enable and Start the Service

+++

Now, you can manage your MyST website using standard systemd commands. This will launch the Nginx container and serve the files synchronized by GitHub.

```bash
# Reload systemd to recognize the changes
systemctl --user daemon-reload

# Enable the service to start on boot
systemctl --user enable $MYST_WEBSITE_SERVICE

# Start the service immediately
systemctl --user start $MYST_WEBSITE_SERVICE
```

+++

#### Verify the Deployment

+++

Check the status of your service to ensure the Nginx container is running correctly:

```bash
systemctl --user status $MYST_WEBSITE_SERVICE
```

+++

(traefik-configuration)=
### 3.3 Configure Traefik Routing

+++

Traefik acts as the entry point, handling SSL/TLS and routing traffic from your domain to the Podman container.

1. Add the **Router** and **Service** to your Traefik dynamic configuration.
    ```bash
    # example of the directory with Traefik dynamic files
    /home/user/.local/share/containers/storage/volumes/traefik-data/_data/dynamic/website_traefik.yml
    ```
2. Ensure the `loadBalancer` URL points to the `hostPort` defined in your pod manifest (e.g., `http://<your-website>:8080`).

+++

:::{tip} ### `website_traefik.yml` example
:class: dropdown
:open: false
```yaml
# myst-website on nginx for traefik
http:
  routers:
    myst_pod_router:
    rule: "Host(`your_website`)"
    entryPoints:
      - websecure
    service: myst_pod_service
    tls:
      certResolver: myresolver

  services:
    myst_pod_service:
      loadBalancer:
        servers:
          - url: "http://your_website:<port_number>"
```
:::

+++

## **Troubleshooting Checklist**

+++

* **404 Error:** Ensure Nginx is listening on port `80` inside the container and the Pod manifest maps `containerPort: 80` to your `hostPort`.
* **Permission Denied:** Check that the GitHub SSH user has write access to the target folder on the server.
* **No Site Config:** Ensure `myst.yml` is present in the root of your GitHub repository.
* **Traefik Issues:** Check the Traefik dashboard to ensure the service is "Healthy" and the URL matches the host's listener.

+++

## **Appendix A: Configuration Files**

+++

See attached files for `nginx.conf`, Traefik YAML, and the Kubernetes/Podman manifest in `helpers/website/configs/`.

```{code-cell} ipython3
ls configs
```

Other files are active repo files, so you should inspect them directly in the repo.

+++

## **Appendix B: Multi-Site Configuration (Single Pod)**

+++

This section describes how to host multiple MyST websites within a single Nginx instance and Podman Pod by using port-based routing. This approach is highly efficient as it shares a single container process across multiple repositories.

Each website's files can be maintained in different git repos, you will need to configure github actions for each one respectively, but all of these sites share the same config files on the server.

+++

### B.1 Recommended File Tree on the Server

+++

```bash
# server
$ tree --dirsfirst -L 2 ~/website/
/home/user/website/
├── site_a
│   └── html
├── site_b
│   └── html
├── nginx.conf
└── play_nginx.yaml

5 directories, 2 files
```

+++

### B.1 nginx.conf

+++

To serve multiple repositories, the Nginx configuration is updated with independent `server` blocks, each listening on a unique internal port. Each block points to a specific directory (`root`) where the respective site's HTML is mounted.

+++

:::{tip} ### `nginx.conf` multi-site example
:class: dropdown
:open: false
```yaml
# Website A (Primary Site)
server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/site_a; 
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location ~* \.(css|js|gif|jpe?g|png|svg|json)$ {
        expires 1y;
        log_not_found off;
        access_log off;
        add_header Cache-Control "public";
    }
}

# Website B (Secondary Site)
server {
    listen 81;
    server_name localhost;

    root /usr/share/nginx/site_b;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    location ~* \.(css|js|gif|jpe?g|png|svg|json)$ {
        expires 1y;
        log_not_found off;
        access_log off;
        add_header Cache-Control "public";
    }
}
```

Note that the `root` paths must be different so they don't serve the same files.
:::

+++

### B.2 play_nginx.yaml

+++

The Pod manifest is updated to define multiple `hostPath` volumes—one for each git repository's build output—and to expose unique `hostPort` values for external access.

+++

:::{tip} ### `play_nginx.yaml` multi-site example
:class: dropdown
:open: false
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: myst-multi-site-pod
  labels:
    app: myst-docs
spec:
  volumes:
    - name: nginx-config
      hostPath:
        path: /home/user/website/nginx.conf
        type: File
    - name: localtime
      hostPath:
        path: /etc/localtime
        type: File
    - name: site-a-storage
      hostPath:
        path: /home/user/website/site-a/html
        type: Directory
    - name: site-b-storage
      hostPath:
        path: /home/user/website/site-b/html
        type: Directory
  containers:
    - name: nginx-container
      image: docker.io/library/nginx:1.29.4
      ports:
        - containerPort: 80
          hostPort: 8080   # Port for Site A
          name: port-site-a
        - containerPort: 81
          hostPort: 8081   # Port for Site B
          name: port-site-b
      volumeMounts:
        - mountPath: /etc/nginx/conf.d/default.conf
          name: nginx-config
          readOnly: true
        - mountPath: /usr/share/nginx/site_a
          name: site-a-storage
          readOnly: true
        - mountPath: /usr/share/nginx/site_b
          name: site-b-storage
          readOnly: true
```
:::

+++

When using this specific multi-site configuration in a single Pod, you must pay attention to how the 
- **Host Paths**, 
- **Port Mappings**, and 
- **Volume Mounts**

align with your `nginx.conf`. 

Any mismatch between these three areas will result in "404 Not Found" or "Bad Gateway" errors.

1. **Host Path Accuracy**

    The `hostPath` must point to the exact location on your server where the MyST HTML files are stored.
    
    * **Permissions:** Ensure the user running the container has read permissions for these directories (e.g., `/home/user/website/site-a/html`).
    * **Directory Type:** The `type: Directory` ensures that the pod will only start if these folders already exist on your host machine.

2. **Port Mapping and Naming**

    This config uses port-based routing rather than domain-based routing.
    
    * **Unique Names:** Each port defined in the `ports` section must have a unique `name` (e.g., `port-site-a` and `port-site-b`).
    * **External Access:** You will access your sites using the `hostPort` values. In this example, Website A is at `http://<server-ip>:8080` and Website B is at `http://<server-ip>:8081`.
    * **Internal Alignment:** Your `nginx.conf` **must** contain two `server` blocks: one `listen 80;` and one `listen 81;` to match the `containerPort` values defined here.

3. **Volume Mount Alignment**

    The `mountPath` inside the container is what Nginx "sees."
    
    * **Root Directory:** In your `nginx.conf`, the `root` directive for Site A must be set to `/usr/share/nginx/site_a`, and Site B must be `/usr/share/nginx/site_b`.
    * **Config Overwrite:** The `nginx-config` volume mounts to `/etc/nginx/conf.d/default.conf`. This completely replaces the default Nginx welcome page configuration with your custom multi-site rules.

+++

### B.3 Traefik Dynamic File

+++

Remember to create an additional dynamic file for routing the new website through your Traefik instance. You can copy the existing file for the first site described in [***{name}***](#traefik-configuration), rename it, and change the:

- hostname
- port number

and all the occurences of the first website naming in router, services, etc. naming. No additional information for this file needed.

+++

:::{tip} ### `website_b_traefik.yml` example
:class: dropdown
:open: false
```yaml
# Traefik routing for the second MyST website (Website B)
http:
  routers:
    # Unique router name for the second site
    myst_site_b_router:
      rule: "Host(`second-website.com`)" # Your second domain
      entryPoints:
        - websecure
      service: myst_site_b_service
      tls:
        certResolver: myresolver

  services:
    # Unique service name mapping to the second hostPort
    myst_site_b_service:
      loadBalancer:
        servers:
          # Points to the hostPort defined for Site B (8081)
          - url: "http://<your-server-ip>:8081"
```
:::

+++

### B.4 Deployment Summary

+++

Restart the service:

```bash
systemctl --user restart $MYST_WEBSITE_SERVICE
```

and check your websites. Using this configuration, Nginx routes traffic based on the port number requested by the user:

* **Website A:** Accessible at `https://first-website`.
* **Website B:** Accessible at `https://second-website`.

This setup ensures that only one Nginx container is running on the server, significantly reducing memory and CPU overhead compared to running a separate Pod for every repository.
