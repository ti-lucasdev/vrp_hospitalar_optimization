terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ---------------------------------------------------------------------------
# ECR Repository - onde a imagem Docker da aplicacao fica armazenada
# ---------------------------------------------------------------------------
resource "aws_ecr_repository" "vrp_hospitalar" {
  name                 = "vrp-hospitalar-optimization"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ---------------------------------------------------------------------------
# Secrets Manager - guarda a OPENAI_API_KEY de forma segura
# O valor real da chave NAO fica no codigo: e fornecido na hora do
# "terraform apply", via variavel sensivel (ver variables.tf)
# ---------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "vrp-hospitalar/openai-api-key"
  description = "Chave da API da OpenAI usada pelo modulo de IA do VRP hospitalar"
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key
}

# ---------------------------------------------------------------------------
# IAM User - identidade usada pelo GitHub Actions (CI/CD) para autenticar
# na AWS e enviar (push) imagens Docker para o ECR. Permissao minima,
# restrita apenas ao necessario (nao usa AdministratorAccess).
# ---------------------------------------------------------------------------
resource "aws_iam_user" "github_actions" {
  name = "github-actions-vrp-hospitalar"
}

resource "aws_iam_user_policy" "github_actions_ecr_push" {
  name = "ecr-push-policy"
  user = aws_iam_user.github_actions.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ECRAuth"
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Sid    = "ECRPush"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = aws_ecr_repository.vrp_hospitalar.arn
      }
    ]
  })
}

resource "aws_iam_access_key" "github_actions" {
  user = aws_iam_user.github_actions.name
}