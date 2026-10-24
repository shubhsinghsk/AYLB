# AYLB Careers, Google Sheets, and Email Setup

This guide records the complete setup for the AYLB Contact email and Careers application integrations. It is written for a future setup or recovery, so follow the sections in order.

## What the website does

- The Contact form saves each enquiry to the local `contacts.csv` file and emails the configured `EMAIL_TO` address.
- The Careers page reads active job listings from the `OpenPositions` tab in Google Sheets.
- A Careers application is added as a row in the `Applications` tab, then emailed to `EMAIL_TO` with the applicant's resume attached.
- The spreadsheet stores the resume filename, not the resume file itself.
- Contact enquiries are not added to Google Sheets.
- Contact and Careers emails use the same Gmail sending account and recipient setting. On Render Free, messages use Gmail's HTTPS API; SMTP is an optional fallback for local development or hosts that allow it.

## Part 1: Prepare Gmail sending

Use an email account that the company controls. In the working AYLB setup, the same company Gmail address sends messages and receives them. Use an address authorized by the company if setting this up again.

### 1. Turn on 2-Step Verification

1. Sign in to the Gmail or Google Workspace account that will send the website's email.
2. Open [Google Account Security](https://myaccount.google.com/security).
3. Find **How you sign in to Google**.
4. Open **2-Step Verification**.
5. Turn it on if it is not already on, following Google's prompts.

### 2. Create a Gmail App Password for local SMTP (optional)

1. While signed in to the sending account, open [Google App Passwords](https://myaccount.google.com/apppasswords).
2. Sign in again if Google asks.
3. Enter a name such as `AYLB website`.
4. Create the App Password.
5. Copy it somewhere private so it is available while editing `.env`.
6. Do not use the account's normal Google password.
7. Do not paste the App Password into chat, a ticket, source code, or a spreadsheet.

Google only shows this option when the account is eligible. A Workspace administrator or a security policy may prevent App Passwords. If the option is unavailable, ask the Workspace administrator for the approved SMTP method.

### 3. Gmail SMTP values for local development (optional)

Use these values for Gmail:

| Setting | Gmail value |
| --- | --- |
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_SECURITY` | `starttls` |
| `SMTP_USERNAME` | Full sending email address |
| `SMTP_PASSWORD` | Gmail App Password, with spaces removed |
| `EMAIL_FROM` | `AYLB Logistics <same-sending-address@gmail.com>` |
| `EMAIL_TO` | The inbox that should receive Contact enquiries and Careers applications |

Port 465 can also be used with `SMTP_SECURITY=ssl`. Do not mix port 465 with `starttls`, or port 587 with `ssl`.

### 4. Gmail API setup for Render Free

Render Free blocks outbound SMTP. The app therefore uses Gmail's HTTPS API when `GMAIL_API_REFRESH_TOKEN` is configured. SMTP settings are only a fallback on hosts that permit SMTP.

1. In Google Cloud Console, select the Cloud project used for this website or create a dedicated project.
2. Open **APIs & Services → Library**, search for **Gmail API**, and click **Enable**.
3. Open **Google Auth Platform → Branding** and configure the app name, support email, and contact email.
4. Under **Audience**, choose **External** for a regular Gmail account. Add the sending Gmail account as a test user while setting up.
5. Open **Google Auth Platform → Data Access** and add this exact scope: `https://www.googleapis.com/auth/gmail.send`.
6. Open **Google Auth Platform → Clients → Create Client**.
7. Choose **Desktop app**, give it a name such as `AYLB Render Gmail sender`, and create it.
8. Download the OAuth client JSON file. Keep it private and outside the project/repository.
9. On the computer where the AYLB project is saved, open Terminal and change to the project folder. For example:

   ```bash
   cd /Users/your-name/Work/AYLB
   ```

   Replace `your-name` with the macOS account name. This is the folder containing `run.py` and `requirements.txt`.

10. Activate the project's virtual environment. For the `.venv` folder used in this setup:

    ```bash
    source .venv/bin/activate
    ```

    If your virtual environment has another name, activate that one instead.

11. Install the project's dependencies:

    ```bash
    python -m pip install -r requirements.txt
    ```

12. Run the helper with the downloaded OAuth JSON file as its argument:

    ```bash
    python scripts/get_gmail_refresh_token.py
    ```

    Do not run or open the JSON filename by itself. That tries to execute a data file and can show `permission denied`. After typing the command above and a space, drag the downloaded `client_secret_....json` file from Downloads into the Terminal window. Terminal inserts the full path. Press Return.

13. A browser opens. Sign in as the Gmail address that should send the website email, review the permission, and allow sending email. If Google shows an unverified-app notice, use **Advanced** and continue to the app, provided you recognize the project and initiated this authorization.
14. The terminal prints `GMAIL_API_CLIENT_ID`, `GMAIL_API_CLIENT_SECRET`, and `GMAIL_API_REFRESH_TOKEN`. Treat all three as secrets. Add them to Render directly; do not paste them into chat or commit them.
15. Google marks new external OAuth apps as **Testing** by default. Authorizations for Gmail scopes in Testing expire after seven days. For ongoing production sending, change the app publishing status to **In production**. Google may show an unverified-app warning or require verification depending on the audience and scope; follow the Google console prompts. See Google's [Gmail API Python quickstart](https://developers.google.com/workspace/gmail/api/quickstart/python) and [OAuth publishing status details](https://support.google.com/cloud/answer/15549945).
16. In Render, open the website service, go to **Environment**, and add the three variables from the script output. Also set `EMAIL_FROM` to the same Gmail account used in the browser authorization, such as `AYLB Logistics <sender@gmail.com>`, and `EMAIL_TO` to the inbox that receives enquiries/applications.
17. Save the Render settings and deploy the updated code by following Part 5 below. When Gmail API credentials are present, the updated app automatically uses the Gmail API. If absent, it attempts SMTP using the optional settings above.

## Part 2: Create the Google spreadsheet

### 4. Create the spreadsheet

1. Sign in to Google with the account that will own or manage the Careers spreadsheet.
2. Open [Google Sheets](https://sheets.new) to create a blank spreadsheet.
3. Name it `AYLB Careers`.

### 5. Create the OpenPositions tab

1. At the bottom of the spreadsheet, double-click the first tab, usually named **Sheet1**.
2. Rename the tab exactly `OpenPositions` (no spaces).
3. Click cell **A1**.
4. Paste this tab-separated header row into A1:

```text
title	location	employment_type	description	department	active
```

5. Confirm the six headers appear across columns A through F.
6. Starting in row 2, add one job per row:
   - Column A: job title
   - Column B: location, such as `Noida` or `Remote`
   - Column C: employment type, such as `Full-Time` or `Contract`
   - Column D: short job description
   - Column E: department
   - Column F: `TRUE` to publish or `FALSE` to hide
7. Only enter actual open roles. Adding, editing, or marking a row inactive changes what the website displays after the page is refreshed.

The app treats a blank `active` cell as active for compatibility, so fill column F deliberately for every role.

### 6. Create the Applications tab

1. Click the **+** button at the bottom of the spreadsheet to add a tab.
2. Rename it exactly `Applications`.
3. Click cell **A1**.
4. Paste this header row into A1:

```text
timestamp_utc	applicant_name	applicant_email	applicant_phone	desired_role	cover_letter	resume_filename	status
```

5. Confirm the eight headers appear across columns A through H.
6. Leave the header row in place. The website appends new applications below it.

### 7. Copy the spreadsheet ID

1. Open the `AYLB Careers` spreadsheet.
2. Look at the browser address. It will look similar to:

   `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`

3. Copy only the text between `/d/` and `/edit`.
4. This value goes into `GOOGLE_SHEETS_SPREADSHEET_ID` in `.env`.

## Part 3: Give the website access to Google Sheets

### 8. Create or select a Google Cloud project

1. Open the [Google Cloud project page](https://console.cloud.google.com/projectcreate).
2. Sign in to Google Cloud.
3. Create a project named `AYLB Careers`, or select an existing project that AYLB can use.
4. Make sure the intended project name is selected in the project picker at the top of Google Cloud Console.

### 9. Enable the Google Sheets API

1. With the correct project selected, open the [Google Sheets API page](https://console.cloud.google.com/apis/library/sheets.googleapis.com).
2. Click **Enable**.
3. If the page says it is already enabled, continue.

Google's API setup documentation is [here](https://developers.google.com/workspace/sheets/api/quickstart/python).

### 10. Create a service account

1. Open [Google Cloud Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts).
2. Confirm `AYLB Careers` is selected in the project picker.
3. Click **Create service account**.
4. Enter `aylb-careers-website` as the service account name.
5. Click **Create and continue**.
6. Skip optional project roles; click **Done**. Spreadsheet access is granted directly in the next section.
7. Open the new service account and copy its email address. It ends with `iam.gserviceaccount.com`.

### 11. Create and save a JSON key

1. On the service account page, open the **Keys** tab.
2. Click **Add key → Create new key**.
3. Choose **JSON**.
4. Click **Create** to download the file.
5. Rename the downloaded file `aylb-careers-service-account.json`.
6. Keep it outside the AYLB project folder, for example in your Downloads folder.
7. Never upload the file or paste its contents into chat. If it is exposed, delete that key in Google Cloud and create a replacement.

Google's instructions for service account keys are [here](https://cloud.google.com/iam/docs/keys-create-delete).

### 12. Share the spreadsheet with the service account

1. Open the `AYLB Careers` spreadsheet.
2. Click **Share**.
3. Paste the service account email ending in `iam.gserviceaccount.com`.
4. Set its role to **Editor**.
5. Click **Send** or **Share**.

Sharing this spreadsheet with the service account is essential. Enabling the API alone does not grant access to the spreadsheet.

## Part 4: Configure the local AYLB app

### 13. Find the project folder

The project folder is the folder containing `run.py`, `requirements.txt`, and `env.example`.

### 14. Create or edit `.env`

1. In the project folder, make a copy of `env.example` and name the copy `.env` if `.env` does not exist yet.
2. If `.env` already exists, edit it instead of replacing it. Replacing it would remove the SMTP password already saved there.
3. Open `.env` in a text editor.
4. Fill in SMTP settings from Part 3 for local development. Remove spaces from the App Password. The app prefers Gmail API if `GMAIL_API_REFRESH_TOKEN` is set; otherwise it uses SMTP.
5. Fill in the Google Sheets settings:

```text
GOOGLE_SHEETS_CREDENTIALS_FILE=/full/path/to/aylb-careers-service-account.json
GOOGLE_SHEETS_SPREADSHEET_ID=paste_the_id_copied_from_the_sheet_url
GOOGLE_JOBS_RANGE=OpenPositions!A:F
GOOGLE_APPLICATIONS_RANGE=Applications!A:H
```

6. Replace the example key path with the actual full path to the downloaded JSON file. On the setup machine used for this integration, the file is in the user's Downloads folder under the name `aylb-careers-service-account.json`.
7. Replace the spreadsheet ID placeholder with the ID copied in Step 7.
8. Save `.env`.
9. Do not commit `.env` or the JSON key. `.gitignore` is configured to ignore `.env` files and common service-account key filenames.

The app loads `.env` when it starts. Restart the app after editing environment settings.

### 15. Install the project dependencies

The app needs the packages listed in `requirements.txt`, including the Google Sheets client and Certifi.

1. Open Terminal.
2. Change to the project folder, for example:

   ```bash
   cd /Users/your-name/Work/AYLB
   ```

3. If you normally use a virtual environment, activate that same one first. For the project `.venv` on macOS:

   ```bash
   source .venv/bin/activate
   ```

4. Install or update the requirements:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Start the app using the same environment, for example:

   ```bash
   python run.py
   ```

If the project uses `.venv-1` instead, activate `.venv-1` and install the requirements there. The Python environment used to start the app must have the requirements installed.

## Part 5: Deploy the Gmail API integration to Render Free

Render Free blocks outbound SMTP ports `25`, `465`, and `587`. The website must use the Gmail API over HTTPS. Merely adding Gmail variables to Render does not change the old SMTP code; the updated application must also be deployed. See [Render's Free plan limits](https://render.com/docs/free).

### 16. Save Gmail OAuth settings in Render

1. Sign in to Render and open the AYLB website Web Service.
2. Open **Environment**.
3. Add `GMAIL_API_CLIENT_ID` and paste the matching value printed by the local helper.
4. Add `GMAIL_API_CLIENT_SECRET` and paste its matching value.
5. Add `GMAIL_API_REFRESH_TOKEN` and paste its matching value.
6. Set `EMAIL_FROM` to the same Gmail account you authorized in the browser. It can include a display name, for example `AYLB Logistics <sender@gmail.com>`.
7. Keep `EMAIL_TO` set to the inbox that should receive Contact enquiries and Careers applications.
8. Keep Google Sheets variables and its Secret File as already configured. They are separate from Gmail authorization.
9. Save the Environment settings. Choose **Save only** if available; otherwise allow Render to deploy, then deploy the newest code in the following steps.
10. Do not paste these values into chat, commit them, or put them in a public document. The OAuth client JSON file is also private and should remain outside the repository.

All three `GMAIL_API_*` values are required by this app. Gmail API settings take priority over SMTP when `GMAIL_API_REFRESH_TOKEN` is present. Keep the old SMTP values until Gmail API sending has been confirmed.

### 17. Push and deploy the updated application code

1. The Gmail API implementation and local authorization helper must be included in the code version Render deploys. The helper is `scripts/get_gmail_refresh_token.py`.
2. Push the updated code to the Git branch connected to the Render service. For this setup, the feature branch is `codex/careers-integrations`.
3. In Render, open **Settings → Build & Deploy** and check the service's **Branch**.
4. If it is `codex/careers-integrations`, open **Deploys** and wait for the latest commit to finish deploying. The deployment should include the Gmail API sender code and `google-auth-oauthlib` dependency.
5. If Render watches `main`, merge the feature branch into `main` through a pull request. Wait for the resulting deployment, or use **Manual Deploy → Deploy latest commit** if auto-deploy is disabled.
6. Confirm the deployment status is **Live** before testing either form.

Do not deploy only the environment settings while leaving the old application code in place. The old SMTP implementation will still try port 587 and fail on Render Free.

## Part 6: Verify the setup

### 18. Verify Contact email

1. For Render, first confirm the deployment is **Live**. For local development, start or restart the app after saving `.env`.
2. Open the Contact page in a browser.
3. Submit a clearly labeled test message.
4. Confirm the page shows a success message.
5. Check the `EMAIL_TO` inbox and Spam folder for the test email.
6. Contact enquiries are appended to the app's local `contacts.csv`; remove a test row if appropriate. Render Free has an ephemeral filesystem, so local file changes do not persist through restarts or deploys.

### 19. Verify job listings

1. Confirm one or more real open positions are listed in `OpenPositions` with `TRUE` in column F.
2. Open or refresh the Careers page.
3. Confirm active roles appear and inactive roles do not.
4. If there are no active rows, the page shows an empty-state message. If Sheets is unreachable, it shows a temporary unavailable message.

### 20. Verify an application

1. Open the Careers page and click **Apply Now** for a listed role.
2. Enter the applicant's name, email, and phone number.
3. Choose the intended role from the list.
4. Attach a PDF or DOCX resume smaller than 5 MB.
5. Optionally enter a cover letter.
6. Submit the form.
7. Confirm a new row appears in `Applications` with status `New`.
8. Confirm the `EMAIL_TO` inbox receives an application email with the resume attached.
9. If this was only a test, delete the test row afterward and remove the test email if desired.

The application row is written first. If email delivery then fails, the page warns that the application is recorded and it remains in the `Applications` sheet. If Sheets cannot record the application, the page does not claim it was submitted.

## Troubleshooting

### Contact or Careers email shows a delivery warning

1. On Render Free, confirm all three `GMAIL_API_*` settings are present and copied without extra quotes or spaces.
2. Confirm the OAuth browser flow authorized the same Gmail account named in `EMAIL_FROM`.
3. Confirm **Gmail API** is enabled and that the Gmail address is listed as an OAuth test user if the app is still in Testing.
4. If authorization expired after seven days, move the OAuth app to In production and repeat the local authorization to get a fresh refresh token.
5. Check the Render log for `Gmail API delivery failed` and check the destination inbox's Spam folder.
6. On a host where SMTP is allowed, if using the fallback, check the SMTP settings and app password.

### `CERTIFICATE_VERIFY_FAILED` on macOS Python 3.14

The python.org macOS Python installer provides an **Install Certificates.command** utility. Run it from `/Applications/Python 3.14/Install Certificates.command`; wait for `Successfully installed certifi` and `update complete`, then restart the app. Python's instructions are [here](https://docs.python.org/3.14/using/mac.html).

The app uses HTTPS for Gmail API delivery. Do not disable TLS verification to work around certificate errors.

### Careers page cannot load positions

1. Confirm `GOOGLE_SHEETS_SPREADSHEET_ID` contains only the ID, not the full URL.
2. Confirm the tabs are named exactly `OpenPositions` and `Applications`.
3. Confirm the first row contains the exact header names documented above.
4. Confirm the Google Sheets API is enabled in the selected Cloud project.
5. Confirm the spreadsheet is shared as **Editor** with the service account email.
6. Confirm `GOOGLE_SHEETS_CREDENTIALS_FILE` points to the JSON file and the file still exists at that path.
7. Confirm the Google dependencies are installed in the same Python environment that starts the app.
8. Restart the app and check its terminal logs for the detailed Google API error.

### The page loads, but no roles appear

1. Add a job below the header row in `OpenPositions`.
2. Fill in the `title` column.
3. Set `active` to `TRUE`.
4. Refresh the Careers page.

### Application cannot be recorded

1. Check that the selected role is still active in `OpenPositions`, or select **General Application**.
2. Confirm the service account still has **Editor** access to the spreadsheet.
3. Confirm the `Applications` tab exists and the `Applications!A:H` range is correct.
4. Check the app terminal logs for a Google API error.

### User receives an application warning but the row exists

The application was recorded in Google Sheets, but email delivery failed afterward. Fix the Gmail API settings and use the applicant details in the sheet to follow up. Do not ask the applicant to submit again unless needed; that could create a duplicate row.

## Environment variable reference

| Variable | Purpose |
| --- | --- |
| `GMAIL_API_CLIENT_ID` | OAuth Desktop client ID for the Gmail sender |
| `GMAIL_API_CLIENT_SECRET` | Secret from the OAuth Desktop client |
| `GMAIL_API_REFRESH_TOKEN` | Offline authorization token from the local OAuth helper; secret |
| `SMTP_HOST` | Optional SMTP server, normally `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port, normally `587` for STARTTLS |
| `SMTP_SECURITY` | `starttls`, `ssl`, `auto`, or `none`; Gmail should use `starttls` with port 587 |
| `SMTP_CA_BUNDLE` | Optional custom PEM certificate path for networks with a company CA |
| `SMTP_USERNAME` | Full SMTP account email address |
| `SMTP_PASSWORD` | Optional App Password or provider SMTP password |
| `EMAIL_FROM` | Sender address displayed on outgoing messages |
| `EMAIL_TO` | Inbox for Contact and Careers notifications |
| `GOOGLE_SHEETS_CREDENTIALS_FILE` | Local path to service account JSON key |
| `GOOGLE_SHEETS_CREDENTIALS_JSON` | Alternative: service account JSON stored in a protected environment variable |
| `GOOGLE_SHEETS_SPREADSHEET_ID` | Spreadsheet ID from its URL |
| `GOOGLE_JOBS_RANGE` | Job tab range; default `OpenPositions!A:F` |
| `GOOGLE_APPLICATIONS_RANGE` | Application tab range; default `Applications!A:H` |

For hosted deployments, enter secrets in the hosting provider's protected environment-variable settings. Do not commit them to the repository.
