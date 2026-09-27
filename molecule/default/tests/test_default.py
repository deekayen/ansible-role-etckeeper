"""Testinfra checks for the etckeeper role."""


def test_packages_installed(host):
    assert host.package("etckeeper").is_installed
    assert host.package("openssh-clients").is_installed


def test_root_ssh_key(host):
    key = host.file("/root/.ssh/id_rsa")
    assert key.is_file
    assert key.user == "root"
    assert key.mode == 0o600
    assert host.file("/root/.ssh/id_rsa.pub").is_file


def test_etckeeper_initialized(host):
    assert host.file("/etc/.etckeeper").is_file
    assert host.file("/etc/.git").is_directory


def test_push_remote_configured(host):
    conf = host.file("/etc/etckeeper/etckeeper.conf")
    assert conf.contains('^PUSH_REMOTE="gitlab"$')


def test_git_identity(host):
    name = host.check_output("git -C /etc config --local user.name")
    email = host.check_output("git -C /etc config --local user.email")
    assert name == "Ansible etckeeper"
    assert email.startswith("root@")
