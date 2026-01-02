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
Version: 0.2.0
Birth: 2025-12-17
Modified: 2026-01-03

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

## Step 1: Initialize MyST Locally

+++

Before the automation can work, your repository needs to be recognized as a MyST project.

1. Open your terminal in the root of your local repository.
2. Run `myst init`. Follow the prompts if there are any.
3. **Crucial:** Open your `.gitignore` file. If `myst.yml` was added there, **remove it**. You must track `myst.yml` in Git, while keeping the `_build/` folder ignored.
4. Commit and push the `myst.yml` to your repo.

+++

## Step 2: Configure GitHub Secrets

+++

To allow GitHub to deploy files to your server, you must store your credentials securely.

1. In your GitHub Repo, go to **Settings > Secrets and variables > Actions**.
2. Add the following **Repository secrets**:
    - `SERVER_IP`: Your server’s public IP or domain.
    - `SERVER_USER`: The SSH username (e.g., `root` or a deploy user).
    - `SERVER_PORT`: Your custom SSH port (e.g., `2222`).
    - `SSH_PRIVATE_KEY`: The private key whose public counterpart is in the server's `authorized_keys`.

+++

## Step 3: Prepare the Server Environment

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
    sudo chown -R $USER:$USER /home/server-user/website
    ```

1. **Place Config:**
    - Move your `nginx.conf` to `/home/server-user/website/nginx.conf`.

+++

## Step 4: Deploy the Podman Pod as a Systemd Service

+++

Instead of running the pod manually, we will use Podman’s native integration with **systemd**. This ensures your website starts automatically after a reboot and is managed as a background service.

See the K8S YAML manifest example for the given website here: [*play_nginx.yaml*](/helpers/website/play_nginx.yaml)

+++

### 4.1 Generate the Systemd Escape Path

+++

Systemd requires a specifically formatted "escaped" path to reference the Kubernetes manifest file. Generate this by running:

```bash
systemd-escape /home/server-user/website/play_nging.yaml
```

*Copy the output of this command (e.g., `home-server-user-website-play-nginx.yaml`).*

+++

### 4.2 Configure the Environment Variable

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

### 4.3 Enable and Start the Service

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

### 4.4 Verify the Deployment

+++

Check the status of your service to ensure the Nginx container is running correctly:

```bash
systemctl --user status $MYST_WEBSITE_SERVICE
```

+++

(traefik-configuration)=
## Step 5: Configure Traefik Routing

+++

Traefik acts as the entry point, handling SSL/TLS and routing traffic from your domain to the Podman container.

1. Add the **Router** and **Service** to your Traefik dynamic configuration.
    ```bash
    # example of the directory with Traefik dynamic files
    /home/user/.local/share/containers/storage/volumes/traefik-data/_data/dynamic/website_traefik.yml
    ```
2. Ensure the `loadBalancer` URL points to the `hostPort` defined in your pod manifest (e.g., `http://<your-website>:8080`).

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

+++

## Step 6: Enable the GitHub Action

+++

Your workflow file (`.github/workflows/deploy.yml`) automates the "Build and Sync" process.

1. Push your changes to the `main` branch.
2. Navigate to the **Actions** tab on GitHub to monitor the progress.
3. The workflow will:
* Install `mystmd`.
* Build the Markdown into static HTML.
* Use `rsync` over the custom SSH port to move the HTML into `/home/server-user/website/html`.

+++

## Troubleshooting Checklist

+++

* **404 Error:** Ensure Nginx is listening on port `80` inside the container and the Pod manifest maps `containerPort: 80` to your `hostPort`.
* **Permission Denied:** Check that the GitHub SSH user has write access to the target folder on the server.
* **No Site Config:** Ensure `myst.yml` is present in the root of your GitHub repository.
* **Traefik Issues:** Check the Traefik dashboard to ensure the service is "Healthy" and the URL matches the host's listener.

+++

## Appendix A: Configuration Files

+++

See attached files for `nginx.conf`, Traefik YAML, and the Kubernetes/Podman manifest in `configs`.

Other files are active repo files, so you should inspect them directly in the repo.

+++

## Appendix B: Multi-Site Configuration (Single Pod)

+++

This section describes how to host multiple MyST websites within a single Nginx instance and Podman Pod by using port-based routing. This approach is highly efficient as it shares a single container process across multiple repositories.

Each website's files can be maintained in different git repos, you will need to configure github actions for each one respectively, but all of these sites share the same config files on the server.

+++

### B.1 Recommended File Tree on Server

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

```nginx
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

+++

### B.2 play_nginx.yaml

+++

The Pod manifest is updated to define multiple `hostPath` volumes—one for each git repository's build output—and to expose unique `hostPort` values for external access.

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
