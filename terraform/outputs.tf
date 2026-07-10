output "ecr_repository_url" {
  description = "URL do repositorio ECR (usado no CI/CD para enviar a imagem)"
  value       = aws_ecr_repository.vrp_hospitalar.repository_url
}

output "secrets_manager_secret_arn" {
  description = "ARN do segredo no Secrets Manager (OPENAI_API_KEY)"
  value       = aws_secretsmanager_secret.openai_api_key.arn
}

output "github_actions_access_key_id" {
  description = "Access Key ID para configurar como secret no GitHub Actions"
  value       = aws_iam_access_key.github_actions.id
}

output "github_actions_secret_access_key" {
  description = "Secret Access Key para configurar como secret no GitHub Actions"
  value       = aws_iam_access_key.github_actions.secret
  sensitive   = true
}