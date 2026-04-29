# Lab 05 - Ansible Fundamentals

**Ansible Version:** 2.16+  
**Target VM:** Ubuntu 24.04 LTS (Yandex Cloud)

---

## 1. Architecture Overview

### Ansible Setup

This lab implements Infrastructure-as-Code automation using Ansible with a professional role-based architecture. The system follows Ansible best practices for code organization, reusability, and maintainability.

**Key Components:**
- **Control Node:** Local machine running Ansible
- **Managed Node:** Lab 4 VM (created with Terraform)
- **Inventory:** Static inventory with hosts.ini
- **Roles:** Three specialized roles for provisioning and deployment
- **Vault:** Ansible Vault for secure credential management

### Role-Based Architecture

```
ansible/
├── inventory/
│   └── hosts.ini                    # Static inventory
├── roles/
│   ├── common/                      # System provisioning
│   │   ├── tasks/main.yml
│   │   └── defaults/main.yml
│   ├── docker/                      # Docker installation
│   │   ├── tasks/main.yml
│   │   ├── handlers/main.yml
│   │   └── defaults/main.yml
│   └── app_deploy/                  # Application deployment
│       ├── tasks/main.yml
│       ├── handlers/main.yml
│       └── defaults/main.yml
├── playbooks/
│   ├── provision.yml               # System provisioning playbook
│   └── deploy.yml                  # Application deployment playbook
├── group_vars/
│   └── all.yml                     # Encrypted credentials (Vault)
├── ansible.cfg                     # Configuration
└── docs/
    ├── screenshots/                # Screenshots of terminal output
    └── LAB05.md                    # This documentation

```

### Why Roles Instead of Monolithic Playbooks?

**Benefits of Role-Based Structure:**

1. **Reusability:** Each role can be used independently across projects
2. **Maintainability:** Changes to one role don't affect others
3. **Clarity:** Clear separation of concerns
4. **Sharing:** Roles can be shared via Ansible Galaxy
5. **Testing:** Roles can be tested independently
6. **Modularity:** Mix and match roles as needed

---

## 2. Roles Documentation

### Role 1: Common Role

**Purpose:** System-level provisioning and updates

**Location:** `roles/common/`

**Responsibilities:**
- Update APT package cache
- Install essential system packages (python3-pip, curl, git, vim, htop, wget, net-tools, jq)

**Variables (defaults/main.yml):**
```yaml
common_packages:
  - python3-pip
  - curl
  - git
  - vim
  - htop
  - wget
  - net-tools
  - jq
```

**Tasks:**
- Update apt cache with 1 hour validity
- Install all packages from `common_packages` list

**Handlers:** None
**Idempotency:**  Fully idempotent
- APT cache update is skipped if recent (cache_valid_time: 3600)
- Packages are installed to `state: present` (idempotent)

---

### Role 2: Docker Role

**Purpose:** Docker installation and configuration

**Location:** `roles/docker/`

**Responsibilities:**
- Add Docker's GPG key
- Add Docker official repository
- Install Docker packages (docker-ce, docker-ce-cli, containerd.io)
- Enable and start Docker service
- Add ubuntu user to docker group
- Install python3-docker for Ansible Docker modules

**Variables (defaults/main.yml):**
```yaml
docker_group: docker
```

**Tasks:**
1. Update apt cache
2. Install Docker dependencies (apt-transport-https, ca-certificates, curl, software-properties-common, python3-docker)
3. Add Docker's official GPG key from https://download.docker.com/linux/ubuntu/gpg
4. Add Docker repository for Ubuntu {{ ansible_distribution_release }}
5. Install Docker packages
6. Start and enable Docker service
7. Add ubuntu user to docker group (triggers docker restart handler)

**Handlers:**
```yaml
- name: restart docker
  service:
    name: docker
    state: restarted
```

**Idempotency:**  Fully idempotent
- APT operations use `state: present`
- Service operations use declarative state management
- User group membership is idempotent (append: yes)

---

### Role 3: App_Deploy Role

**Purpose:** Deploy containerized application using Docker

**Location:** `roles/app_deploy/`

**Responsibilities:**
- Authenticate with Docker Hub
- Pull Docker image
- Stop and remove existing container
- Run new container with proper configuration
- Wait for application to be ready
- Verify application health

**Variables (defaults/main.yml):**
```yaml
app_port: 5000
app_restart_policy: unless-stopped
app_environment: {}
```

**Variables (from group_vars/all.yml - encrypted with Vault):**
```yaml
dockerhub_username: DOCKER_USERNAME
dockerhub_password: DOCKER_PASSWORD
app_name: devops-info-python
docker_image: DOCKER_USERNAME/devops-info-python
docker_image_tag: latest
app_port: 5000
app_container_name: devops-app
app_environment: {}
```

