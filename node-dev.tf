terraform {
  required_version = ">= 1.5.0"

  required_providers {
    incus = {
      source  = "lxc/incus"
      version = "~> 1.1"
    }
  }
}

provider "incus" {}

resource "incus_instance" "node_dev" {
  name     = "node-dev"
  image    = "images:archlinux/current/amd64"
  profiles = ["default"]
  running  = true

  device {
    name = "condition-assesment-report-generator"
    type = "disk"

    properties = {
      source = "/home/kian/condition-assesment-report-generator"
      path   = "/home/dev/condition-assesment-report-generator"
      shift  = "true"
    }
  }

  device {
    name = "clusterfork"
    type = "disk"

    properties = {
      source   = "/home/kian/clusterfork"
      path     = "/home/dev/clusterfork"
      readonly = "true"
      shift    = "true"
    }
  }

  device {
    name = "clusterfork-auth"
    type = "disk"

    properties = {
      source   = "/home/kian/.local/share/clusterfork-auth"
      path     = "/home/dev/.local/share/clusterfork-auth"
      readonly = "true"
      shift    = "true"
    }
  }

  device {
    name = "game"
    type = "disk"

    properties = {
      source = "/home/kian/game"
      path   = "/home/dev/game"
      shift  = "true"
    }
  }

  # Host localhost:8000/8001 → container :8000/:8001 (e.g. dev servers, game backends).
  device {
    name = "port-8000"
    type = "proxy"

    properties = {
      listen  = "tcp:127.0.0.1:8000"
      connect = "tcp:127.0.0.1:8000"
    }
  }

  device {
    name = "port-8001"
    type = "proxy"

    properties = {
      listen  = "tcp:127.0.0.1:8001"
      connect = "tcp:127.0.0.1:8001"
    }
  }

  # Forwards only the host Wayland socket into the container. A proxy device
  # (rather than a disk mount of /run/user/1000) keeps the host session's
  # D-Bus, ssh-agent, gpg-agent, and PipeWire sockets out of the container,
  # survives compositor restarts, and doesn't block container startup when
  # no host session exists yet.
  device {
    name = "wayland-proxy"
    type = "proxy"

    properties = {
      bind    = "instance"
      connect = "unix:/run/user/1000/wayland-0"
      listen  = "unix:/mnt/wayland-0"

      # Ownership/mode of the listening socket inside the container.
      uid  = "1000"
      gid  = "1000"
      mode = "0600"

      # Host-side connections run as the session owner so the proxy can
      # traverse /run/user/1000 (mode 0700) after dropping privileges.
      "security.uid" = "1000"
      "security.gid" = "1000"
    }
  }
}
