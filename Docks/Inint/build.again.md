sudo apt update
git clone https://github.com/openthread/ot-ns.git ./otns
cd otns
 ./script/install-deps
./script/install
rm -rf openthread 
git clone https://github.com/openthread/openthread openthread
cd openthread
cd  script
./bootstrap
./cmake-build simulation

-----------------
rm -rf ~/otns/openthread/build/simulslation
mkdir -p ~/otns/openthread/build/simulation
cd ~/otns/openthread/build/simulation

cmake -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DOT_SIMULATION=ON \
    -DOT_COMMISSIONER=ON \
    -DOT_JOINER=ON \
    -DOT_COAP=ON \
    -DOT_PLATFORM=simulation \
    ../..

ninja