**Tasks:**
1. Log in to Docker Hub (skipped if no password, secured with no_log: true)
2. Pull Docker image with `source: pull`
3. Stop existing container (ignored if doesn't exist)
4. Remove old container (ignored if doesn't exist)
5. Run new container with port mapping 5000:8080
6. Wait for port 5000 to be available (delay: 5s, timeout: 30s)
7. Verify health endpoint: GET http://localhost:5000/health -> 200 OK (retries: 3)
8. Display health check result with uptime

**Handlers:**
```yaml
- name: restart app container
  docker_container:
    name: "{{ app_container_name }}"
    state: restarted
```

**Idempotency:**  Fully idempotent
- Docker image pull uses `source: pull` (only downloads if needed)
- Container stop/remove operations ignore errors for missing containers
- Container state management is declarative
- Wait_for and URI checks don't modify system state

**Key Implementation Details:**
- **Port Mapping:** Maps external port 5000 to container port 8080 (app runs on 8080 internally)
- **Health Check:** Verifies /health endpoint returns 200 status code
- **Security:** Docker Hub credentials encrypted with Ansible Vault, masked in logs with `no_log: true`
- **Error Handling:** Gracefully handles missing containers with `ignore_errors: true`

---

## 3. Idempotency Demonstration

Idempotency is a critical IaC principle: running a playbook multiple times should produce the same result.

### First Run: Provision Playbook

**Command:**
```bash
ansible-playbook playbooks/provision.yml --vault-password-file .vault_pass
```

**Output (First Run):**
```
PLAY [Provision web servers] *****

TASK [Gathering Facts] ****
ok: [lab5-vm]

TASK [common : Update apt cache] ****
changed: [lab5-vm]

TASK [common : Install common packages] ****
changed: [lab5-vm]

TASK [docker : Update apt cache] ****
changed: [lab5-vm]

TASK [docker : Install Docker dependencies] ****
changed: [lab5-vm]

TASK [docker : Add Docker GPG key] ****
changed: [lab5-vm]

TASK [docker : Add Docker repository] ****
changed: [lab5-vm]

TASK [docker : Install Docker packages] ****
changed: [lab5-vm]

TASK [docker : Ensure Docker service is started and enabled] ****
changed: [lab5-vm]

TASK [docker : Add ubuntu user to docker group] ****
changed: [lab5-vm]

PLAY RECAP ****
lab5-vm : ok=11 changed=8 unreachable=0 failed=0
```

**Analysis:** 11 total tasks, 8 changed (expected on first run)
- The 11th task is the `restart docker` handler, triggered by the "Add ubuntu user to docker group" task
- Handlers run at the end of the play and only execute when notified
- 8 tasks needed changes: APT cache, packages, Docker setup, user group, and handler restart
- 3 tasks showed `ok`: Facts, one apt cache (already updated), service already started

### Second Run: Provision Playbook (Idempotency Test)

**Command:**
```bash
ansible-playbook playbooks/provision.yml --vault-password-file .vault_pass
```

**Output (Second Run):**
```
PLAY [Provision web servers] *****

TASK [Gathering Facts] ****
ok: [lab5-vm]

TASK [common : Update apt cache] ****
ok: [lab5-vm]

TASK [common : Install common packages] ****
ok: [lab5-vm]

TASK [docker : Update apt cache] ****
ok: [lab5-vm]

TASK [docker : Install Docker dependencies] ****
ok: [lab5-vm]

TASK [docker : Add Docker GPG key] ****
ok: [lab5-vm]

TASK [docker : Add Docker repository] ****
ok: [lab5-vm]

TASK [docker : Install Docker packages] ****
ok: [lab5-vm]

TASK [docker : Ensure Docker service is started and enabled] ****
ok: [lab5-vm]

TASK [docker : Add ubuntu user to docker group] ****
ok: [lab5-vm]

PLAY RECAP ****
lab5-vm : ok=10 changed=0 unreachable=0 failed=0
```

**Result:**
- All 10 tasks show `ok` status
- Zero changes on second run
- This proves roles are idempotent and safe to re-run
- System reached desired state on first run, needs no modifications on second

**Why Tasks Are Idempotent:**
- `apt` module with `state: present` checks if packages are installed before modifying
- `service` module checks current service state before making changes
- `apt_key` and `apt_repository` check if already added
- `user` module with `append: yes` idempotently manages group membership

**Why Task Count Differs (11 vs 10):**
- First run: 10 regular tasks + 1 handler = 11 total
- Second run: 10 regular tasks + 0 handlers = 10 total
- Handler `restart docker` only runs when notified (first run only)
---

## 4. Ansible Vault Usage & Credential Management

### Vault Implementation in Lab 5

**Encrypted File:** `group_vars/all.yml`

```
$ head -5 group_vars/all.yml
$ANSIBLE_VAULT;1.1;AES256
32633064643561653832393936666532366466363236626535643362376134353966633364386633
6561666331363466623638313362633062303632616534370a383638386331346564623530383766
36343063303030613838663165666263613631643131373138333464646666393631633265613934
6139666361376134330a373235623930313561663537376232616366633363323938623763323932
```

**Viewing Encrypted Content:**
```bash
$ ansible-vault view group_vars/all.yml --vault-password-file .vault_pass
---
# Docker Hub credentials (here username and password are removed since it's sensitive information)
dockerhub_username: DOCKER_USERNAME
dockerhub_password: DOCKER_PASSWORD

# Application configuration
app_name: devops-info-python
docker_image: DOCKER_USERNAME/devops-info-python
docker_image_tag: latest
app_port: 5000
app_container_name: devops-app
app_environment: {}
```

### Vault Password Management

**Password Storage:** `.vault_pass` file (gitignored)

```bash
$ chmod 600 .vault_pass  # Only owner can read
$ cat .vault_pass
SOMEPASSWORD
```

**In .gitignore:**
```
.vault_pass
```

This prevents accidental commit of the vault password.

### Using Vault in Playbooks

**In playbooks/deploy.yml:**
```yaml
- name: Deploy application
  hosts: webservers
  become: true
  vars_files:
    - ../group_vars/all.yml
  roles:
    - app_deploy
```

**Running with Vault:**
```bash
# Option 1: Prompt for password
ansible-playbook playbooks/deploy.yml --ask-vault-pass

# Option 2: Use vault password file (more convenient)
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass
```

### Security in Docker Login Task

The `docker_login` task in app_deploy role uses `no_log: true` to prevent credentials from appearing in Ansible logs:

```yaml
- name: Log in to Docker Hub
  docker_login:
    username: "{{ dockerhub_username }}"
    password: "{{ dockerhub_password }}"
    state: present
  no_log: true
```

**Why Ansible Vault is Important:**
1. **Encryption at Rest:** Credentials are encrypted in files
2. **Safe in Git:** Can commit encrypted files to version control
3. **No Hardcoding:** Prevents credentials in code
4. **Secret Rotation:** Easy to update passwords without code changes
5. **Audit Trail:** Changes can be tracked in git history
6. **Access Control:** Only users with vault password can see secrets

---

## 5. Deployment Verification

### Deployment Playbook Execution

**Command:**
```bash
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass
```

**Output:**
```
PLAY [Deploy application] ****

TASK [Gathering Facts] ****
ok: [lab5-vm]

TASK [app_deploy : Log in to Docker Hub] ****
ok: [lab5-vm]

TASK [app_deploy : Pull Docker image] ****
ok: [lab5-vm]

TASK [app_deploy : Stop existing container] ****
changed: [lab5-vm]

TASK [app_deploy : Remove old container] ****
changed: [lab5-vm]

TASK [app_deploy : Run application container] ****
changed: [lab5-vm]

TASK [app_deploy : Wait for application port to be available] ****
ok: [lab5-vm]

TASK [app_deploy : Verify application health endpoint] ****
ok: [lab5-vm]

TASK [app_deploy : Display health check result] ****
ok: [lab5-vm] => {
    "msg": "Application is healthy: {'status': 'healthy', 'timestamp': '2026-02-23T11:31:44.363943+00:00', 'uptime_seconds': 13}"
}

PLAY RECAP ****
lab5-vm : ok=9 changed=3 unreachable=0 failed=0
```

**Result:**  **DEPLOYMENT SUCCESSFUL!**
- All 9 tasks completed successfully
- 3 tasks made changes (stopped old container, removed it, started new one)
- 0 failed tasks
- Application is healthy

### Container Status Verification

**Command:**
```bash
ansible webservers -a "docker ps" --vault-password-file .vault_pass
```

**Output:**
```
lab5-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                    COMMAND                  CREATED          STATUS          PORTS                    NAMES
9a71d208efa8   DOCKER_USERNAME/devops-info-python:latest   "gunicorn -b 0.0.0.0…"   56 seconds ago   Up 55 seconds   0.0.0.0:5000->8080/tcp   devops-app
```

**Verification:**  Container is running
- Container ID: 9a71d208efa8
- Image: DOCKER_USERNAME/devops-info-python:latest
- Status: Up 55 seconds
- Port mapping: 0.0.0.0:5000->8080/tcp (external 5000 -> internal 8080)
- Name: devops-app

### Health Check Verification

**Verification Method:** Ansible health check task

The deploy playbook includes a health check task that verifies the application is responding correctly on the managed host:

```yaml
- name: Verify application health endpoint
  uri:
    url: "http://localhost:5000/health"
    method: GET
  register: health_check
  failed_when: health_check.status != 200
```

**Result:**
```
TASK [app_deploy : Display health check result] ****
ok: [lab5-vm] => {
    "msg": "Application is healthy: {'status': 'healthy', 'timestamp': '2026-02-23T11:31:44.363943+00:00', 'uptime_seconds': 13}"
}
```

**Verification:**  Application is healthy
- Health endpoint responding with status 200 OK
- Application uptime: 13+ seconds
- Container is running and functional

*Note: Health checks performed internally on the managed host via Ansible for security.*

### Main Application Endpoint

The application also exposes a main service endpoint providing system and runtime information. This is verified through Ansible's internal health checks during deployment.

**Example Response Structure:**
```json
{
  "endpoints": [
    {
      "description": "Service information",
      "method": "GET",
      "path": "/"
    },
    {
      "description": "Health check",
      "method": "GET",
      "path": "/health"
    }
  ],
  "service": {
    "description": "DevOps course info service",
    "framework": "Flask",
    "name": "devops-info-service",
    "version": "1.0.0"
  },
  "system": {
    "architecture": "x86_64",
    "cpu_count": 2,
    "platform": "Linux",
    "python_version": "3.13.12"
  }
}
```

**Verification:**  Service endpoints available and responding
---

## 6. Key Decisions & Justifications

### Q1: Why use roles instead of plain playbooks?

**Answer:** Roles provide:
- **Reusability:** Can use same role across multiple projects without duplication
- **Organization:** Clear structure makes code easier to navigate and maintain
- **Modularity:** Can enable/disable roles per environment
- **Sharing:** Roles can be published to Ansible Galaxy for team reuse
- **Testing:** Each role can be tested independently

In this lab, the common, docker, and app_deploy roles are completely independent and reusable.

### Q2: How do roles improve reusability?

**Answer:** 
- **Standalone:** A role contains all its tasks, handlers, defaults, and templates
- **No External Deps:** Doesn't require specific playbook structure to work
- **Parameterizable:** Uses variables to customize behavior across projects
- **Portable:** Can copy role directory to another project and use immediately

Example: The docker role can be reused in any project needing Docker.

### Q3: What makes a task idempotent?

**Answer:** Idempotent tasks:
- Check current state before making changes
- Only modify if needed to reach desired state
- Produce same result on repeated runs
- Don't have side effects from re-execution

Example: `apt: state: present` - Only installs if not installed


### Q4: How do handlers improve efficiency?

**Answer:** Handlers:
- **Batched Execution:** Run once at end of play, even if triggered multiple times
- **Conditional Execution:** Only run if notified by a task
- **Efficiency:** Avoid unnecessary restarts/reloads
- **Readability:** Separate concerns (task changes vs. service restarts)

Example: If adding user to docker group, only restart docker once at the end, not immediately.

### Q5: Why is Ansible Vault necessary?

**Answer:**
- **Encryption:** Prevents credentials from being visible in files
- **Version Control:** Can safely commit encrypted files to git
- **Compliance:** Helps meet security and audit requirements
- **Access Control:** Only users with vault password can decrypt
- **Audit Trail:** Changes are tracked in git history
- **No Hardcoding:** Credentials separated from code

Without Vault, credentials would either be:
1. Hardcoded in playbooks (security risk)
2. Gitignored and not tracked (lose configuration)
3. In separate untracked files (lose infrastructure-as-code principle)


### Challenges Faced During Implementation

- **Undefined Variables in Playbook** - Vault variables weren't being loaded until we added `vars_files` directive to load `group_vars/all.yml`
- **Docker Port Mismatch** - Initial health checks failed because container port mapping wasn't correctly configured (5000:8080)
- **Ansible Module Parameter Names** - Had to use correct parameter name `env` instead of `environment` in docker_container module
- **Handler Notification Logic** - First run showed 11 tasks (with handler), second run showed 10 (handler not notified) - this is correct idempotent behavior
- **Security - Credential Exposure** - Had to ensure all credentials are in vault-encrypted files and sensitive IPs removed from documentation

---

## 7. Note: screenshots folder have terminal output proofs (IPs are partially hide)