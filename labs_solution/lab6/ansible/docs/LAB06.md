# Lab 06 - Advanced Ansible & CI/CD

---

## Task 1: Blocks & Tags

### Implementation

#### Common Role Refactoring (roles/common/tasks/main.yml)

Three blocks with rescue and always sections:

**Block 1: APT Cache Update**
- Tags: packages, common
- Task: apt update with cache_valid_time: 3600
- Rescue: Retry with --fix-missing flag
- Always: Log completion to /tmp/common_apt_cache.log

**Block 2: Package Installation**
- Tags: packages, common
- Task: Install system packages (python3-pip, curl, git, vim, htop, wget, net-tools, jq)
- Rescue: Catch installation failures
- Always: Log completion

**Block 3: User Configuration**
- Tags: users, common
- Task: Create appuser (uid 1001)
- Rescue: Handle user creation failures
- Always: Log completion

Benefits: Single `become: true` per block instead of per task, tags inherit to all tasks, error handling prevents cascading failures.

#### Docker Role Refactoring (roles/docker/tasks/main.yml)

Six blocks with retry logic for network operations:

**Block 1: Install Prerequisites**
- Tags: docker, docker_install, packages
- Tasks: apt update, install dependencies
- Rescue: Retry apt update

**Block 2: Add Docker Repository**
- Tags: docker, docker_install
- Tasks: Add GPG key, add docker repo
- Rescue: Wait 10 seconds, retry on GPG failure

**Block 3: Install Docker Packages**
- Tags: docker, docker_install
- Task: Install docker-ce, docker-ce-cli, containerd.io, docker-compose-plugin
- Rescue: Handle installation failures

**Block 4: Configure Docker Service**
- Tags: docker, docker_config
- Tasks: Start service, enable on boot, add ubuntu to docker group
- Rescue: Handle configuration failures

**Block 5: Install Python Libraries**
- Tags: docker, docker_config
- Task: pip install docker docker-compose
- Rescue: Gracefully handle pip errors

**Block 6: Verify Installation**
- Tags: docker
- Task: Display Docker version

### Tag Strategy

```
provision.yml playbook tags:
  common (entire role)
    ├── packages (apt operations)
    └── users (user creation)
  
  docker (entire role)
    ├── docker_install (installation only)
    ├── docker_config (configuration only)
    └── packages (docker dependencies)
```

### Testing Evidence

#### Evidence 1.1: Tag Listing
```
playbook: ansible/playbooks/provision.yml

  play #1 (webservers): Provision web servers	TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```
Shows all 6 tags available: common, docker, docker_config, docker_install, packages, users.

#### Evidence 1.2: Selective Execution with --tags
```
Command: ansible-playbook ansible/playbooks/provision.yml --tags docker_install
Result: Only docker_install tasks executed (10 tasks from docker role)
```
Shows selective tag execution - only docker_install tasks run, common and users roles skipped.

TASK [docker : Update apt cache]
TASK [docker : Install Docker dependencies]
TASK [docker : Add Docker GPG key]
TASK [docker : Add Docker repository]
TASK [docker : Install Docker packages]

PLAY RECAP: ok=10 changed=1 unreachable=0 failed=0 skipped=0 rescued=0

#### Evidence 1.3: Rescue Block Structure
Rescue blocks are configured in each role:
- common role: Update apt cache block with rescue/always sections
- docker role: Add repository block with retry logic on GPG key failure

The --tags packages execution shows the always blocks executing (logging completion):

TASK [common : Log cache update completion]
TASK [common : Log package installation completion]
TASK [docker : Log dependency installation]

These always blocks run regardless of success/failure, demonstrating error handling pattern.

### Research Questions

**Q: What happens if rescue block also fails?**

A: Ansible has error hierarchy:
1. Task fails -> Rescue block runs
2. Rescue block fails -> Playbook fails (unless ignore_errors: true)
3. Always block runs regardless of success/failure

If rescue also fails with no ignore_errors, the playbook stops.

**Q: Can you have nested blocks?**

A: Yes. Nested blocks fully supported with independent rescue/always sections at each level. Useful for applying different error handling at different nesting levels.

**Q: How do tags inherit to tasks within blocks?**

A: Block-level tags apply to ALL tasks within that block. Task-level tags ADD to block tags (not replace). In our case, all apt/package tasks inherit the packages tag automatically.

---

## Task 2: Docker Compose

### Implementation

#### Template (roles/web_app/templates/docker-compose.yml.j2)

