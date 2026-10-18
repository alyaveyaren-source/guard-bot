import os
import sys
import subprocess
import time
import threading
import io
from collections import defaultdict
import datetime

class QuietWriter(io.StringIO):
    def write(self, x):
        pass

sys.stderr = QuietWriter()

try:
    import discord
    from discord import app_commands
    from discord.ext import commands
    from flask import Flask
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "discord.py", "flask"])
    import discord
    from discord import app_commands
    from discord.ext import commands
    from flask import Flask

# --- FLASK WEB SUNUCUSU (RENDER UYUMLU) ---
web_app = Flask('')

@web_app.route('/')
def home():
    return "Guard Bot v9 Ultimate 24/7 Aktif"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    try:
        web_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
    except Exception as e:
        print(f"Web server hatasi: {e}")

threading.Thread(target=run_web, daemon=True).start()

# --- BOT AYARLARI ---
BOT_TOKEN = "MTU2MTQwOTMxNzM2ODg5MzQ5Mg.GoEXUT.tduv5is-eBDVVmtaYMZd9sOdkY323dgrqF3NO0"
TARGET_GUILD_ID = 1558605340398845994
CONTROL_CHANNEL_ID = 1561422691527827476
AUTHORIZED_USERNAME = "flex.c0meback"

guard_settings = {
    "kanal_koruma": True,
    "rol_koruma": True,
    "url_koruma": True,
    "bot_koruma": True,
    "reklam_koruma": True,
    "kufur_koruma": True,
    "caps_koruma": True,
    "spam_koruma": True
}

whitelist = set()

def is_authorized(user, guild):
    return user == guild.owner or user.name.lower() == AUTHORIZED_USERNAME.lower()

