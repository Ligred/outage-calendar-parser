Here is a comprehensive `README.md` file tailored to your project. It covers the local setup, the architecture, and the deployment steps for Google Cloud (Run & Functions) as we discussed.

You can copy-paste this directly into your project root.

-----

# 💡 Lviv Power Outage Calendar Sync (LOE to Google Calendar)

  

This project automates the process of fetching power outage schedules from the **Lviv Oblenergo (LOE)** API and syncing them to a specific **Google Calendar**.

It is designed to run "serverless" on **Google Cloud Platform (GCP)** using the Free Tier resources.

## ✨ Features

  * **HTML Parsing:** Fetches raw data from the LOE API (`photo-grafic` endpoint) and parses HTML for "Today" and "Tomorrow".
  * **Smart Sync:** Uses a "Clear & Repopulate" strategy for the specific day to ensure the calendar always reflects the latest changes (removing cancelled outages or updating times).
  * **Target Group:** Configured for **Group 5.2** (customizable).
  * **Cost Efficient:**
      * Runs on **Cloud Run Jobs** (only pays for seconds of execution).
      * Scheduled via **Cloud Scheduler** (e.g., 7:00 AM - 11:30 PM).
  * **Telegram Trigger:** Includes a Cloud Function webhook to manually trigger an update via a Telegram Bot command (`/update`).

## 🏗️ Architecture

1.  **Cloud Scheduler:** Triggers the job every 30 minutes.
2.  **Telegram Bot:** Sends a webhook to Cloud Functions to trigger an immediate run.
3.  **Cloud Run Job:**
      * Fetches data from LOE API.
      * Authenticates with Google Calendar via Service Account.
      * Updates the Calendar.

## 🚀 Prerequisites

1.  **Google Cloud Project:** With billing enabled (for API access, though usage stays within Free Tier).
2.  **Google Calendar API:** Enabled in GCP Console.
3.  **Service Account:** Created in GCP with permission to edit the target Google Calendar.
4.  **Telegram Bot Token:** (Optional) If you want the manual trigger.

## 📂 Project Structure

```text
.
├── main.py                 # Core logic: API parsing & Calendar sync (Cloud Run Job)
├── telegram_trigger.py     # Webhook logic for Telegram (Cloud Function)
├── Dockerfile              # Instructions to build the image for Cloud Run
├── requirements.txt        # Python dependencies
├── service_account.json    # GCP Credentials (⚠️ DO NOT COMMIT THIS FILE)
└── README.md               # Documentation
```

## 🛠️ Local Setup

1.  **Clone the repository:**

    ```bash
    git clone <your-repo-url>
    cd <folder-name>
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Configuration:**

      * Place your `service_account.json` in the root folder.
      * Open `main.py` and update the constants:
        ```python
        TARGET_GROUP = "5.2"
        CALENDAR_ID = "your_calendar_id@group.calendar.google.com"
        ```

4.  **Run locally:**

    ```bash
    python main.py
    ```

## ☁️ Deployment to Google Cloud

### 1\. Deploy the Main Logic (Cloud Run Job)

This job handles the actual parsing and syncing.

**Build the Docker Image:**

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/light-bot
```

**Create the Job:**

```bash
gcloud run jobs create light-bot-job \
  --image gcr.io/YOUR_PROJECT_ID/light-bot \
  --region us-central1 \
  --memory 512Mi \
  --max-retries 0 \
  --task-timeout 5m
```

**Set Schedule (Cloud Scheduler):**
Runs every 30 minutes between 07:00 and 23:30 (Kyiv Time).

```bash
gcloud scheduler jobs create http light-scheduler \
  --location us-central1 \
  --schedule "*/30 7-23 * * *" \
  --time-zone "Europe/Kyiv" \
  --uri "https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/YOUR_PROJECT_ID/jobs/light-bot-job:run" \
  --http-method POST \
  --oauth-service-account-email "YOUR_COMPUTE_SERVICE_ACCOUNT_EMAIL"
```

### 2\. Deploy the Telegram Trigger (Cloud Function)

This function listens for `/update` from Telegram and manually starts the Cloud Run Job.

**Deploy Function:**

```bash
gcloud functions deploy telegram-bot-trigger \
  --gen2 \
  --runtime python310 \
  --region us-central1 \
  --entry-point telegram_webhook \
  --source . \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=YOUR_PROJECT_ID,TELEGRAM_TOKEN=YOUR_BOT_TOKEN
```

**Set Telegram Webhook:**
Replace values and visit this URL in your browser:

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=<YOUR_CLOUD_FUNCTION_URL>
```

## 🔒 Security Note

  * **`service_account.json`**: Never commit this file to GitHub/GitLab. Add it to your `.gitignore`.
  * When deploying to Cloud Run via `gcloud builds submit`, the local JSON file is bundled into the private container image in Google Container Registry, which is safe for private projects.

## 📝 Troubleshooting

  * **Calendar not updating?** Check if the Service Account email is added to the "Share with specific people" settings of your Google Calendar with "Make changes to events" permission.
  * **"Billing not enabled"?** Ensure your GCP project has a billing account linked (required for APIs), even if you stay within the free tier.
  * **Timezone issues?** Ensure `Europe/Kyiv` is set in both the Python script and the Cloud Scheduler configuration.