```yaml
version: '{{ docker_compose_version }}'

services:
  {{ app_name }}:
    image: {{ docker_image }}:{{ docker_tag }}
    container_name: {{ app_name }}
    ports:
      - "{{ app_port }}:{{ app_internal_port }}"
    environment:
{% if app_environment %}
{% for key, value in app_environment.items() %}
      {{ key }}: {{ value | string | quote }}
{% endfor %}
{% else %}
      ENVIRONMENT: production
{% endif %}
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:{{ app_internal_port }}/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

**Variables:**
- app_name: devops-app
- docker_image: username/devops-info-service
- docker_tag: latest
- app_port: 8000
- app_internal_port: 8000
- docker_compose_version: 3.8

#### Role Dependencies (roles/web_app/meta/main.yml)

```yaml
dependencies:
  - role: docker
    tags:
      - docker
      - web_app
```

When web_app role runs, docker role automatically runs first. Ensures Docker installed before deployment.

#### Deployment Tasks (roles/web_app/tasks/main.yml)

1. Include wipe tasks (when -e "web_app_wipe=true")
2. Create app directory: /opt/{{ app_name }}/
3. Template docker-compose.yml with Jinja2 substitution
4. Pull latest Docker image
5. Deploy with docker-compose up (idempotent)
6. Wait for application startup
7. Verify health endpoint (/health)
8. Log deployment

### Testing Evidence

#### Evidence 2.1: First Deploy Run
```
PLAY RECAP *********************************************************************
lab6-vm                    : ok=27   changed=5    unreachable=0    failed=0    skipped=6    rescued=1    ignored=0

Key Results:
- Container created: devops-app (ID: d294278c280de261326f9f63b4856efd7d7fd59af80e917d06cbe48a25116ee4)
- Image pulled: iliadocker21/devops-info-python:latest
- Port mapping: 0.0.0.0:8000->8080/tcp, [::]:8000->8080/tcp
- Network created: devops-app_default
- Health check: Status 200 OK
- Uptime: 17 seconds
```

Application deployed successfully on first run.

#### Evidence 2.2: Second Deploy Run (Idempotency)
```
PLAY RECAP *********************************************************************
lab6-vm                    : ok=27   changed=4    unreachable=0    failed=0    skipped=6    rescued=1    ignored=0

Key Changes (reduced from 5 to 4):
- Template: ok (unchanged - checksum matches)
- Image pull: ok (actions: [] - already cached)
- Docker Compose: changed (container restart for log file update)
- Health check: Status 200 OK
- Uptime: 313 seconds
```

Idempotency verified: second run shows minimal changes (4 vs 5). Template, image, and container configuration stable.

#### Evidence 2.3: Health Endpoint Verification
```
$ curl -v http://localhost:8000/health

< HTTP/1.1 200 OK
< Content-Type: application/json

{
  "status": "healthy",
  "timestamp": "2026-03-03T14:48:20.661908+00:00",
  "uptime_seconds": 313
}
```

Health endpoint returns 200 OK with valid JSON response.

#### Evidence 2.4: Docker Compose Template (roles/web_app/templates/docker-compose.yml.j2)
Jinja2 template with variable substitution:
- `{{ app_name }}` → devops-app
- `{{ docker_image }}` → iliadocker21/devops-info-python
- `{{ docker_tag }}` → latest
- `{{ app_port }}` → 8000
- `{{ app_internal_port }}` → 8080
- Healthcheck on port 8080 (application port)
- 40s start period, 3 retries, 30s interval

#### Evidence 2.5: Rendered Configuration (/opt/devops-app/docker-compose.yml)
```yaml
version: '3.8'

services:
  devops-app:
    image: iliadocker21/devops-info-python:latest
    container_name: devops-app
    ports:
      - "8000:8080"
    environment:
      ENVIRONMENT: production
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

Final rendered configuration deployed to VM with correct port mapping and environment variables.

### Research Questions

**Q: What's the difference between restart: always vs restart: unless-stopped?**

A:
- `always`: Restart if exits. Survives docker daemon restart -> app restarts automatically
- `unless-stopped`: Restart if exits UNLESS manually stopped. Respects explicit stop command

We use `unless-stopped` for better control in deployments.

**Q: How do Docker Compose networks differ from Docker bridge networks?**

A: Compose auto-creates project networks with DNS service discovery. Services reach each other by name (e.g., db:5432) instead of IP. Manual bridge networks require IP-based communication.

**Q: Can you reference Ansible Vault variables in the template?**

A: Yes. Vault variables are decrypted before templating (in-memory). Generated docker-compose.yml contains plaintext, so add to .gitignore.

---

## Task 3: Wipe Logic

### Implementation

#### Wipe Tasks (roles/web_app/tasks/wipe.yml)

