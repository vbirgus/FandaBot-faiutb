import os
import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Button
import smtplib, ssl
import random, string
from email.message import EmailMessage
from dotenv import load_dotenv
import json


# Pro vytvoření Reaction Role Menu použí tyto příkazy:
#!reactionrole_narodnost :flag_cz: Česko :flag_sk: Slovensko
#!reactionrole_typ_studia :regional_indicator_p: Prezenční :regional_indicator_k: Kombinované
#!reactionrole_obor :robot: ISR :wrench: PA
#!reactionrole_rocnik :one: Prvák :two: Druhák :three: Třeťák :four: Ing. Prvák :five: Ing. Druhák
#!reactionrole_veteran :mortar_board: Absolvent :crown: Doktorand
# Příkaz napiš do chatu na discordu.

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

VERIFICATION_CHANNEL_ID = int(os.getenv("VERIFICATION_CHANNEL_ID", "0"))
RESTRICTED_CHANNEL_NAME = os.getenv("RESTRICTED_CHANNEL_NAME", "")


intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.reactions = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

blacklist_raw = os.getenv("EMAIL_BLACKLIST", "")
BLACKLIST = set(email.strip().lower() for email in blacklist_raw.split(",") if email.strip())

pending_verifications = {}

data_file = "reaction_roles.json"

#radim code for role bot
if not os.path.exists(data_file):
    with open(data_file, "w") as f:
        json.dump({}, f)

with open(data_file, "r") as f:
    reaction_data = json.load(f)
#

def send_verification_code(email: str, code: str):
    msg = EmailMessage()
    msg.set_content(f"Toto je tvůj ověřovací kód pro Discord: {code}")
    msg["Subject"] = "Ověření UTB Discord účtu"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = email

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.seznam.cz", 465, context=context) as server:
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

class VerifyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(VerifyButton())
        self.add_item(ApplicantButton())  # Přidá tlačítko pro uchazeče


