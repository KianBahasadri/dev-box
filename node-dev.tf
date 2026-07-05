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
}
