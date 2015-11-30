# Fix GLIBC issue
echo "export LD_PRELOAD=/usr/lib64/libstdc++.so.6:/lib64/libgcc_s.so.1" >> ~/.bashrc

# Use P4API.so built for uni linux (fixes SSL issue)
mkdir -p $HOME/.nuke
cp ./P4* $HOME/.nuke
