# NVIDIA GPU access

`node-dev.tf` shares the host's NVIDIA GPU at PCI address `0000:01:00.0`
(the RTX 4060 Laptop GPU on this host) with the container. This is an Incus
container device, so the host can continue using the GPU. The device nodes
belong to container UID/GID 1000 with mode `0660`, allowing the `dev` user
to use them.

`nvidia.runtime = "true"` makes Incus inject the host's NVIDIA driver
libraries. The enabled capabilities are `compute`, `utility`, and `video`
for CUDA, `nvidia-smi`, and hardware video encoding/decoding. Applications
still need their own compatible CUDA and cuDNN runtime packages.

## Host setup

On this Arch Linux host, install the package providing `nvidia-container-cli`
before applying the configuration:

```bash
sudo pacman -S --needed libnvidia-container
cd /home/kian/dev-box
sudo terraform apply
sudo incus --force-local --project default restart node-dev
```

Review Terraform's plan before confirming. The runtime and capability settings
take effect when the container starts, so the first activation needs a restart.
Restarting closes existing container sessions and stops its running workloads.
Ordinary `terraform apply` also works for administrators with direct Incus
socket access; this host's desktop user currently uses sudo for administration.

Inside the container, verify device access as `dev`:

```bash
nvidia-smi
```

The access applies to programs running as `dev`, including FaceFusion; it is
not restricted to one application. The container continues to use the host's
NVIDIA kernel driver. To remove access persistently, remove the GPU device and
the two NVIDIA configuration entries from Terraform, apply, and restart.

References: [GPU devices](https://linuxcontainers.org/incus/docs/main/reference/devices_gpu/)
and [NVIDIA runtime options](https://linuxcontainers.org/incus/docs/main/reference/instance_options/#nvidia-and-cuda-configuration).