class VerifyButton(Button):
    def __init__(self):
        super().__init__(label="Ověřit", style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ověření probíhá přes soukromé zprávy (DM)...", ephemeral=True)

        def check(m):
            return m.author == interaction.user and isinstance(m.channel, discord.DMChannel)

        try:
            dm_channel = await interaction.user.create_dm()
            await dm_channel.send("👋 Ahoj! Napiš prosím svůj školní e-mail (@utb.cz):")
            email_msg = await bot.wait_for("message", timeout=120, check=check)
            email = email_msg.content.strip().lower()
            guild = interaction.guild or discord.utils.get(bot.guilds)

            if not email.endswith("@utb.cz"):
                await dm_channel.send("❌ E-mail nemá doménu @utb.cz. Byla ti přidělena role Impostor.")
                role = discord.utils.get(guild.roles, name="Impostor")
                if role:
                    await interaction.user.add_roles(role)
                return

            if email in BLACKLIST:
                await dm_channel.send("❌ Tento e-mail je zakázaný. Byla ti přidělena role Impostor.")
                role = discord.utils.get(guild.roles, name="Impostor")
                if role:
                    await interaction.user.add_roles(role)
                return

            code = ''.join(random.choices(string.digits, k=6))
            pending_verifications[interaction.user.id] = {
                "email": email,
                "code": code,
                "attempts": 0
            }

            async def remove_code_later(user_id):
                await asyncio.sleep(600)
                if user_id in pending_verifications:
                    del pending_verifications[user_id]

            bot.loop.create_task(remove_code_later(interaction.user.id))
            send_verification_code(email, code)
            await dm_channel.send(f"✅ Kód byl odeslán na {email}. Zadej ho sem do zprávy:")

            while True:
                code_msg = await bot.wait_for("message", timeout=300, check=check)
                entry = pending_verifications.get(interaction.user.id)
                if not entry:
                    await dm_channel.send("⏰ Kód vypršel. Začni ověření znovu.")
                    return

                entry["attempts"] += 1
                if code_msg.content.strip() == entry["code"]:
                    role_approved = discord.utils.get(guild.roles, name="Ověřen")
                    role_impostor = discord.utils.get(guild.roles, name="Impostor")

                    if role_approved:
                        await interaction.user.add_roles(role_approved)

                    if role_impostor and role_impostor in interaction.user.roles:
                        await interaction.user.remove_roles(role_impostor)

                    await dm_channel.send("✅ Ověření proběhlo úspěšně. Byla ti přidělena role Ověřen.")
                    del pending_verifications[interaction.user.id]
                    return
                elif entry["attempts"] >= 3:
                    await dm_channel.send("❌ Nesprávný kód. Byl(a) ti přidělena role Impostor.")
                    role = discord.utils.get(guild.roles, name="Impostor")
                    if role:
                        await interaction.user.add_roles(role)
                    del pending_verifications[interaction.user.id]
                    return
                else:
                    await dm_channel.send(f"❌ Nesprávný kód. Pokus {entry['attempts']} / 3")
        except Exception as e:
            await interaction.user.send("❌ Došlo k chybě během ověřování:\n" + str(e))

class ApplicantButton(Button):
    def __init__(self):
        super().__init__(label="Jsem uchazeč", style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild or discord.utils.get(bot.guilds)
        role = discord.utils.get(guild.roles, name="Uchazeč")
        if role:
            if role in interaction.user.roles:
                await interaction.response.send_message("Už máš roli Uchazeč.", ephemeral=True)
            else:
                await interaction.user.add_roles(role)
                await interaction.response.send_message("Byla ti přidělena role **Uchazeč**.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Role 'Uchazeč' nebyla nalezena na serveru.", ephemeral=True)

# === Reaction Role Menu pro národnost ===
@bot.command(name="reactionrole_narodnost")
@commands.has_permissions(administrator=True)
async def reactionrole(ctx):
    emoji_role_map = {
        "🇨🇿": "Česko",
        "🇸🇰": "Slovensko"
    }

    embed = discord.Embed(
        title="Zde si vyber svou národnost",
        description="Kliknutím na emoji si vybereš svou národnost",
        color=discord.Color.blue()
    )

    for emoji, role_name in emoji_role_map.items():
        embed.add_field(name=emoji, value=role_name, inline=True)

    message = await ctx.send(embed=embed)
    for emoji in emoji_role_map.keys():
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await ctx.send(f"Nemohu přidat emoji {emoji}, zkontroluj jeho platnost.")

    reaction_data[str(message.id)] = emoji_role_map
    with open(data_file, "w") as f:
        json.dump(reaction_data, f, indent=4)

    await ctx.send("Reaction role zpráva byla úspěšně nastavena.")


# === Reaction Role Menu pro typ studia ===
@bot.command(name="reactionrole_typ_studia")
@commands.has_permissions(administrator=True)
async def reactionrole(ctx):
    emoji_role_map = {
        "🇵": "Prezenční",
        "🇰": "Kombinované"
    }

    embed = discord.Embed(
        title="Zde si vyber svůj typ studia",
        description="Kliknutím na emoji si vybereš svůj typ studia",
        color=discord.Color.blue()
    )

    for emoji, role_name in emoji_role_map.items():
        embed.add_field(name=emoji, value=role_name, inline=True)

    message = await ctx.send(embed=embed)
    for emoji in emoji_role_map.keys():
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await ctx.send(f"Nemohu přidat emoji {emoji}, zkontroluj jeho platnost.")

    reaction_data[str(message.id)] = emoji_role_map
    with open(data_file, "w") as f:
        json.dump(reaction_data, f, indent=4)

    await ctx.send("Reaction role zpráva byla úspěšně nastavena.")


# === Reaction Role Menu pro obor ===
@bot.command(name="reactionrole_obor")
@commands.has_permissions(administrator=True)
async def reactionrole(ctx):
    emoji_role_map = {
        "🤖": "ISR",
        "🔧": "PA"
    }

    embed = discord.Embed(
        title="Zde si vyber svůj obor",
        description="Kliknutím na emoji si vybereš svůj obor",
        color=discord.Color.blue()
    )

    for emoji, role_name in emoji_role_map.items():
        embed.add_field(name=emoji, value=role_name, inline=True)

    message = await ctx.send(embed=embed)
    for emoji in emoji_role_map.keys():
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await ctx.send(f"Nemohu přidat emoji {emoji}, zkontroluj jeho platnost.")

    reaction_data[str(message.id)] = emoji_role_map
    with open(data_file, "w") as f:
        json.dump(reaction_data, f, indent=4)

    await ctx.send("Reaction role zpráva byla úspěšně nastavena.")


# === Reaction Role Menu pro ročník ===
@bot.command(name="reactionrole_rocnik")
@commands.has_permissions(administrator=True)
async def reactionrole(ctx):
    """
    Použití: !reactionrole_rocnik :one: Prvák :two: Druhák :three: Třeťák :four: Ing. Prvák :five: Ing. Druhák
    """
    emoji_role_map = {
        "1️⃣": "Prvák",
        "2️⃣": "Druhák",
        "3️⃣": "Třeťák",
        "4️⃣": "Ing. Prvák",
        "5️⃣": "Ing. Druhák"
    }

    embed = discord.Embed(
        title="Zde si vyber svůj ročník",
        description="Kliknutím na emoji si vybereš svůj ročník",
        color=discord.Color.blue()
    )

    for emoji, role_name in emoji_role_map.items():
        embed.add_field(name=emoji, value=role_name, inline=True)  # <== změněno na inline=True

    message = await ctx.send(embed=embed)

    for emoji in emoji_role_map.keys():
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await ctx.send(f"Nemohu přidat emoji {emoji}, zkontroluj jeho platnost.")

    reaction_data[str(message.id)] = emoji_role_map
    with open(data_file, "w") as f:
        json.dump(reaction_data, f, indent=4)

    await ctx.send("Reaction role zpráva byla úspěšně nastavena.")


# === Reaction Role Menu pro veterán ===
@bot.command(name="reactionrole_veteran")
@commands.has_permissions(administrator=True)
async def reactionrole(ctx):
    emoji_role_map = {
        "🎓": "Absolvent",
        "👑": "Doktorand"
    }

    embed = discord.Embed(
        title="Zde si vyber svou veteránskou hodnost",
        description="Kliknutím na emoji si vybereš svou veteránskou hodnost, roli absolventa si prosím zvolte až při úspešném ukončení studia a nepokračování na UTB,",
        color=discord.Color.blue()
    )

    for emoji, role_name in emoji_role_map.items():
        embed.add_field(name=emoji, value=role_name, inline=True)

    message = await ctx.send(embed=embed)
    for emoji in emoji_role_map.keys():
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException:
            await ctx.send(f"Nemohu přidat emoji {emoji}, zkontroluj jeho platnost.")

    reaction_data[str(message.id)] = emoji_role_map
    with open(data_file, "w") as f:
        json.dump(reaction_data, f, indent=4)

    await ctx.send("Reaction role zpráva byla úspěšně nastavena.")


@bot.event
async def on_ready():
    print(f"Přihlášen jako {bot.user}")
    for guild in bot.guilds:
        channel = guild.get_channel(VERIFICATION_CHANNEL_ID)
        if channel:
            try:
                # Najdi poslední zprávu od bota s embedem pro ověření
                async for msg in channel.history(limit=10):
                    if msg.author == bot.user and any(isinstance(e, discord.Embed) and "Ověření UTB účtu" in e.title for e in msg.embeds):
                        await msg.edit(view=VerifyButtonView())
                        print("✅ View pro ověřovací zprávu znovu připojena.")
                        break
                else:
                    # Pokud nebyla nalezena, vytvoř novou
                    embed = discord.Embed(
                        title="🎓 Ověření UTB účtu",
                        description=(
                            "Pro přístup k ostatním kanálům je potřeba ověřit svůj školní e-mail.\n\n"
                            "➡️ Klikni na tlačítko **Ověřit** níže. "
                            "Bot ti pošle zprávu do DM, kde zadáš svůj **@utb.cz** e-mail, na který ti následně přijde kód, který botu zadáš.\n\n"
                            "⚠️ **E-maily učitelů nejsou povoleny.**"
                        ),
                        color=discord.Color.blurple()
                    )
                    await channel.send(embed=embed, view=VerifyButtonView())
                    print("✅ Nová ověřovací zpráva odeslána.")
            except Exception as e:
                print(f"❌ Chyba při obnovování ověřovací zprávy: {e}")
        else:
            print("❌ Kanál s daným ID nebyl nalezen.")

    # === Synchronizace reakcí po restartu bota ===
    print("🔄 Spouštím synchronizaci reaction rolí...")
    role_channel_id = int(os.getenv("ROLE_CHANNEL_ID", "0"))
    if not role_channel_id:
        print("❌ ROLE_CHANNEL_ID není nastaven.")
        return

    for guild in bot.guilds:
        role_channel = guild.get_channel(role_channel_id)
        if not role_channel:
            print("❌ Role kanál nenalezen.")
            continue

        for msg_id, emoji_role_map in reaction_data.items():
            try:
                message = await role_channel.fetch_message(int(msg_id))
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                continue

            user_reactions = {}

            for reaction in message.reactions:
                emoji = str(reaction.emoji)
                if emoji not in emoji_role_map:
                    continue
                async for user in reaction.users():
                    if user.bot:
                        continue
                    if user.id not in user_reactions:
                        user_reactions[user.id] = []
                    user_reactions[user.id].append(emoji)

            for member in guild.members:
                # Uživatel má nějakou reakci v této zprávě
                emojis = user_reactions.get(member.id, [])

                # Najdi všechny role, které se vztahují k této zprávě
                roles_in_this_menu = [
                    discord.utils.get(guild.roles, name=role_name)
                    for role_name in emoji_role_map.values()
                ]

                # Role, které uživatel má z tohoto menu
                current_roles = [r for r in roles_in_this_menu if r and r in member.roles]

                # Vybraná emoji (naposledy přidaná, nebo žádná)
                selected_emoji = emojis[-1] if emojis else None
                selected_role = (
                    discord.utils.get(guild.roles, name=emoji_role_map[selected_emoji])
                    if selected_emoji else None
                )

                # Odeber všechny ostatní role z tohoto menu
                to_remove = [r for r in current_roles if r != selected_role]
                if to_remove:
                    await member.remove_roles(*to_remove)
                    print(f"🧹 Odebrány staré role {', '.join(r.name for r in to_remove)} uživateli {member.display_name}")

                # Přidej vybranou roli pokud chybí
                if selected_role and selected_role not in member.roles:
                    await member.add_roles(selected_role)
                    print(f"✅ Přidána role {selected_role.name} uživateli {member.display_name}")

                # Odebrání reakcí, které uživatel nemá mít
                if selected_emoji:
                    for emoji in emojis:
                        if emoji != selected_emoji:
                            for reaction in message.reactions:
                                if str(reaction.emoji) == emoji:
                                    try:
                                        await reaction.remove(member)
                                    except discord.HTTPException:
                                        pass

    print("✅ Synchronizace dokončena.")




       


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # Kontrola jen pro zprávy na serveru (ne DM)
    if isinstance(message.channel, discord.TextChannel):
        if message.channel.name == RESTRICTED_CHANNEL_NAME:
            if not message.attachments:
                try:
                    await message.delete()
                    await message.author.send(
                        f"Ahoj {message.author.name}, tvoje zpráva byla odstraněna, protože kanál **{RESTRICTED_CHANNEL_NAME}** slouží pouze k odesílání souborů."
                    )
                except discord.Forbidden:
                    print("⚠️ Nemám oprávnění smazat zprávu nebo poslat DM.")

    await bot.process_commands(message)

#radim code for role bot
@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return

    message_id = str(payload.message_id)
    if message_id in reaction_data:
        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return

        emoji = str(payload.emoji)
        if emoji in reaction_data[message_id]:
            role_name = reaction_data[message_id][emoji]
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                return

            member = guild.get_member(payload.user_id)
            if not member:
                return
            # Seznam roli ročník (podle tvého emoji_role_map)
            rocnik_roles = ["Prvák", "Druhák", "Třeťák", "Ing. Prvák", "Ing. Druhák"]
            veteran_roles = ["Absolvent", "Doktorand"]

            # 1) Pokud uživatel má roli Absolvent nebo Doktorand,
            #    nesmí si přidat žádnou roli z Ročník.
            if any(r in [role.name for role in member.roles] for r in veteran_roles):
                if role_name in rocnik_roles:
                    channel = guild.get_channel(payload.channel_id)
                    # Odebrání reakce uživatele - zamezit přidání role
                    message = await channel.fetch_message(payload.message_id)
                    for reaction in message.reactions:
                        if str(reaction.emoji) == emoji:
                            users = [u async for u in reaction.users()]
                            if member in users:
                                try:
                                    await reaction.remove(member)
                                except discord.HTTPException:
                                    pass
                    # Můžeš tu také poslat zprávu uživateli, že si nemůže zvolit roli ročníku
                    try:
                        await member.send("Nemůžeš si zvolit roli ročníku, protože máš roli Absolvent nebo Doktorand.")
                    except:
                        pass
                    return  # Ukončit dálší přidávání role

            # 2) Pokud si uživatel zvolí roli Absolvent nebo Doktorand,
            #    odeber mu všechny role z Ročník
            if role_name in veteran_roles:
                roles_to_remove = []
                for r_name in rocnik_roles:
                    r = discord.utils.get(guild.roles, name=r_name)
                    if r in member.roles:
                        roles_to_remove.append(r)
                if roles_to_remove:
                    await member.remove_roles(*roles_to_remove)

                    # Odebrání reakcí na ročníkové zprávě (reaction role zprávu ročník najdeme v reaction_data)
                    for msg_id, emoji_role_map in reaction_data.items():
                        # Jestli je to zpráva pro ročník - zkontrolujeme, jestli v emoji_role_map jsou ročníkové role
                        if any(role in rocnik_roles for role in emoji_role_map.values()):
                            channel = guild.get_channel(payload.channel_id)
                            if channel is None:
                                continue
                            try:
                                message = await channel.fetch_message(int(msg_id))
                            except:
                                continue
                            # Projdi reakce u zprávy
                            for reaction in message.reactions:
                                # Pokud reakce odpovídá některé roli ročníku, a uživatel ji má, odeber ji
                                if reaction.emoji in emoji_role_map:
                                    role_for_emoji = emoji_role_map[reaction.emoji]
                                    if role_for_emoji in rocnik_roles:
                                        users = [u async for u in reaction.users()]
                                        if member in users:
                                            try:
                                                await reaction.remove(member)
                                            except discord.HTTPException:
                                                pass

            # Odebrání všech ostatních rolí z tohoto menu
            roles_to_remove = []
            for other_emoji, other_role_name in reaction_data[message_id].items():
                if other_role_name != role_name:
                    other_role = discord.utils.get(guild.roles, name=other_role_name)
                    if other_role in member.roles:
                        roles_to_remove.append(other_role)
            if roles_to_remove:
                await member.remove_roles(*roles_to_remove)

            await member.add_roles(role)
            print(f"Přidána role {role_name} uživateli {member.display_name}.")

            # Odebrání ostatních reakcí uživatele na této zprávě
            channel = guild.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            for reaction in message.reactions:
                if str(reaction.emoji) != emoji:
                    users = [u async for u in reaction.users()]
                    for u in users:
                        if u.id == payload.user_id:
                            try:
                                await reaction.remove(u)
                            except discord.HTTPException:
                                pass


#radim code for role bot
@bot.event
async def on_raw_reaction_remove(payload):
    message_id = str(payload.message_id)
    if message_id in reaction_data:
        guild = bot.get_guild(payload.guild_id)
        if guild is None:
            return

        emoji = str(payload.emoji)
        if emoji in reaction_data[message_id]:
            role_name = reaction_data[message_id][emoji]
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                return

            member = guild.get_member(payload.user_id)
            if member:
                await member.remove_roles(role)
                print(f"Odebrána role {role_name} uživateli {member.display_name}.")




bot.run(TOKEN)
