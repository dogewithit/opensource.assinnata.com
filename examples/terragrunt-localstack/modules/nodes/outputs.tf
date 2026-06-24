output "instance_ids" {
  description = "Node name to its EC2 instance id."
  value       = { for name, mod in module.instance : name => mod.id }
}

output "private_ips" {
  description = "Node name to its private IP."
  value       = { for name, mod in module.instance : name => mod.private_ip }
}
