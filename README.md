# deekayen.etckeeper

[![CI](https://github.com/deekayen/ansible-role-etckeeper/actions/workflows/ci.yml/badge.svg)](https://github.com/deekayen/ansible-role-etckeeper/actions/workflows/ci.yml) [![Ansible Galaxy](https://img.shields.io/badge/galaxy-deekayen.etckeeper-blue.svg)](https://galaxy.ansible.com/ui/standalone/roles/deekayen/etckeeper/) [![Project Status: Inactive – The project has reached a stable, usable state but is no longer being actively developed; support/maintenance will be provided as time allows.](https://www.repostatus.org/badges/latest/inactive.svg)](https://www.repostatus.org/#inactive) ![BSD 3-Clause license](https://img.shields.io/badge/license-BSD%203--Clause-blue)

An Ansible role that installs [etckeeper](https://etckeeper.branchable.com) on EL hosts so changes to `/etc` are committed to a local git repository. Given a GitLab API token, it also creates one GitLab project per host and a deploy key so each host can push its `/etc` history to GitLab.

On the target, the role installs `openssh-clients` and `etckeeper` (from EPEL, through the `geerlingguy.repo-epel` dependency), generates an RSA key for root at `/root/.ssh/id_rsa`, runs `etckeeper init` in `/etc`, sets `PUSH_REMOTE="gitlab"` in `/etc/etckeeper/etckeeper.conf`, and sets the `/etc` repository's git identity to `Ansible etckeeper` and `root@<fqdn>`. When `gitlab_ansible_token` is set, the controller creates a GitLab project named after `inventory_hostname_short` and adds root's public key to it as a deploy key with push access. Handlers then try to add the `gitlab` remote, make the first commit, and push `master`; see [Known issues](#known-issues).

## Requirements

- ansible-core 2.15 or newer on the controller.
- The `community.general` collection: `ansible-galaxy collection install community.general`.
- For the GitLab steps, the `python-gitlab` and `requests` Python libraries on the controller. The project and deploy key tasks run there with `connection: local` and `become: false`.
- Privilege escalation on the target. Run the play with `become: true`; the role installs packages, writes root's SSH key, and initializes a repository in `/etc`.
- Outbound access from the target to the EPEL mirrors, and SSH from the target to `gitlab_fqdn` for the push.
- Fact gathering left on. The git email uses `ansible_facts.fqdn`.

## Supported platforms

From `meta/main.yml`, and each one runs through Molecule in CI:

| Platform | Versions |
| --- | --- |
| EL (Rocky Linux in CI) | 9, 10 |

CI runs without a GitLab token, so it exercises the local commit setup and none of the GitLab tasks or handlers.

## Installation

From Ansible Galaxy:

```bash
ansible-galaxy role install deekayen.etckeeper
ansible-galaxy collection install community.general
```

Or pin it in `requirements.yml`:

```yaml
---
roles:
  - name: deekayen.etckeeper
    src: https://github.com/deekayen/ansible-role-etckeeper.git
    scm: git
    version: main

collections:
  - name: community.general
```

```bash
ansible-galaxy install -r requirements.yml
```

## Role variables

| Variable | Default | Description |
| --- | --- | --- |
| `etckeeper_ssh_key_bits` | `3072` | Size of the RSA key generated for root. The role asserts it is at least `2048`. |
| `gitlab_ansible_token` | `""` | GitLab API token that creates the project and deploy key. When empty or one character long, the role skips every GitLab task and etckeeper commits only locally. Supply it from Ansible Vault or a lookup. |
| `gitlab_group` | `''` | GitLab group for the per-host project, and the path used in the `gitlab` remote URL. When empty, the project goes to the token owner's personal namespace. See [Known issues](#known-issues). |
| `gitlab_issues_enabled` | `false` | Enable the issue tracker on the created project. |
| `gitlab_snippets_enabled` | `false` | Enable snippets on the created project. |
| `gitlab_wiki_enabled` | `false` | Enable the wiki on the created project. |
| `gitlab_visibility` | `private` | Visibility of the created project. The role asserts it is `private`, `internal`, or `public`. |
| `gitlab_fqdn` | `gitlab.com` | GitLab hostname, used for the SSH remote and `ssh-keyscan`. |
| `gitlab_server_url` | `https://{{ gitlab_fqdn }}` | GitLab API base URL. The role asserts it starts with `http://` or `https://`. |

## Behavior

- Every run fetches `/root/.ssh/id_rsa.pub` to `/tmp/.ssh/<inventory_hostname>/root/.ssh/id_rsa.pub` on the controller, and the deploy key task reads it from there.
- The `ssh-keyscan` task appends GitLab's ECDSA host key to `/root/.ssh/known_hosts` only when that file does not exist yet.
- The initial commit and push run only as handlers of the deploy key task, so they happen on the run that creates the deploy key and not on later runs.

## Dependencies

- [geerlingguy.repo-epel](https://github.com/geerlingguy/ansible-role-repo-epel), declared in `meta/main.yml`, so Galaxy installs it automatically.

## Example playbook

Encrypt the token with `ansible-vault encrypt_string`, or keep it in a vaulted `group_vars` file:

```yaml
---
- name: Track /etc with etckeeper and push it to GitLab.
  hosts: el_servers
  become: true

  vars:
    gitlab_fqdn: gitlab.example.internal
    gitlab_group: etckeeper
    gitlab_ansible_token: "{{ vault_gitlab_etckeeper_token }}"

  roles:
    - deekayen.etckeeper
```

`gitlab.example.internal` is a placeholder for your GitLab server, and `vault_gitlab_etckeeper_token` is a placeholder for a vaulted variable. The example sets `gitlab_group: etckeeper` because the deploy key task hardcodes that group. The push still fails until the remote issue under [Known issues](#known-issues) is fixed.

## Tags

| Tag | Tasks |
| --- | --- |
| `install` | `openssh-clients` and `etckeeper` packages. |
| `configure` | `PUSH_REMOTE` setting, GitLab project, and deploy key. |

Input validation in `tasks/assert.yml` is tagged `always`. Key generation, `etckeeper init`, the git identity, and `ssh-keyscan` are untagged.

## Known issues

- `handlers/main.yml:3` runs `etckeeper vcs remote add -m gitlab git@...`. etckeeper's `vcs.d/50vcs-cmd` passes those arguments to git unchanged, and `-m` takes the next argument as its value, so `git remote add` gets only the URL and exits with a usage error (exit code 129 when run directly against a test repository). `failed_when: false` on line 9 hides that, so no `gitlab` remote is created. The push handler on line 19 has no `failed_when`, so any run with `gitlab_ansible_token` set fails at that handler on the run that creates the deploy key.
- `tasks/main.yml:92` hardcodes the deploy key's project as `etckeeper/{{ inventory_hostname_short }}`, while the project task on line 66 creates it in `gitlab_group`. Any other group, or an empty one, points the deploy key at a project the role did not create.
- `tasks/main.yml:33-39` writes `PUSH_REMOTE="gitlab"` even when `gitlab_ansible_token` is empty, although `tasks/assert.yml` says etckeeper will only commit locally. etckeeper's `commit.d/99push` then runs `git push gitlab` after every commit, which fails without a `gitlab` remote; the script ignores the failure, so commits still succeed.
- With an empty `gitlab_group`, the remote URL in `handlers/main.yml:3` becomes `git@<gitlab_fqdn>:/<host>.git`.

## Development

CI runs on every push to `main` and every pull request (see `.github/workflows/ci.yml`):

1. Lint: installs `molecule/default/requirements.yml`, then runs `ansible-lint --profile production` and `flake8 molecule/`.
2. Molecule: converge, idempotence, and testinfra verification in Docker on `rockylinux9` and `rockylinux10`.

To run the same checks locally with Docker available:

```bash
pip3 install ansible-core ansible-lint flake8 molecule "molecule-plugins[docker]" docker pytest-testinfra
ansible-galaxy install -r molecule/default/requirements.yml
ansible-lint --profile production
flake8 molecule/
MOLECULE_DISTRO=rockylinux9 molecule test
```

`MOLECULE_DISTRO` selects a `geerlingguy/docker-<distro>-ansible` image. The testinfra checks in `molecule/default/tests/test_default.py` confirm that `etckeeper` and `openssh-clients` are installed, `/root/.ssh/id_rsa` is a root-owned `0600` file with its public key beside it, `/etc/.etckeeper` and `/etc/.git` exist, `etckeeper.conf` sets `PUSH_REMOTE="gitlab"`, and the `/etc` repository has the `Ansible etckeeper` name and a `root@` email.

The repository also has a `.pre-commit-config.yaml`; run `pre-commit run --all-files` before pushing.

### Repository layout

| Path | Purpose |
| --- | --- |
| `tasks/main.yml` | Packages, root SSH key, etckeeper setup, and the GitLab project and deploy key. |
| `tasks/assert.yml` | Input validation and the no-token warning, tagged `always`. |
| `handlers/main.yml` | Adds the `gitlab` remote, makes the initial commit, and pushes. |
| `defaults/main.yml` | Every user-facing variable. |
| `meta/main.yml` | Galaxy metadata, the supported platform list, and the EPEL dependency. |
| `meta/argument_specs.yml` | Argument spec for the user-facing variables. |
| `molecule/default/` | Molecule scenario: `prepare.yml`, `converge.yml`, role and collection requirements, and testinfra tests. |
| `.github/workflows/` | `ci.yml` for lint and Molecule, `release.yml` for Galaxy import. |

## Releases

Pushing a git tag runs `.github/workflows/release.yml`, which imports the tagged commit into Ansible Galaxy as `deekayen.etckeeper`. The import needs a `GALAXY_API_KEY` repository or organization secret.

## License

BSD 3-Clause. See [LICENSE](LICENSE).

## Author

[David Norman](https://github.com/deekayen). Sponsorship links are in [.github/FUNDING.yml](.github/FUNDING.yml).
