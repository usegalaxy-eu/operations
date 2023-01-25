# VGCN
## Build Requirements
The repo VGCN holds all everything needed to build the VirtualGalaxyComputeNodes.
It uses `packer`, the [packer qemu plugin](https://github.com/hashicorp/packer-plugin-qemu/releases) and `qemu-kvm`.
From Rocky 8 `qemu-kvm` is located in `/usr/libexec/qemu-kvm` and you need to create a symlink to make it work:
```bash
sudo ln -s /usr/libexec/qemu-kvm /usr/bin/qemu-system-x86_64
```

## Adding a new distro
In order to create a new base-image from a distro, just copy e.g. `rockylinux-9.x-x86_64.json` and replace the following values:
```json
{
        "variables": {
                "iso_url": "https://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9.1-x86_64-boot.iso",
                "iso_checksum": "sha256:a36753d0efbea2f54a3dc7bfaa4dba95efe9aa3d6af331d5c5b147ea91240c21",
                "iso_checksum_url": "http://download.rockylinux.org/pub/rocky/9/isos/x86_64/Rocky-9.1-x86_64-boot.iso.CHECKSUM",
                "vm_name": "rockylinux-9.x-x86_64",

```
Then you can execute the makefile with
```bash
make mynewdistro-10.x-86_64/base
```

## Jenkins build script
Since we can not place it in the VGCN repo because of lack of reusability for the community, I decided to place it here (as backup).
```bash
# source openstack creds
set +x
.  $OPENSTACK_CREDENTIALS

pip install -r requirements.txt

# rhel packer installation fails
export PACKER_PATH=/usr/bin/packer

GIT_COMMIT_SHORT=`git log --format="%H" -n 1 | sed -e 's/^\(.\{12\}\).*/\1/g'`
echo "GIT_COMMIT_SHORT=$GIT_COMMIT_SHORT"
VG_BUILD=`cat ansible-roles/group_vars/all.yml | grep '^vg_build:' | sed 's/vg_build: //g'`
echo "VG_BUILD=$VG_BUILD"
NICE_BRANCH=`git name-rev --name-only HEAD | sed 's|remotes/origin/||g'`
echo "NICE_BRANCH=$NICE_BRANCH"
# continue with the same build01 numbering
BN=`expr $BUILD_NUMBER + 142`
echo "BN=$BN"
BUILD_TAG="vggp-v$VG_BUILD-j$BN-$GIT_COMMIT_SHORT-$NICE_BRANCH"
echo "BUILD_TAG=$BUILD_TAG"

sed -i 's/build_tag: .*/build_tag: $BUILD_TAG/' ansible-roles/group_vars/all.yml

#if [[ "$NICE_BRANCH" == "centos8" ]]; then
#    TEMPLATE="centos-8.x-x86_64"
#else
#   TEMPLATE="centos-7.x-x86_64"
#fi

TEMPLATE="rockylinux-9.x-x86_64"

rm -fr $TEMPLATE/base/
rm -fr $TEMPLATE/vgcn-bwcloud/
rm -fr $TEMPLATE/vgcn-bwcloud-internal/
rm -fr $TEMPLATE/vgcn-bwcloud-external/

rm -f .vault_pass
cp $VAULT_PASS .vault_pass

# add PACKER_LOG=1 to be more verbose
make PACKER_LOG=1 $TEMPLATE/base
make $TEMPLATE/vgcn-bwcloud
make $TEMPLATE/vgcn-bwcloud-external
make $TEMPLATE/vgcn-bwcloud-internal

qemu-img convert -O raw $TEMPLATE/vgcn-bwcloud-internal/image "$TEMPLATE/vgcn-bwcloud-internal/bwcloud-jenkins-$BN.raw"
qemu-img convert -O raw $TEMPLATE/vgcn-bwcloud-external/image "$TEMPLATE/vgcn-bwcloud-external/bwcloud-jenkins-$BN.raw"

openstack image create --file "$TEMPLATE/vgcn-bwcloud-internal/bwcloud-jenkins-$BN.raw" $BUILD_TAG

# Release publicly only if on master
if [[ "$NICE_BRANCH" == "centos8" ]]; then
    scp -i $SSH_USER_PRIVATE_KEY "$TEMPLATE/vgcn-bwcloud-external/bwcloud-jenkins-$BN.raw" "galaxy@sn04.bi.uni-freiburg.de:/usr/local/galaxy/galaxy-dist/static/vgcn/$BUILD_TAG.raw"
    ssh -i $SSH_USER_PRIVATE_KEY galaxy@sn04.bi.uni-freiburg.de chmod ugo+r "/usr/local/galaxy/galaxy-dist/static/vgcn/$BUILD_TAG.raw"
fi

```
