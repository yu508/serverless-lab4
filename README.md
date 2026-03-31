# Лабораторна робота №5
## AWS serverless-застосунок з AI-сервісом (варіант 16)

### Виконала:
Рибчак Юлія

---

## Опис роботи

У цій лабораторній роботі реалізовано розширення попередньої serverless-системи на AWS.

Було створено API для:
- оновлення статусу замовлення
- надсилання сповіщення про зміну статусу
- перекладу тексту сповіщення через Amazon Translate

---

## Використані сервіси AWS

- AWS Lambda
- Amazon API Gateway
- Amazon DynamoDB
- Amazon SNS
- Amazon S3
- Amazon CloudWatch
- Amazon Translate
- IAM
- Terraform

---

## Функціональність

### 1. Оновлення статусу замовлення
Endpoint:

```text
PUT /orders/{id}/status

Приклад body:

{
  "status": "shipped"
}

2. Надсилання перекладеного сповіщення

Endpoint:

PUT /orders/{id}/notify?lang=uk

Цей endpoint:

бере статус замовлення з DynamoDB
формує текст сповіщення
перекладає його через Amazon Translate
надсилає повідомлення через SNS
зберігає результат у DynamoDB
пише лог у S3

Розгортання

У папці lab5/envs/dev виконати:

terraform init -reconfigure
terraform fmt -recursive
terraform validate
terraform plan
terraform apply -auto-approve

Приклад перевірки через Postman / curl

Оновлення статусу:

PUT /orders/1/status

Надсилання сповіщення:

PUT /orders/1/notify?lang=uk
Додатково

Для зручності тестування реалізовано простий HTML-інтерфейс (ui/index.html), через який можна викликати API без Postman.