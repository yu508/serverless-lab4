# Serverless Lab 4 - AWS (V - 16)


У цій лабораторній роботі реалізовано serverless-застосунок на AWS для зміни статусу замовлення.

API дозволяє оновити статус замовлення через HTTP-запит та автоматично надсилає сповіщення.

---

## Використані сервіси AWS

- AWS Lambda — обробка запиту
- Amazon API Gateway — HTTP API
- Amazon DynamoDB — зберігання замовлень
- Amazon SNS — email-сповіщення
- Amazon S3 — зберігання логів
- Amazon CloudWatch — логування

---

 Розгортання
Ініціалізація Terraform:
terraform init
Перевірка:
terraform plan
Розгортання:
terraform apply -auto-approve
Тестування
Через Postman або PowerShell:
PUT https://<api-url>/orders/1/status

Body:

{
  "status": "shipped"
}
 
Результати

Після виконання запиту:

оновлюється запис у DynamoDB
надсилається email через SNS
створюється лог у S3
запис логів у CloudWatch
 Очищення ресурсів

Після завершення:

terraform destroy -auto-approve

 Автор

Рибчак Юлія