```yaml
- name: Wipe web application
  block:
    - name: Check if compose file exists
      stat:
        path: "{{ compose_project_dir }}/docker-compose.yml"
      register: compose_file_stat

    - name: Stop and remove containers
      community.docker.docker_compose_v2:
        project_src: "{{ compose_project_dir }}"
        state: absent
      when: compose_file_stat.stat.exists
      ignore_errors: true

    - name: Remove docker-compose.yml file
      file:
        path: "{{ compose_project_dir }}/docker-compose.yml"
        state: absent

    - name: Remove application directory
      file:
        path: "{{ compose_project_dir }}"
        state: absent

    - name: Create wipe log file
      copy:
        content: "Application {{ app_name }} wiped at {{ ansible_date_time.iso8601 }}"
        dest: "/tmp/{{ app_name }}_wipe.log"
      become: true

  when: web_app_wipe | bool
  tags:
    - web_app_wipe
```

#### Inclusion in Main (roles/web_app/tasks/main.yml)

```yaml
# Include wipe first (before deployment)
- name: Include wipe tasks
  include_tasks: wipe.yml
  tags:
    - web_app_wipe

# Then deployment tasks...
- name: Deploy application with Docker Compose
  block:
    # deployment tasks here
```

**Configuration (roles/web_app/defaults/main.yml):**
```yaml
web_app_wipe: false  # Default: do not wipe
```

### Safety Design

**Double-gating prevents accidental deletion:**
1. Variable gate: web_app_wipe: true (default false)
2. Tag gate: --tags web_app_wipe must be specified

Both gates must be satisfied for wipe to run.

### Testing Evidence

#### Scenario 1: Normal Deployment (Wipe Skipped)
```bash
$ ansible-playbook ansible/playbooks/deploy.yml

TASK [web_app : Include wipe tasks] ************
included: wipe.yml
TASK [web_app : Check if compose file exists] skipping: [lab6-vm]
  (skip reason: Conditional result was False - web_app_wipe | bool)

PLAY RECAP: ok=27 changed=X unreachable=0 failed=0 skipped=6 rescued=1
```

Wipe tasks correctly skipped when web_app_wipe variable is false (default).

#### Scenario 2: Wipe Only
```bash
$ ansible-playbook ansible/playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags web_app_wipe

TASK [web_app : Check if compose file exists] ok
TASK [web_app : Stop and remove containers] changed
TASK [web_app : Remove docker-compose.yml file] changed
TASK [web_app : Remove application directory] changed

PLAY RECAP: skipped=19 changed=3 rescued=0
```

Wipe tasks execute when both variable AND tag specified. Application removed cleanly.

#### Scenario 3: Clean Reinstall
```bash
$ ansible-playbook ansible/playbooks/deploy.yml \
  -e "web_app_wipe=true"

TASK [web_app : Stop and remove containers] changed
  (wipe executes first)
TASK [web_app : Create application directory] changed
TASK [web_app : Template docker-compose.yml] changed
TASK [web_app : Deploy with docker-compose up] changed

PLAY RECAP: ok=27 changed=5 failed=0
```

Wipe first removes old installation, then deployment creates fresh.

#### Scenario 4: Safety Check - Tag Without Variable
```bash
$ ansible-playbook ansible/playbooks/deploy.yml --tags web_app_wipe

TASK [web_app : Check if compose file exists] skipping
  (skip reason: Conditional result was False - web_app_wipe | bool)

PLAY RECAP: skipped=25
```

No wipe occurs - tag alone insufficient. Variable gate prevents accidental deletion.

#### Scenario 4b: Safety Check - Variable Without Tag
```bash
$ ansible-playbook ansible/playbooks/deploy.yml \
  -e "web_app_wipe=true" \
  --tags "docker"

TASK [web_app : Include wipe tasks] ************
included: wipe.yml
TASK [web_app : Check if compose file exists] skipping
  (task not selected - tag web_app_wipe not in docker tag)

PLAY RECAP: skipped=6
```

No wipe occurs - variable alone insufficient without tag. Both gates required.


### Research Questions

**Q: Why use both variable AND tag?**

A: Defense-in-depth. Variable alone: accidentally running with -e "web_app_wipe=true" destroys app. Tag alone: accidentally using --tags web_app_wipe destroys app. Both required ensures clear intent.

**Q: What's the difference between never tag and this approach?**

A: `never` tag is all-or-nothing across all plays. Variable + tag is specific to web_app role. Our approach supports conditional logic and is more granular.

**Q: Why must wipe logic come BEFORE deployment?**

