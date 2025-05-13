# 🚍 Public Transport Tracking & Alert System
A real-time tracking and notification system for public transit. Built using AWS services like Lambda, API Gateway, DynamoDB, SNS, S3, and CloudFormation.


# 🚀 Features

* 🚌 Real-time bus tracking with live data from public transport APIs

* 🔔 Personalized notifications for transit delays or route changes

* 🧑‍🤝‍🧑 User registration and authentication via AWS Cognito

* ✉️ Email alerts for subscribed users (via AWS SNS)

* 🌐 API endpoints for managing subscriptions, status checks, and email updates

* 🛠 Serverless architecture for scalability and low-cost operation

* ☁️ Deployment and infrastructure management using AWS CloudFormation

* 🗃 Storage of deployment artifacts in Amazon S3.


# 🧱 Tech Stack

## Frontend (client/)
   ⚡ HTML/CSS/JavaScript

   ⚡ Interacts with the backend through API Gateway  

## Backend (server/)
   ⚡ AWS Lambda (Python)  

   ⚡ API Gateway (for routing requests and securing endpoints via Cognito)

   ⚡ DynamoDB (for storing user data and subscription logs)  

   ⚡ SNS (for email notifications)  

   ⚡ Amazon S3 (for storing Lambda deployment artifacts)

   ⚡ CloudFormation (for infrastructure management and deployment).



# 🚏 API Endpoints

| Method | Endpoint                  | Description                                  |
|--------|---------------------------|----------------------------------------------|
| POST   | /subscribe                | Subscribe to transit alerts                  |
| GET    | /status                   | View delay status for your routes            |
| PUT    | /update                   | Update subscription details (e.g., email)    |
| DELETE | /unsubscribe              | Unsubscribe from transit alerts              |
| DELETE | /subscription             | Remove subscription record from DynamoDB     |


 All endpoints are protected via Amazon API Gateway and secured with Cognito authorizers.



## 👥 Project Contributors

A cross-functional team behind the development of a serverless transit alert system powered by AWS and real-time transit data.

| Name                 | Role                                   |
|----------------------|----------------------------------------|
| Devynn McDaniel      | Initiative Facilitator                 |
| Mehmet Ozdemir       | Backend Developer (AWS & Python)       |
| Patrick Medida       | Frontend Developer (UI/UX Integration) |
| Akinbiyi Fagbemi     | Creative Strategist                    |
| Mbah Cobbi           | Solutions Analyst                      |



# 🔒 Security

All sensitive data is securely managed:

* DynamoDB stores user data and subscription logs with encryption at rest.
* Lambda environment variables are used for managing credentials and other sensitive information, never hard-coded in the codebase.
* API Gateway enforces HTTPS for secure data transmission.
* IAM Roles ensure that Lambda functions have the necessary permissions to interact with DynamoDB, SNS, and other AWS services.
* S3 stores Lambda deployment artifacts securely, ensuring that only authorized users can upload and retrieve code packages.


# 📄 License

Permission is granted, free of charge, to use, copy, modify, and distribute this Software, provided that the original copyright and permission notice are included.

The above copyright notice and this permission notice must be included in all copies or substantial portions of the Software.


# 📜 DISCLAIMER

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.

IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.