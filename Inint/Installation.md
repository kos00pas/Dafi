# Ubuntu 
```Bash
    1  clear
    2  sudo apt update
    3  go version
    4  wget https://go.dev/dl/go1.22.1.linux-amd64.tar.gz
    5  sudo tar -C /usr/local -xzf go1.22.1.linux-amd64.tar.gz
    6  echo "export PATH=\$PATH:/usr/local/go/bin" >> ~/.bashrc
    7  source ~/.bashrc
    8  go version
    9  git clone https://github.com/openthread/ot-ns.git ./otns
   10  cd otns
   11  sudo apt install unzip
   12  git clone https://github.com/openthread/ot-ns.git ./otns
   13  ls
   14  cd ..
   15  ls
   16  rm -rf otns/
   17  git clone https://github.com/openthread/ot-ns.git ./otns
   18  cd otns
   19  ./script/install-deps
   20  sudo apt install python3-pip
   21  ./script/install-deps
   22  ./script/install
   23  which otns
   24  git clone https://github.com/openthread/openthread ~/src/openthread
   25  ./script/cmake-build simulation -DOT_OTNS=ON -DOT_SIMULATION_VIRTUAL_TIME=ON -DOT_SIMULATION_VIRTUAL_TIME_UART=ON -DOT_SIMULATION_MAX_NETWORK_SIZE=999
   26  sudo apt install ninja-build build-essential
   27  cd ~/src/openthread
   28  ./script/cmake-build simulation   -DOT_OTNS=ON   -DOT_SIMULATION_VIRTUAL_TIME=ON   -DOT_SIMULATION_VIRTUAL_TIME_UART=ON   -DOT_SIMULATION_MAX_NETWORK_SIZE=999
   29  otns
   pip install grpcio grpcio-tools
   pip install pyshark
```