# UTB Discord Verification & Role Bot

A custom Discord bot designed for student communities of UTB (Tomas Bata University) to streamline the process of identity verification using university email addresses, as well as to manage role assignments via reaction menus.

> Developed by **Vojtěch Birgus** and **Radim Měrka**.


## ✨ Features

- **Email Verification**
  - Verifies users through their `@utb.cz` university email.
  - Sends a 6-digit verification code via email.
  - Automatically assigns appropriate roles (e.g., "Verified" or "Impostor").

- **Reaction Role Menus**
  - Allows users to choose roles by reacting with emojis.
  - Categories include:
    - Nationality (`Czech`, `Slovak`)
    - Type of Study (`Full-time`, `Part-time`)
    - Field of Study (`ISR`, `PA`)
    - Year (`1st Year`, ..., `Master 2nd Year`)
    - Veteran status (`Graduate`, `PhD`)

- **Applicant Role**
  - Users can self-identify as applicants (future students) with a button click.

- **Restricted Channel Handling**
  - Automatically deletes non-file messages in a specific channel and notifies the user.

## 📦 Requirements

- Python 3.8+
- `discord.py` (with UI support)
- `.env` file for environment variables
- SMTP-compatible email account (tested with seznam.cz)
- A `reaction_roles.json` file (auto-generated)

## ⚙️ Setup

1. Clone this repository.

2. Create a `.env` file with the following content:

    ```env
    DISCORD_TOKEN=your_discord_bot_token
    EMAIL_ADDRESS=your_email@example.com
    EMAIL_PASSWORD=your_email_password
    VERIFICATION_CHANNEL_ID=your_verification_channel_id
    RESTRICTED_CHANNEL_NAME=restricted-channel-name
    EMAIL_BLACKLIST=email1@utb.cz,email2@utb.cz
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

4. Run the bot:

    ```bash
    python discord_bot_v1.py
    ```

## 🛡 Roles Required on Server

Ensure the following roles exist on your Discord server:

- `Verified`
- `Impostor`
- `Uchazeč` (Applicant)
- All roles used in reaction menus (e.g., `Česko`, `ISR`, `Prvák`, etc.)

## 🛠 Reaction Role Commands

Admins can run these commands to create reaction role menus:

```text
!reactionrole_narodnost
!reactionrole_typ_studia
!reactionrole_obor
!reactionrole_rocnik
!reactionrole_veteran
