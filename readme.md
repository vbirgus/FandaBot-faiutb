# UTB Discord Verification & Role Bot

A custom Discord bot designed for the student community of UTB (Tomas Bata University) to streamline identity verification using university email addresses and manage role assignments via reaction menus.

> Developed by **Vojtěch Birgus** and **Radim Měrka**

---

## ✨ Features

- **Email Verification**
  - Verifies users through their `@utb.cz` university email.
  - Sends a 6-digit verification code via email.
  - Automatically assigns appropriate roles: `Verified`, `Impostor`, or `Applicant`.
  - Prevents reuse of the same email address.
  - Email blacklist support.

- **Reaction Role Menus**
  - Allows users to choose roles by reacting with emojis.
  - Role menus supported:
    - **Nationality** (`Czech`, `Slovak`)
    - **Type of Study** (`Full-time`, `Part-time`)
    - **Field of Study** (`ISR`, `PA`)
    - **Year** (`1st Year`, ..., `Master 2nd Year`)
    - **Veteran Status** (`Graduate`, `PhD`)
  - Logic to prevent incompatible role combinations (e.g., `Graduate` cannot have `1st Year`).

- **Applicant Role Button**
  - Users can identify themselves as future students via a button.
  - Automatically removed upon successful email verification.

- **News Scraper**
  - Periodically fetches and posts latest news from:
    - [utb.cz](https://www.utb.cz)
    - [fai.utb.cz](https://fai.utb.cz)
  - Posts news links into a designated channel without duplication.

- **Restricted Channel Handling**
  - Deletes non-file messages from a designated channel.
  - Notifies the user via DM about channel rules.

- **Persistent Data**
  - Saves verified users to a JSON file.
  - Caches sent news articles to avoid reposting.
  - Stores reaction role message-role mapping.

- **Role Reaction Sync on Startup**
  - Automatically restores reaction role states after bot restart.
  - Syncs roles with selected emojis and removes invalid or outdated ones.

---

## 📦 Requirements

- Python 3.8+
- `discord.py` (with UI components support)
- `.env` file for environment variables
- SMTP-compatible email account (tested with Seznam.cz)
- `reaction_roles.json` (auto-generated)
- `verified_users.json` (auto-generated)

---

## ⚙️ Setup

1. **Clone the repository**

2. **Create a `.env` file** with the following content:

    ```env
    DISCORD_TOKEN=your_discord_bot_token
    EMAIL_ADDRESS=your_email@example.com
    EMAIL_PASSWORD=your_email_password
    VERIFICATION_CHANNEL_ID=your_verification_channel_id
    NEWS_CHANNEL_ID=your_news_channel_id
    ROLE_CHANNEL_ID=your_role_channel_id
    RESTRICTED_CHANNEL_NAME=restricted-channel-name
    EMAIL_BLACKLIST=email1@utb.cz,email2@utb.cz
    ```

3. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Run the bot**:

    ```bash
    python discord_bot_v4.py
    ```

---

## 🛡 Required Roles on Your Discord Server

Make sure the following roles exist on your server:

- `Ověřen` (Verified)
- `Impostor`
- `Uchazeč` (Applicant)
- All roles used in reaction menus, such as:
  - `Česko`, `Slovensko`
  - `Prezenční`, `Kombinované`
  - `ISR`, `PA`
  - `Prvák`, `Druhák`, `Třeťák`, `Ing. Prvák`, `Ing. Druhák`
  - `Absolvent`, `Doktorand`

---

## 🛠 Reaction Role Commands

Admins can run the following commands in Discord to create reaction role menus:

```text
!reactionrole_narodnost
!reactionrole_typ_studia
!reactionrole_obor
!reactionrole_rocnik
!reactionrole_veteran
