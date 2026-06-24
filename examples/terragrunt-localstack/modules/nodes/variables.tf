variable "nodes" {
  description = "Map of node name to its placement (the subnet it runs in)."
  type = map(object({
    subnet_id = string
  }))
}

variable "ami" {
  description = "AMI id for every node."
  type        = string
}

variable "instance_type" {
  description = "Instance type for every node."
  type        = string
  default     = "t3.micro"
}

variable "security_group_ids" {
  description = "Security groups applied to every node."
  type        = list(string)
}

variable "tags" {
  description = "Tags applied to every node."
  type        = map(string)
  default     = {}
}
