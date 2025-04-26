# Last Setup 

```markdown
    WSL : 
        PRETTY_NAME="Ubuntu 22.04.5 LTS"
        NAME="Ubuntu"
        VERSION_ID="22.04"
        VERSION="22.04.5 LTS (Jammy Jellyfish)"
        VERSION_CODENAME=jammy
        ID=ubuntu
        ID_LIKE=debian
        HOME_URL="https://www.ubuntu.com/"
        SUPPORT_URL="https://help.ubuntu.com/"
        BUG_REPORT_URL="https://bugs.launchpad.net/ubuntu/"
        PRIVACY_POLICY_URL="https://www.ubuntu.com/legal/terms-and-policies/privacy-policy"
        UBUNTU_CODENAME=jammy
```

```bash
 mkdir -p src
cd src 
git clone --recursive https://github.com/openthread/openthread.git
cd openthread
./script/bootstrap
./script/cmake-build simulation
 ./script/cmake-build posix -DOT_DAEMON=ON
```

## You will have the following binaries
| Tool / Binary   | Path                                             | What It Does                                                                                                                  |
|-----------------|--------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------|
| ot-cli-ftd      | ./build/simulation/examples/apps/cli/ot-cli-ftd  | Full Thread Device (FTD) simulation CLI node (Router, Leader, FED). This is the one we spawn multiple times!                  |
| ot-cli-mtd      | ./build/simulation/examples/apps/cli/ot-cli-mtd  | Minimal Thread Device (MTD) simulation CLI node (not needed for DAfI, but nice to have).                                      |
| ot-daemon       | ./build/posix/examples/apps/daemon/ot-daemon     | A POSIX background daemon that manages virtual Thread interfaces (optional for bigger automated tests or system integration). |
| ot-ctl          | ./build/posix/tools/ot-ctl                       | CLI client to control ot-daemon if you use it (kind of like nmcli for NetworkManager).                                        |
| ot-commissioner | ./build/posix/tools/commissioner/ot-commissioner | Standalone Thread Commissioner tool (for joining and authentication tests).                                                   |
| ot-bbr          | ./build/posix/tools/border_router/ot-bbr         | Basic Border Router sample (used to simulate Border Router behavior — not mandatory for DAfI).                                |
| ot-config       | ./build/posix/tools/config/ot-config             | Inspect and manipulate OpenThread configuration files.                                                                        |
| ot-link         | ./build/posix/tools/link/ot-link                 | Used for direct radio link layer testing (lower level than simulation).                                                       |
| ot-ip6          | ./build/posix/tools/ip6/ot-ip6                   | Direct IPv6 testing tool for OpenThread nodes.                                                                                |

## Test to ensure everything is ok 
# start node 1 & 2 , do setup and ping them , then run coap and see if it is okay 