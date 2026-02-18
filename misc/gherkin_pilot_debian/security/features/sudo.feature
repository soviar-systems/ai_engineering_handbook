# Phase 1 Pilot: Sudo Privilege Division
#
# Stakeholders:
#   Security division (Product Owner) — authors acceptance criteria
#   System architect — translates policy intent into scenarios
#   OS developer — implements sudoers config, writes step definitions
#
# Lifecycle:
#   user story → Three Amigos session → this file → step definitions → CI gate
#
# Run: uv run pytest security/features/sudo.feature -v

Feature: Sudo Privilege Division
  As a security division, we need to enforce the principle of least privilege
  for all workstation user roles. Elevated access must be scoped, audited,
  and individually granted — not inherited through group membership alone.

  Background:
    Given the workstation has a configured sudoers policy in /etc/sudoers.d/
    And the audit daemon is running and writes to /var/log/auth.log

  # ---------------------------------------------------------------------------
  # Domain: Package management
  # User story: "As a developer, I need to install approved packages via apt
  #              so that I can set up my development environment."
  # Security requirement: permitted only for packages in the approved list;
  #                       action must be logged with full user identity.
  # ---------------------------------------------------------------------------

  Scenario: Developer installs an approved package via apt
    Given the user is a member of the 'developers' group
    And 'python3-dev' is in the approved package list
    When the user runs "sudo apt install python3-dev"
    Then the command exits with code 0
    And /var/log/auth.log contains an entry with the user's identity and the command

  Scenario: Developer cannot install a package not on the approved list
    Given the user is a member of the 'developers' group
    And 'netcat-traditional' is not in the approved package list
    When the user runs "sudo apt install netcat-traditional"
    Then the command exits with code 1
    And no package is installed on the system

  Scenario: Analyst role cannot run apt with sudo
    Given the user is a member of the 'analysts' group
    When the user runs "sudo apt install python3-dev"
    Then the command exits with code 1

  # ---------------------------------------------------------------------------
  # Domain: Service management
  # User story: "As a sysadmin, I need to reload firewall rules so that
  #              network policy changes take effect without rebooting."
  # Security requirement: permitted only for specific systemd units listed
  #                       in the sysadmin sudoers fragment.
  # ---------------------------------------------------------------------------

  Scenario: Sysadmin reloads the firewall service
    Given the user is a member of the 'sysadmins' group
    When the user runs "sudo systemctl reload nftables"
    Then the command exits with code 0
    And /var/log/auth.log contains an entry with the user's identity and the command

  Scenario: Developer cannot manage systemd services
    Given the user is a member of the 'developers' group
    When the user runs "sudo systemctl reload nftables"
    Then the command exits with code 1

  # ---------------------------------------------------------------------------
  # Domain: Privilege escalation — absolute prohibition
  # User story: "As a sysadmin, I need a root shell for emergency maintenance."
  # Security requirement: DENIED for all roles. Emergency access is handled
  #                       exclusively via the break-glass procedure (out-of-band).
  # ---------------------------------------------------------------------------

  Scenario Outline: No role can gain an unrestricted root shell
    Given the user is a member of the '<role>' group
    When the user runs "<command>"
    Then the command exits with code 1
    And no interactive shell process is spawned as root

    Examples:
      | role       | command      |
      | developers | sudo -i      |
      | sysadmins  | sudo -i      |
      | analysts   | sudo -i      |
      | developers | sudo su -    |
      | sysadmins  | sudo su -    |
      | developers | sudo bash    |

  # ---------------------------------------------------------------------------
  # Domain: Sudoers configuration integrity
  # These scenarios verify the policy file structure, not runtime behaviour.
  # Run in CI before any image delivery.
  # ---------------------------------------------------------------------------

  Scenario: The sudoers configuration passes visudo syntax validation
    When visudo -c is run against /etc/sudoers and /etc/sudoers.d/
    Then visudo exits with code 0

  Scenario: No sudoers fragment grants unrestricted ALL=(ALL) NOPASSWD:ALL
    When the sudoers policy is inspected for wildcard privilege grants
    Then no fragment contains the pattern "ALL=(ALL) NOPASSWD: ALL"
    And no fragment contains the pattern "ALL=(ALL:ALL) NOPASSWD: ALL"
