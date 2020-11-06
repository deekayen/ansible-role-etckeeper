etckeeper
=========

[![CI](https://github.com/deekayen/ansible-role-etckeeper/workflows/CI/badge.svg)](https://github.com/deekayen/ansible-role-etckeeper/actions?query=workflow%3ACI) [![Project Status: Inactive – The project has reached a stable, usable state but is no longer being actively developed; support/maintenance will be provided as time allows.](https://www.repostatus.org/badges/latest/inactive.svg)](https://www.repostatus.org/#inactive)

Install the [etckeeper](https://etckeeper.branchable.com) application, configure it, and have it push configuration archives to a remote GitLab repository.

Requirements
------------

The `gitlab_ansible_token` variable is unset. Generate and set an API token for running the role.

Default Variables
-----------------

```
etckeeper_ssh_key_bits: 3072

gitlab_group: ''
gitlab_issues_enabled: no
gitlab_snippets_enabled: no
gitlab_wiki_enabled: no
gitlab_visibility: private


gitlab_fqdn: gitlab.com

gitlab_ansible_token: ""
```

Dependencies
------------

The EPEL repo is used to install etckeeper packages.

```
dependencies:
- src: geerlingguy.repo-epel
```

Example Playbook
----------------

Keep your API token secret! Even better than this example would be to use `ansible-vault` to create an encrypted string here or to create a vault file in a `group_vars` or `host_vars` folder alongside the playbook.

To encrypt a string as in this example playbook, run something like:

```
ansible-vault encrypt_string 7accd_1-9MnryXehybxx
```

Playbook:

    - hosts: servers

      vars:
        gitlab_fqdn: git.example.com
        gitlab_group: etckeeper
        gitlab_ansible_token: !vault |
          $ANSIBLE_VAULT;1.1;AES256
          65313861666664663531613232356334646663333035613237356232643966663839376462353232
          6337326435343330343534636237656665363634326264320a613036363136636334396238646533
          32316261363032643462383532336162383031376661376664363034613861656233663338643164
          6335353530646365380a383538623162663966373832613433643136646336643532663233666166
          64333933376631616335343964376466373131303365656661303532613739356633

      roles:
        - deekayen.etckeeper
