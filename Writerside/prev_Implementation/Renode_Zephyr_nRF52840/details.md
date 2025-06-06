```bash 
root@kospas:/mnt/c/Users/kos00# lsb_release -a
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 22.04.5 LTS
Release:        22.04
Codename:       jammy
```


 
``` bash
 root@kospas:/mnt/c/Users/kos00# renode --version
Renode v1.15.3.6113
  build: 1b68a3ec-202503260323
  build type: Release
  runtime: Mono 4.0.30319.42000
 ```


root@kospas:/mnt/c/Users/kos00/renode-zephyr-nrf52840/zephyr/zephyr#  cat west.yml
# The west manifest file for upstream Zephyr.
#
# The per-installation west configuration file, .west/config, sets the
# path to the project containing this file in the [manifest] section's
# "path" variable.
#
# You are free to create your own manifest files and put them in any
# repository you want, to create your own custom Zephyr installations.
# For example, you could create a manifest file in your own out of
# tree application directory, which would pull this zephyr repository
# in as an ordinary project.
#
# You can pass your manifest repositories to west init when creating a
# new Zephyr installation. See the west documentation for more
# information.

manifest:
  defaults:
    remote: upstream

  remotes:
    - name: upstream
      url-base: https://github.com/zephyrproject-rtos

  #
  # Please add items below based on alphabetical order
  projects:
    - name: canopennode
      revision: f167efe85c8c7de886f1bc47f9173cfb8a346bb5
      path: modules/lib/canopennode
    - name: civetweb
      revision: 094aeb41bb93e9199d24d665ee43e9e05d6d7b1c
      path: modules/lib/civetweb
    - name: cmsis
      revision: b0612c97c1401feeb4160add6462c3627fe90fc7
      path: modules/hal/cmsis
      groups:
        - hal
    - name: edtt
      revision: 7dd56fc100d79cc45c33d43e7401d1803e26f6e7
      path: tools/edtt
      groups:
        - tools
    - name: fatfs
      revision: 94fcd6bfb3801ac0a5e12ea2f52187e0a688b90e
      path: modules/fs/fatfs
      groups:
        - fs
    - name: hal_altera
      revision: 23c1c1dd7a0c1cc9a399509d1819375847c95b97
      path: modules/hal/altera
      groups:
        - hal
    - name: hal_atmel
      revision: 9f78f520f6cbb997e5b44fe8ab17dd5bf2448095
      path: modules/hal/atmel
      groups:
        - hal
    - name: hal_cypress
      revision: 81a059f21435bc7e315bccd720da5a9b615bbb50
      path: modules/hal/cypress
      groups:
        - hal
    - name: hal_espressif
      revision: 22d8246a520d2cf1ca6ba2e690471913cc00482a
      path: modules/hal/espressif
      west-commands: west/west-commands.yml
      groups:
        - hal
    - name: hal_infineon
      revision: f1fa8241f8786198ba41155413243de36ed878a5
      path: modules/hal/infineon
      groups:
        - hal
    - name: hal_microchip
      revision: 870d05e6a64ea9548da6b907058b03c8c9420826
      path: modules/hal/microchip
      groups:
        - hal
    - name: hal_nordic
      revision: a6e5299041f152da5ae0ab17b2e44e088bb96d6d
      path: modules/hal/nordic
      groups:
        - hal
    - name: hal_nuvoton
      revision: b4d31f33238713a568e23618845702fadd67386f
      path: modules/hal/nuvoton
      groups:
        - hal
    - name: hal_nxp
      revision: c7bb88ec3240f1f44b1aafd2831b1472ca99b1d8
      path: modules/hal/nxp
      groups:
        - hal
    - name: hal_openisa
      revision: 40d049f69c50b58ea20473bee14cf93f518bf262
      path: modules/hal/openisa
      groups:
        - hal
    - name: hal_quicklogic
      revision: b3a66fe6d04d87fd1533a5c8de51d0599fcd08d0
      path: modules/hal/quicklogic
      repo-path: hal_quicklogic
      groups:
        - hal
    - name: hal_silabs
      revision: be39d4eebeddac6e18e9c0c3ba1b31ad1e82eaed
      path: modules/hal/silabs
      groups:
        - hal
    - name: hal_st
      revision: 575de9d461aa6f430cf62c58a053675377e700f3
      path: modules/hal/st
      groups:
        - hal
    - name: hal_stm32
      revision: 2d95b36c57c3245e2d08714592790750c95a73af
      path: modules/hal/stm32
      groups:
        - hal
    - name: hal_telink
      revision: ffcfd6282aa213f1dc0848dbca6279b098f6b143
      path: modules/hal/telink
      groups:
        - hal
    - name: hal_ti
      revision: 1992a4c536554c4f409c36896eda6abdc414d277
      path: modules/hal/ti
      groups:
        - hal
    - name: hal_xtensa
      revision: 6e1cf3c483e87df4888e87c5396b4534570f01af
      path: modules/hal/xtensa
      groups:
        - hal
    - name: libmetal
      revision: 39d049d4ae68e6f6d595fce7de1dcfc1024fb4eb
      path: modules/hal/libmetal
      groups:
        - hal
    - name: littlefs
      path: modules/fs/littlefs
      groups:
        - fs
      revision: 9e4498d1c73009acd84bb36036ee5e2869112a6c
    - name: loramac-node
      revision: 12019623bbad9eb54fe51066847a7cbd4b4eac57
      path: modules/lib/loramac-node
    - name: lvgl
      revision: 783c1f78c8e39751fe89d0883c8bce7336f55e94
      path: modules/lib/gui/lvgl
    - name: lz4
      revision: 8e303c264fc21c2116dc612658003a22e933124d
      path: modules/lib/lz4
    - name: mbedtls
      revision: 5765cb7f75a9973ae9232d438e361a9d7bbc49e7
      path: modules/crypto/mbedtls
      groups:
        - crypto
    - name: mcuboot
      revision: ca01db4216c63678768ea78fe04f27cd80b83246
      path: bootloader/mcuboot
    - name: mcumgr
      revision: 31a2aa9cea58d3ceecbf0d5b91361bff7c94aeca
      path: modules/lib/mcumgr
    - name: mipi-sys-t
      path: modules/debug/mipi-sys-t
      groups:
        - debug
      revision: 75e671550ac1acb502f315fe4952514dc73f7bfb
    - name: nanopb
      revision: d148bd26718e4c10414f07a7eb1bd24c62e56c5d
      path: modules/lib/nanopb
    - name: net-tools
      revision: f49bd1354616fae4093bf36e5eaee43c51a55127
      path: tools/net-tools
      groups:
        - tools
    - name: nrf_hw_models
      revision: a47e326ca772ddd14cc3b9d4ca30a9ab44ecca16
      path: modules/bsim_hw_models/nrf_hw_models
    - name: open-amp
      revision: 6010f0523cbc75f551d9256cf782f173177acdef
      path: modules/lib/open-amp
    - name: openthread
      revision: 5d706547ebcb0a85e11412bcd88e80e2af98c74d
      path: modules/lib/openthread
    - name: segger
      revision: 3a52ab222133193802d3c3b4d21730b9b1f1d2f6
      path: modules/debug/segger
      groups:
        - debug
    - name: sof
      revision: 76feb11d1b8f425021b5691668af2250fee444ac
      path: modules/audio/sof
    - name: tflite-micro
      revision: 9156d050927012da87079064db59d07f03b8baf6
      path: modules/lib/tflite-micro
      repo-path: tflite-micro
    - name: tinycbor
      revision: 40daca97b478989884bffb5226e9ab73ca54b8c4
      path: modules/lib/tinycbor
    - name: tinycrypt
      revision: 3e9a49d2672ec01435ffbf0d788db6d95ef28de0
      path: modules/crypto/tinycrypt
      groups:
        - crypto
    - name: TraceRecorderSource
      revision: 5b5f8d7adbf0e93a09087e8f5708f0eebb8b25bf
      path: modules/debug/TraceRecorder
      groups:
        - debug
    - name: trusted-firmware-m
      path: modules/tee/tfm
      revision: c74be3890c9d975976fde1b1a3b2f5742bec34c0
      groups:
        - tee

  self:
    path: zephyr
    west-commands: scripts/west-commands.yml