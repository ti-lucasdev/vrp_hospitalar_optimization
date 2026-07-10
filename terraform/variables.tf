variable "aws_region" {
  description = "Regiao da AWS onde os recursos serao criados"
  type        = string
  default     = "us-east-1"
}

variable "openai_api_key" {
  description = "Chave da API da OpenAI (fornecida na hora do apply, nunca commitada)"
  type        = string
  sensitive   = true
}