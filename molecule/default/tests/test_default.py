import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_dependencies_installed(host):
    assert host.package("etckeeper").is_installed
    assert host.package("openssh-clients").is_installed


def test_etckeeper_files(host):
    assert host.file("/root/.ssh/known_hosts").is_file
    assert host.file("/etc/.git/logs/refs/heads/master").exists
    assert host.file("/etc/.etckeeper").is_directory
