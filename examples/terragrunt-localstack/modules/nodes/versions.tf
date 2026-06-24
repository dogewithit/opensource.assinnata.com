terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source = "hashicorp/aws"
      # Pin to AWS provider 5.x: the ec2-instance module this wraps still uses
      # cpu_core_count / cpu_threads_per_core, which provider 6 removed.
      version = "~> 5.79"
    }
  }
}