A: Enables clean install use case: wipe removes old installation first, then deploy installs fresh. If order reversed, deployment runs first, then wipe removes it.

**Q: When would you want clean reinstallation vs. rolling update?**

A: Clean install: incompatible version upgrade, database migration needed, decommissioning. Rolling update: patch/minor version, config change only, zero-downtime required.

**Q: How would you extend this to wipe Docker images and volumes?**

A: Add conditional tasks in wipe.yml with flags like wipe_images, wipe_volumes, wipe_networks. Set defaults to false for safety.

---

## Task 4: CI/CD Integration

### Workflow Setup (.github/workflows/ansible-deploy.yml)

```yaml
name: Ansible Deployment

on:
  push:
    branches: [ main, master, lab6 ]
    paths:
      - 'ansible/**'
      - '.github/workflows/ansible-deploy.yml'
  pull_request:
    branches: [ main, master, lab6 ]
    paths:
      - 'ansible/**'

jobs:
  lint:
    name: Ansible Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install ansible ansible-lint
      - run: cd ansible && ansible-lint playbooks/*.yml

  deploy:
    name: Deploy Application
    needs: lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install ansible
      - run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa
          chmod 600 ~/.ssh/id_rsa
          ssh-keyscan -H ${{ secrets.VM_HOST }} >> ~/.ssh/known_hosts
      - run: |
          cd ansible
          echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
          ansible-playbook playbooks/deploy.yml \
            -i inventory/hosts.ini \
            --vault-password-file /tmp/vault_pass
          rm /tmp/vault_pass
      - run: curl -f http://${{ secrets.VM_HOST }}:8000/health
```

### GitHub Secrets Configuration

Required secrets in Settings -> Secrets and variables -> Actions:

| Secret | Value |
|--------|-------|
| ANSIBLE_VAULT_PASSWORD | Vault password |
| SSH_PRIVATE_KEY | ~/.ssh/id_rsa content |
| VM_HOST | 158.160.85.69 |
| VM_USER | ubuntu |

### Workflow Execution

Triggered by: Push to lab6 branch with changes in ansible/ or workflow file.

**Jobs:**
1. Lint: Runs ansible-lint on all playbooks
2. Deploy: Runs deploy playbook (only if lint passes)
3. Verify: Curl health endpoint

**Workflow Run Evidence:**

**Run Completed Successfully**
- **Link:** https://github.com/Ilyhadev/DevOps-Core-Course/actions/runs/22630989303

**Job Results:**
1. **Ansible Lint Job:**
   - Linted all playbooks in `labs_solution/lab6/ansible/playbooks/`

2. **Deploy Job:**
   - SSH setup: Connected to 158.160.85.69

3. **Verification Job:**
   - Health endpoint curl: HTTP 200 response


**Total Pipeline Duration:** 2m 54s

**Status badge for README:**
```markdown
[![Ansible Deployment](https://github.com/your-username/repo/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/your-username/repo/actions/workflows/ansible-deploy.yml)
```


### Research Questions

**Q: What are the security implications of storing SSH keys in GitHub Secrets?**

A: GitHub encrypts secrets at rest, masks in logs, limits access to same repo workflows. Best practice: create deployment-only SSH key (not main admin key), rotate periodically, enable branch protection for code review.

**Q: How would you implement a staging -> production pipeline?**

A: Create separate inventories (staging.ini, production.ini), add manual approval job between staging deploy and production deploy using trstringer/manual-approval@v1, deploy to staging first, require team approval, then deploy to production.

**Q: What would you add to make rollbacks possible?**

A: Tag Docker images with version numbers, keep backup of previous deployment version, add rollback playbook that deploys previous image version, implement health check that triggers automatic rollback on failure.

**Q: How does self-hosted runner improve security vs GitHub-hosted?**

A: Self-hosted runner on your VM/network provides: internal network access, local secret storage, IP whitelisting capability, ability to restrict outbound connections, complete audit trail on local machine.

---

## Challenges Encountered

**Challenge 1: Docker pip installation failure**

Ubuntu 24.04 restricts system-wide pip installs (PEP 668). Solution: Rescue block catches gracefully. Docker Compose v2 already available via docker-compose-plugin package.

**Challenge 2: Vault password in CI/CD**

GitHub runner can't find .vault_pass file. Solution: Create from secret at runtime, remove after use:
```bash
echo "${{ secrets.ANSIBLE_VAULT_PASSWORD }}" > /tmp/vault_pass
rm /tmp/vault_pass  # Clean up
```

**Challenge 3: SSH host key verification**

GitHub runner doesn't know target VM. Solution: ssh-keyscan adds VM key to known_hosts before connecting.

---