def main():
    target_guild_id = TARGET_GUILD_ID
    control_channel_id = CONTROL_CHANNEL_ID

    intents = discord.Intents.default()
    intents.guilds = True
    intents.messages = True
    intents.message_content = True
    intents.members = True
    intents.moderation = True
    intents.bans = True
    intents.voice_states = True

    bot = commands.Bot(command_prefix=".", intents=intents)
    bot.remove_command("help")

    ALLOWED_ROLES = ["BOTLOADER", "Z1RVEDEYİZ", "JAZ", "J", "BOENQUE"]
    TARGET_GUILD = target_guild_id
    CONTROL_CHANNEL = control_channel_id
    
    guild_vanity_urls = {}
    auto_role_data = {}
    link_warnings = defaultdict(int)
    last_messages = {}

    async def strip_roles_and_ban(guild, user, reason):
        if is_authorized(user, guild) or user.bot or user.id in whitelist:
            return
        try:
            roles_to_remove = [role for role in user.roles if role.name != "@everyone" and role < guild.me.top_role]
            if roles_to_remove:
                await user.remove_roles(*roles_to_remove, reason=f"Guard: {reason}")
        except Exception:
            pass
        try:
            await guild.ban(user, reason=reason)
        except Exception:
            pass

    async def setup_private_system(guild):
        category_name = "GUARD ULTIMATE LOGS"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, view_channel=False),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True)
        }
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            try:
                category = await guild.create_category(category_name, overwrites=overwrites)
            except Exception:
                pass

        log_names = [
            "ban-log", "kick-log", "timeout-log", "kanal-log", "rol-log", 
            "bot-log", "url-log", "ses-log", "mesaj-log", "ayar-log", "uye-log"
        ]
        for name in log_names:
            channel = discord.utils.get(guild.text_channels, name=name)
            if not channel and category:
                try:
                    await guild.create_text_channel(name, category=category, overwrites=overwrites)
                except Exception:
                    pass

    async def send_log(guild, channel_name, message):
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel:
            try:
                await channel.send(message)
            except Exception:
                pass

    def check_permissions(author):
        if is_authorized(author, author.guild) or author.guild_permissions.administrator or author.id in whitelist:
            return True
        user_roles = [role.name for role in author.roles]
        return any(r in ALLOWED_ROLES for r in user_roles)

    @bot.event
    async def on_ready():
        print(f"\n[BASARILI] Guard v9 Ultimate Aktif: {bot.user.name}")
        for guild in bot.guilds:
            if guild.id != TARGET_GUILD:
                try:
                    await guild.leave()
                except Exception:
                    pass
            else:
                await setup_private_system(guild)
                try:
                    vanity = await guild.vanity_invite()
                    if vanity:
                        guild_vanity_urls[guild.id] = vanity.code
                except Exception:
                    pass

        ctrl_channel = bot.get_channel(CONTROL_CHANNEL)
        if ctrl_channel:
            try:
                await ctrl_channel.send("AKTİF")
            except Exception:
                pass

        try:
            synced = await bot.tree.sync()
            print(f"[SLASH] {len(synced)} komut senkronize edildi.")
        except Exception as e:
            print(f"Hata: {e}")

        await bot.change_presence(activity=discord.Game(name="Guard v9 | Tac & flex.c0meback Yonetim"))

    @bot.event
    async def on_guild_join(guild):
        if guild.id != TARGET_GUILD:
            try:
                await guild.leave()
            except Exception:
                pass

    @bot.event
    async def on_member_join(member):
        if member.guild.id != TARGET_GUILD:
            return

        if member.bot and guard_settings["bot_koruma"]:
            async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                adder = entry.user
                if not is_authorized(adder, member.guild) and adder.id not in whitelist:
                    try:
                        await member.guild.ban(member, reason="Izinsiz bot")
                        await strip_roles_and_ban(member.guild, adder, reason="Izinsiz bot ekleme")
                        await send_log(member.guild, "bot-log", f"[BOT ENGEL] {member} eklendi. Ekleyen {adder} banlandi.")
                    except Exception:
                        pass
                break
            return

        await send_log(member.guild, "uye-log", f"[KATILDI] {member} sunucuya katildi.")
        role_id = auto_role_data.get(member.guild.id)
        if role_id:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role, reason="Otorol")
                except Exception:
                    pass

    @bot.event
    async def on_guild_update(before, after):
        if after.id != TARGET_GUILD or not guard_settings["url_koruma"]:
            return
        if before.vanity_url_code != after.vanity_url_code:
            old_code = guild_vanity_urls.get(after.id, before.vanity_url_code)
            async for entry in after.audit_logs(limit=1, action=discord.AuditLogAction.guild_update):
                user = entry.user
                if not is_authorized(user, after) and user.id not in whitelist and not user.bot:
                    await strip_roles_and_ban(after, user, reason="Izinsiz URL degisikligi")
                    if old_code:
                        try:
                            await after.edit(vanity_code=old_code, reason="URL geri alindi")
                            await send_log(after, "url-log", f"[ANLIK URL KURTARMA] {user} URL degistirdi, banlandi ve URL geri alindi.")
                        except Exception:
                            pass
                break

    @bot.event
    async def on_guild_channel_create(channel):
        if channel.guild.id != TARGET_GUILD or not guard_settings["kanal_koruma"]:
            return
        guild = channel.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            user = entry.user
            if not is_authorized(user, guild) and user.id not in whitelist and not user.bot:
                try:
                    await channel.delete()
                    await strip_roles_and_ban(guild, user, reason="Izinsiz kanal")
                    await send_log(guild, "kanal-log", f"[ANLIK KANAL KORUMA] {user} kanal acti, banlandi ve kanal silindi.")
                except Exception:
                    pass
            break

    @bot.event
    async def on_guild_channel_delete(channel):
        if channel.guild.id != TARGET_GUILD or not guard_settings["kanal_koruma"]:
            return
        guild = channel.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            user = entry.user
            if not is_authorized(user, guild) and user.id not in whitelist and not user.bot:
                try:
                    if isinstance(channel, discord.TextChannel):
                        await guild.create_text_channel(name=channel.name, category=channel.category)
                    elif isinstance(channel, discord.VoiceChannel):
                        await guild.create_voice_channel(name=channel.name, category=channel.category)
                    await strip_roles_and_ban(guild, user, reason="Izinsiz kanal silme")
                    await send_log(guild, "kanal-log", f"[ANLIK KANAL KORUMA] {user} kanal sildi, geri acildi ve banlandi.")
                except Exception:
                    pass
            break

    @bot.event
    async def on_guild_role_create(role):
        if role.guild.id != TARGET_GUILD or not guard_settings["rol_koruma"]:
            return
        guild = role.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            user = entry.user
            if not is_authorized(user, guild) and user.id not in whitelist and not user.bot:
                try:
                    await role.delete()
                    await strip_roles_and_ban(guild, user, reason="Izinsiz rol")
                    await send_log(guild, "rol-log", f"[ANLIK ROL KORUMA] {user} rol acti, silindi ve banlandi.")
                except Exception:
                    pass
            break

    @bot.event
    async def on_guild_role_delete(role):
        if role.guild.id != TARGET_GUILD or not guard_settings["rol_koruma"]:
            return
        guild = role.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            user = entry.user
            if not is_authorized(user, guild) and user.id not in whitelist and not user.bot:
                try:
                    await strip_roles_and_ban(guild, user, reason="Izinsiz rol silme")
                    await send_log(guild, "rol-log", f"[ANLIK ROL KORUMA] {user} rol sildi ve banlandi.")
                except Exception:
                    pass
            break

    class AutoRoleSelect(discord.ui.RoleSelect):
        def __init__(self):
            super().__init__(placeholder="Katilan uyelere verilecek Otorol secin...", min_values=1, max_values=1)

        async def callback(self, interaction: discord.Interaction):
            if not is_authorized(interaction.user, interaction.guild):
                await interaction.response.send_message("Bu ayari sadece Tac Sahibi veya flex.c0meback degistirebilir!", ephemeral=True)
                return
            selected_role = self.values[0]
            auto_role_data[interaction.guild.id] = selected_role.id
            await interaction.response.send_message(f"Otorol ayarlandi: {selected_role.name}", ephemeral=True)

    class ControlPanelView(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=None)
            self.add_item(AutoRoleSelect())

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if not is_authorized(interaction.user, interaction.guild):
                await interaction.response.send_message("Bu paneli ve ayarlarini sadece Tac Sahibi veya flex.c0meback kullanabilir.", ephemeral=True)
                return False
            return True

        @discord.ui.button(label="Kanal Koruma", style=discord.ButtonStyle.blurple, row=0)
        async def toggle_kanal(self, interaction: discord.Interaction, button: discord.ui.Button):
            guard_settings["kanal_koruma"] = not guard_settings["kanal_koruma"]
            status = "Aktif" if guard_settings["kanal_koruma"] else "Kapali"
            button.style = discord.ButtonStyle.green if guard_settings["kanal_koruma"] else discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"Kanal Koruma: {status}", ephemeral=True)

        @discord.ui.button(label="Rol Koruma", style=discord.ButtonStyle.blurple, row=0)
        async def toggle_rol(self, interaction: discord.Interaction, button: discord.ui.Button):
            guard_settings["rol_koruma"] = not guard_settings["rol_koruma"]
            status = "Aktif" if guard_settings["rol_koruma"] else "Kapali"
            button.style = discord.ButtonStyle.green if guard_settings["rol_koruma"] else discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"Rol Koruma: {status}", ephemeral=True)

        @discord.ui.button(label="URL Koruma", style=discord.ButtonStyle.blurple, row=0)
        async def toggle_url(self, interaction: discord.Interaction, button: discord.ui.Button):
            guard_settings["url_koruma"] = not guard_settings["url_koruma"]
            status = "Aktif" if guard_settings["url_koruma"] else "Kapali"
            button.style = discord.ButtonStyle.green if guard_settings["url_koruma"] else discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"URL Koruma: {status}", ephemeral=True)

        @discord.ui.button(label="Anti-Bot", style=discord.ButtonStyle.blurple, row=1)
        async def toggle_bot(self, interaction: discord.Interaction, button: discord.ui.Button):
            guard_settings["bot_koruma"] = not guard_settings["bot_koruma"]
            status = "Aktif" if guard_settings["bot_koruma"] else "Kapali"
            button.style = discord.ButtonStyle.green if guard_settings["bot_koruma"] else discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"Anti-Bot: {status}", ephemeral=True)

        @discord.ui.button(label="Reklam Engeli", style=discord.ButtonStyle.blurple, row=1)
        async def toggle_reklam(self, interaction: discord.Interaction, button: discord.ui.Button):
            guard_settings["reklam_koruma"] = not guard_settings["reklam_koruma"]
            status = "Aktif" if guard_settings["reklam_koruma"] else "Kapali"
            button.style = discord.ButtonStyle.green if guard_settings["reklam_koruma"] else discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"Reklam Engeli: {status}", ephemeral=True)

        @discord.ui.button(label="Kufur Engeli", style=discord.ButtonStyle.blurple, row=1)
        async def toggle_kufur(self, interaction: discord.Interaction, button: discord.ui.Button):
            guard_settings["kufur_koruma"] = not guard_settings["kufur_koruma"]
            status = "Aktif" if guard_settings["kufur_koruma"] else "Kapali"
            button.style = discord.ButtonStyle.green if guard_settings["kufur_koruma"] else discord.ButtonStyle.red
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"Kufur Engeli: {status}", ephemeral=True)

    @bot.event
    async def on_message(message):
        if not message.guild or message.guild.id != TARGET_GUILD or message.author.bot:
            return

        content_lower = message.content.lower()

        if content_lower == ".panel":
            if message.channel.id != CONTROL_CHANNEL:
                await message.delete()
                return
            
            if not is_authorized(message.author, message.guild):
                await message.channel.send(f"{message.author.mention}, bu paneli sadece Tac Hesabi veya flex.c0meback acabilir.", delete_after=10)
                try:
                    await message.delete()
                except Exception:
                    pass
                return

            embed = discord.Embed(
                title="GUARD v9 - Yonetim Paneli",
                description="Aşağıdaki butonlari sadece Tac Hesabi veya flex.c0meback kullanabilir.",
                color=discord.Color.dark_gray()
            )
            embed.add_field(name="Kanal Koruma", value="Aktif" if guard_settings["kanal_koruma"] else "Kapali", inline=True)
            embed.add_field(name="Rol Koruma", value="Aktif" if guard_settings["rol_koruma"] else "Kapali", inline=True)
            embed.add_field(name="URL Koruma", value="Aktif" if guard_settings["url_koruma"] else "Kapali", inline=True)
            embed.add_field(name="Anti-Bot", value="Aktif" if guard_settings["bot_koruma"] else "Kapali", inline=True)
            embed.add_field(name="Reklam Engeli", value="Aktif" if guard_settings["reklam_koruma"] else "Kapali", inline=True)
            embed.add_field(name="Kufur Engeli", value="Aktif" if guard_settings["kufur_koruma"] else "Kapali", inline=True)
            
            curr_role = auto_role_data.get(message.guild.id)
            role_text = f"<@&{curr_role}>" if curr_role else "Ayarlanmadi"
            embed.add_field(name="Mevcut Otorol", value=role_text, inline=False)

            await message.channel.send(embed=embed, view=ControlPanelView())
            return

        if content_lower == ".komutlar":
            if message.channel.id != CONTROL_CHANNEL:
                await message.delete()
                return

            embed = discord.Embed(
                title="GUARD v9 ULTIMATE - GELISMIS KOMUT LISTESI",
                description="Sunucuda aktif olan tum slash komutlari:",
                color=discord.Color.dark_gray()
            )
            embed.add_field(name="/ban [kullanici] [sebep]", value="Kullaniciyi sunucudan yasaklar.", inline=False)
            embed.add_field(name="/unban [id]", value="Kullanicinin yasaklamasini kaldirir.", inline=False)
            embed.add_field(name="/kick [kullanici] [sebep]", value="Kullaniciyi sunucudan atar.", inline=False)
            embed.add_field(name="/mute [kullanici] [dakika] [sebep]", value="Kullaniciya timeout atar.", inline=False)
            embed.add_field(name="/unmute [kullanici]", value="Kullanicinin timeout cezasini kaldirir.", inline=False)
            embed.add_field(name="/kilitle", value="Bulunulan kanali mesaja kapatir.", inline=False)
            embed.add_field(name="/kilit-ac", value="Kilitli kanali mesaja yeniden acar.", inline=False)
            embed.add_field(name="/sil [adet]", value="Belirtilen sayida mesaji temizler.", inline=False)
            embed.add_field(name="/yavas-mod [saniye]", value="Kanala yavas mod suresi ekler.", inline=False)
            embed.add_field(name="/rolver [kullanici] [rol]", value="Kullaniciya rol ekler.", inline=False)
            embed.add_field(name="/rolal [kullanici] [rol]", value="Kullanicindan rol alir.", inline=False)
            embed.add_field(name="/toplu-rolver [rol]", value="Sunucudaki herkese ilgili rolü verir.", inline=False)
            embed.add_field(name="/toplu-rolal [rol]", value="Sunucudaki herkesten ilgili rolü alir.", inline=False)
            embed.add_field(name="/duyuru [baslik] [mesaj]", value="Kanalda profesyonel embed duyuru yapar.", inline=False)
            embed.add_field(name="/sunucu-bilgi", value="Sunucu hakkinda detayli istatistik sunar.", inline=False)
            embed.add_field(name="/kullanici-bilgi [kullanici]", value="Uye hakkinda detayli bilgi verir.", inline=False)
            embed.add_field(name="/whitelist-ekle [kullanici]", value="Kullaniciyi koruma istisnasina alir.", inline=False)
            embed.add_field(name="/whitelist-cikar [kullanici]", value="Kullaniciyi guvenli listeden cikarir.", inline=False)
            embed.add_field(name="/ping", value="Botun gecikme suresini gosterir.", inline=False)
            embed.set_footer(text="Guard v9 Ultimate - Tam Guvenlik & Moderasyon Seti")

            await message.channel.send(embed=embed)
            return

        if not is_authorized(message.author, message.guild) and message.author.id not in whitelist:
            author_id = message.author.id
            last_msg_text, count = last_messages.get(author_id, ("", 0))
            
            if last_msg_text == message.content:
                count += 1
            else:
                count = 1
            
            last_messages[author_id] = (message.content, count)

            if count >= 3:
                try:
                    await message.delete()
                except Exception:
                    pass
                try:
                    await message.author.timeout(datetime.timedelta(minutes=5), reason="Ayni mesaji arka arkaya flood yapma")
                    await message.channel.send(f"{message.author.mention}, arka arkaya ayni mesaji yazdigin icin 5 dakika susturuldun.", delete_after=10)
                    await send_log(message.guild, "timeout-log", f"[FLOOD TIMEOUT] {message.author} ayni mesaji 3 kez attigi icin susturuldu.")
                    last_messages[author_id] = ("", 0)
                except Exception:
                    pass
                return

            is_link = "discord.gg/" in content_lower or "http://" in content_lower or "https://" in content_lower or "www." in content_lower
            if guard_settings["reklam_koruma"] and is_link:
                try:
                    await message.delete()
                except Exception:
                    pass
                user_id = message.author.id
                link_warnings[user_id] += 1
                warn_count = link_warnings[user_id]
                if warn_count < 3:
                    try:
                        await message.author.timeout(datetime.timedelta(minutes=5), reason="Reklam")
                        await message.channel.send(f"{message.author.mention}, reklam yasak. ({warn_count}/3)", delete_after=10)
                        await send_log(message.guild, "timeout-log", f"[TIMEOUT] {message.author} reklam nedeniyle susturuldu ({warn_count}/3)")
                    except Exception:
                        pass
                else:
                    try:
                        await message.guild.ban(message.author, reason="3 kez reklam")
                        await send_log(message.guild, "ban-log", f"[REKLAM BAN] {message.author} 3 kez reklam yaptigi icin banlandi.")
                        link_warnings[user_id] = 0
                    except Exception:
                        pass
                return

        await bot.process_commands(message)

    @bot.tree.command(name="ban", description="Kullaniciyi sunucudan banlar.")
    async def slash_ban(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        try:
            await kullanici.ban(reason=sebep)
            await interaction.response.send_message(f"{kullanici.mention} banlandi. Sebep: {sebep}", ephemeral=True)
            await send_log(interaction.guild, "ban-log", f"[BAN] {kullanici} | Yetkili: {interaction.user} | Sebep: {sebep}")
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @bot.tree.command(name="unban", description="Kullanicinin yasaklamasini ID uzerinden kaldirir.")
    async def slash_unban(interaction: discord.Interaction, kullanici_id: str):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        try:
            user = await bot.fetch_user(int(kullanici_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"{user.name} kullanicisinin yasaklamasi kaldirildi.", ephemeral=True)
            await send_log(interaction.guild, "ban-log", f"[UNBAN] {user.name} yasagı kaldirildi | Yetkili: {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @bot.tree.command(name="kick", description="Kullaniciyi sunucudan atar.")
    async def slash_kick(interaction: discord.Interaction, kullanici: discord.Member, sebep: str = "Sebep belirtilmedi"):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        try:
            await kullanici.kick(reason=sebep)
            await interaction.response.send_message(f"{kullanici.mention} sunucudan atildi. Sebep: {sebep}", ephemeral=True)
            await send_log(interaction.guild, "kick-log", f"[KICK] {kullanici} atildi | Yetkili: {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @bot.tree.command(name="mute", description="Kullaniciya timeout (susturma) uygular.")
    async def slash_mute(interaction: discord.Interaction, kullanici: discord.Member, dakika: int, sebep: str = "Sebep belirtilmedi"):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        try:
            duration = datetime.timedelta(minutes=dakika)
            await kullanici.timeout(duration, reason=sebep)
            await interaction.response.send_message(f"{kullanici.mention} {dakika} dakika susturuldu.", ephemeral=True)
            await send_log(interaction.guild, "timeout-log", f"[MUTE] {kullanici} {dakika} dk susturuldu | Yetkili: {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @bot.tree.command(name="unmute", description="Kullanicinin timeout cezasini kaldirir.")
    async def slash_unmute(interaction: discord.Interaction, kullanici: discord.Member):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        try:
            await kullanici.timeout(None)
            await interaction.response.send_message(f"{kullanici.mention} kullanicisinin susturmasi kaldirildi.", ephemeral=True)
            await send_log(interaction.guild, "timeout-log", f"[UNMUTE] {kullanici} susturmasi kaldirildi | Yetkili: {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @bot.tree.command(name="kilitle", description="Kanali varsayilan üyelere mesaja kapatir.")
    async def slash_kilitle(interaction: discord.Interaction):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        channel = interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = False
        try:
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            await interaction.response.send_message("Kanal mesaja kilitlendi.", ephemeral=True)
            await send_log(interaction.guild, "kanal-log", f"[KANAL KILIT] {channel.name} kilitlendi | Yetkili: {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @bot.tree.command(name="kilit-ac", description="Kilitli kanali mesaja tekrar acar.")
    async def slash_kilit_ac(interaction: discord.Interaction):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        channel = interaction.channel
        overwrite = channel.overwrites_for(interaction.guild.default_role)
        overwrite.send_messages = True
        try:
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrite)
            await interaction.response.send_message("Kanal kilidi acildi.", ephemeral=True)
            await send_log(interaction.guild, "kanal-log", f"[KANAL KILIT ACILDI] {channel.name} kilidi acildi | Yetkili: {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @bot.tree.command(name="sil", description="Belirtilen miktarda mesaji kanaldan siler.")
    async def slash_sil(interaction: discord.Interaction, adet: int):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        try:
            deleted = await interaction.channel.purge(limit=adet)
            await interaction.response.send_message(f"{len(deleted)} mesaj temizlendi.", ephemeral=True)
            await send_log(interaction.guild, "mesaj-log", f"[SIL] {interaction.channel.name} kanalinda {len(deleted)} mesaj silindi | Yetkili: {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @bot.tree.command(name="yavas-mod", description="Kanaldaki mesaj gonderme yavas mod suresini ayarlar.")
    async def slash_yavas_mod(interaction: discord.Interaction, saniye: int):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        try:
            await interaction.channel.edit(slowmode_delay=saniye)
            await interaction.response.send_message(f"Yavas mod {saniye} saniye olarak ayarlandi.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @bot.tree.command(name="rolver", description="Kullaniciya rol ekler.")
    async def slash_rolver(interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        try:
            await kullanici.add_roles(rol)
            await interaction.response.send_message(f"{kullanici.mention} kullanicisina {rol.name} rolu verildi.", ephemeral=True)
            await send_log(interaction.guild, "rol-log", f"[ROL VER] {kullanici} -> {rol.name} | Yetkili: {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @bot.tree.command(name="rolal", description="Kullanicidan rol alir.")
    async def slash_rolal(interaction: discord.Interaction, kullanici: discord.Member, rol: discord.Role):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        try:
            await kullanici.remove_roles(rol)
            await interaction.response.send_message(f"{kullanici.mention} kullanicisindan {rol.name} rolu alindi.", ephemeral=True)
            await send_log(interaction.guild, "rol-log", f"[ROL AL] {kullanici} <- {rol.name} | Yetkili: {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(f"Hata: {e}", ephemeral=True)

    @bot.tree.command(name="toplu-rolver", description="Sunucudaki insan üyelere toplu rol verir.")
    async def slash_toplu_rolver(interaction: discord.Interaction, rol: discord.Role):
        if interaction.guild.id != TARGET_GUILD or not is_authorized(interaction.user, interaction.guild):
            await interaction.response.send_message("Bu komut sadece Tac Sahibi veya flex.c0meback tarafindan kullanilabilir!", ephemeral=True)
            return
        await interaction.response.send_message("Toplu rol verme islemi baslatildi...", ephemeral=True)
        count = 0
        for member in interaction.guild.members:
            if not member.bot and rol not in member.roles:
                try:
                    await member.add_roles(rol)
                    count += 1
                except Exception:
                    pass
        await send_log(interaction.guild, "rol-log", f"[TOPLU ROL VER] {count} kisiye {rol.name} rolu verildi.")

    @bot.tree.command(name="toplu-rolal", description="Sunucudaki tum üyelerden belirtilen rolü alir.")
    async def slash_toplu_rolal(interaction: discord.Interaction, rol: discord.Role):
        if interaction.guild.id != TARGET_GUILD or not is_authorized(interaction.user, interaction.guild):
            await interaction.response.send_message("Bu komut sadece Tac Sahibi veya flex.c0meback tarafindan kullanilabilir!", ephemeral=True)
            return
        await interaction.response.send_message("Toplu rol alma islemi baslatildi...", ephemeral=True)
        count = 0
        for member in interaction.guild.members:
            if rol in member.roles:
                try:
                    await member.remove_roles(rol)
                    count += 1
                except Exception:
                    pass
        await send_log(interaction.guild, "rol-log", f"[TOPLU ROL AL] {count} kisiden {rol.name} rolu alindi.")

    @bot.tree.command(name="duyuru", description="Embed formatinda ciddi duyuru metni yayinlar.")
    async def slash_duyuru(interaction: discord.Interaction, baslik: str, mesaj: str):
        if interaction.guild.id != TARGET_GUILD or not check_permissions(interaction.user):
            await interaction.response.send_message("Yetkiniz yetersiz!", ephemeral=True)
            return
        embed = discord.Embed(title=baslik, description=mesaj, color=discord.Color.dark_gray())
        embed.set_footer(text=f"Yayinlayan: {interaction.user.display_name}")
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("Duyuru gonderildi.", ephemeral=True)

    @bot.tree.command(name="sunucu-bilgi", description="Sunucu hakkinda genel bilgileri sunar.")
    async def slash_sunucu_bilgi(interaction: discord.Interaction):
        guild = interaction.guild
        embed = discord.Embed(title=f"{guild.name} - Sunucu Bilgileri", color=discord.Color.dark_gray())
        embed.add_field(name="Sunucu Sahibi", value=f"{guild.owner}", inline=True)
        embed.add_field(name="Uye Sayisi", value=f"{guild.member_count}", inline=True)
        embed.add_field(name="Rol Sayisi", value=f"{len(guild.roles)}", inline=True)
        embed.add_field(name="Kanal Sayisi", value=f"{len(guild.channels)}", inline=True)
        embed.add_field(name="Olusturulma Tarihi", value=guild.created_at.strftime("%d/%m/%Y"), inline=False)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="kullanici-bilgi", description="Secilen uye hakkinda bilgi verir.")
    async def slash_kullanici_bilgi(interaction: discord.Interaction, kullanici: discord.Member):
        embed = discord.Embed(title=f"{kullanici.name} - Uye Bilgisi", color=discord.Color.dark_gray())
        embed.add_field(name="ID", value=f"{kullanici.id}", inline=True)
        embed.add_field(name="Takma Ad", value=f"{kullanici.display_name}", inline=True)
        embed.add_field(name="Sunucuya Katilis", value=kullanici.joined_at.strftime("%d/%m/%Y"), inline=False)
        embed.add_field(name="Hesap Acilis", value=kullanici.created_at.strftime("%d/%m/%Y"), inline=False)
        await interaction.response.send_message(embed=embed)

    @bot.tree.command(name="whitelist-ekle", description="Kullaniciyi koruma istisnasina (whitelist) ekler.")
    async def slash_wl_ekle(interaction: discord.Interaction, kullanici: discord.Member):
        if interaction.guild.id != TARGET_GUILD or not is_authorized(interaction.user, interaction.guild):
            await interaction.response.send_message("Sadece Tac Sahibi veya flex.c0meback kullanabilir!", ephemeral=True)
            return
        whitelist.add(kullanici.id)
        await interaction.response.send_message(f"{kullanici.mention} guvenli listeye (whitelist) eklendi.", ephemeral=True)

    @bot.tree.command(name="whitelist-cikar", description="Kullaniciyi guvenli listeden cikarir.")
    async def slash_wl_cikar(interaction: discord.Interaction, kullanici: discord.Member):
        if interaction.guild.id != TARGET_GUILD or not is_authorized(interaction.user, interaction.guild):
            await interaction.response.send_message("Sadece Tac Sahibi veya flex.c0meback kullanabilir!", ephemeral=True)
            return
        whitelist.discard(kullanici.id)
        await interaction.response.send_message(f"{kullanici.mention} guvenli listeden cikarildi.", ephemeral=True)

    @bot.tree.command(name="ping", description="Botun gecikme suresini gosterir.")
    async def slash_ping(interaction: discord.Interaction):
        await interaction.response.send_message(f"Bot Gecikmesi: {round(bot.latency * 1000)}ms", ephemeral=True)

    bot.run(BOT_TOKEN)

if __name__ == "__main__":
    main()
