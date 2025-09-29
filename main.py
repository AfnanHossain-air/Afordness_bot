import discord
from discord.ext import commands
from discord.ui import View, Modal, TextInput
import traceback
import re

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ========================
# Event
# ========================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

# ========================
# Forum Post Copier
# ========================
@bot.command()
async def copy_posts(ctx, source_channel_id: int, target_channel_id: int):
    """Copy all posts (threads) from a forum channel to another forum channel"""
    source_channel = bot.get_channel(source_channel_id)
    target_channel = bot.get_channel(target_channel_id)

    if not isinstance(source_channel, discord.ForumChannel):
        await ctx.send("❌ Source channel must be a ForumChannel.")
        return
    if not isinstance(target_channel, discord.ForumChannel):
        await ctx.send("❌ Target channel must be a ForumChannel.")
        return

    await ctx.send(f"⚡ Copying all posts from **{source_channel.name}**...")

    async for thread in source_channel.threads:
        new_thread = await target_channel.create_thread(
            name=thread.name,
            content="📌 Copied post",
        )

        async for msg in thread.history(limit=None, oldest_first=True):
            if msg.content:
                await new_thread.send(msg.content)
            for att in msg.attachments:
                await new_thread.send(att.url)
            for emb in msg.embeds:
                await new_thread.send(embed=emb)

    await ctx.send("✅ Successfully copied all posts.")

# ========================
# Message Copy with Edit Modal
# ========================
class EditEmbedModal(Modal):
    def __init__(self, embed: discord.Embed, target_thread: discord.Thread):
        super().__init__(title="Edit Embed Before Sending")
        self.embed = embed
        self.target_thread = target_thread

        self.title_input = TextInput(
            label="Title",
            default=embed.title or "",
            required=False
        )
        self.description_input = TextInput(
            label="Description",
            default=embed.description or "",
            style=discord.TextStyle.paragraph,
            required=False
        )
        self.footer_input = TextInput(
            label="Footer",
            default=(embed.footer.text if embed.footer else ""),
            required=False
        )

        self.add_item(self.title_input)
        self.add_item(self.description_input)
        self.add_item(self.footer_input)

    async def on_submit(self, interaction: discord.Interaction):
        new_embed = discord.Embed(
            title=self.title_input.value,
            description=self.description_input.value,
            color=self.embed.color or discord.Color.blurple()
        )
        if self.footer_input.value:
            new_embed.set_footer(text=self.footer_input.value)

        await self.target_thread.send(embed=new_embed)
        await interaction.response.send_message("✅ Edited embed sent!", ephemeral=True)

class CopyControlView(View):
    def __init__(self, msg: discord.Message, target_thread: discord.Thread):
        super().__init__(timeout=None)
        self.msg = msg
        self.target_thread = target_thread

    @discord.ui.button(label="Edit Message", style=discord.ButtonStyle.primary)
    async def edit_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.msg.embeds:
            embed = self.msg.embeds[0]
            modal = EditEmbedModal(embed, self.target_thread)
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("⚠️ No embed found in this message.", ephemeral=True)

    @discord.ui.button(label="Send Message", style=discord.ButtonStyle.success)
    async def send_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.msg.content:
            await self.target_thread.send(self.msg.content)
        for attachment in self.msg.attachments:
            await self.target_thread.send(attachment.url)
        for embed in self.msg.embeds:
            await self.target_thread.send(embed=embed)

        await interaction.response.send_message("✅ Message sent!", ephemeral=True)

@bot.command()
async def copy_msg(ctx, target_thread_id: int):
    """Copy the most recent bot message with edit option"""
    if ctx.channel.type != discord.ChannelType.public_thread:
        await ctx.send("⚠️ You must run this command inside a forum thread.")
        return

    target_thread = bot.get_channel(target_thread_id)
    if not isinstance(target_thread, discord.Thread):
        await ctx.send("⚠️ Target thread not found or invalid ID.")
        return

    async for msg in ctx.channel.history(limit=10, oldest_first=False):
        if msg.author.bot and msg.id != ctx.message.id:
            view = CopyControlView(msg, target_thread)
            await ctx.send(f"⚙️ Choose what to do with the last bot message from **{msg.author.display_name}**:", view=view)
            return

    await ctx.send("⚠️ No bot message found in recent history.")

# ========================
# Channel Log Exporter
# ========================
@bot.command(name="copy_logs")
async def copy_logs(ctx, filename: str = "messages"):
    try:
        messages = []
        custom_emoji_regex = re.compile(r'<a?:([a-zA-Z0-9_]+):([0-9]+)>')

        async for msg in ctx.channel.history(limit=None, oldest_first=True):
            timestamp = msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
            avatar_url = msg.author.avatar.url if msg.author.avatar else "https://cdn.discordapp.com/embed/avatars/0.png"
            content = msg.content.replace("<", "&lt;").replace(">", "&gt;")

            def replace_emoji(match):
                emoji_id = int(match.group(2))
                emoji = bot.get_emoji(emoji_id)
                if emoji:
                    return f'<img src="{emoji.url}" alt="{match.group(1)}" style="width:22px; height:22px;">'
                return match.group(0)

            content = custom_emoji_regex.sub(replace_emoji, content)

            attachments_html = ""
            if msg.attachments:
                for att in msg.attachments:
                    if att.content_type and "image" in att.content_type:
                        attachments_html += f'<br><img src="{att.url}" style="max-width:400px;">'
                    else:
                        attachments_html += f'<br><a href="{att.url}">📎 {att.filename}</a>'

            embeds_html = ""
            for emb in msg.embeds:
                emb_dict = emb.to_dict()
                emb_title = emb_dict.get("title", "")
                emb_desc = emb_dict.get("description", "")
                embeds_html += f"""
                <div style="border-left:4px solid #5865F2; padding:6px; margin:4px 0; background:#f5f5f5;">
                    <b>{emb_title}</b><br>{emb_desc}
                </div>
                """

            messages.append(
                f"""
                <div style="margin:8px 0; display:flex; align-items:flex-start;">
                    <img src="{avatar_url}" width="32" height="32" style="border-radius:50%; margin-right:8px;">
                    <div>
                        <b>{msg.author}</b> <span style="color:gray; font-size:12px;">[{timestamp}]</span><br>
                        {content}{attachments_html}{embeds_html}
                    </div>
                </div>
                """
            )

        if not messages:
            await ctx.send("⚠️ No messages found in this channel.")
            return

        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Channel Log - {ctx.channel.name}</title>
            <style>
                body {{ font-family:Arial, sans-serif; }}
                img.emoji {{ height: 1.2em; vertical-align: middle; }}
            </style>
        </head>
        <body>
            <h2>Messages from #{ctx.channel.name}</h2>
            {''.join(messages)}
        </body>
        </html>
        """

        safe_filename = f"{filename}.html"
        with open(safe_filename, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"✅ Successfully copied messages to {safe_filename}")
        await ctx.send("✅ Successfully copied channel messages.")

    except Exception as e:
        error_text = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print(error_text)
        await ctx.send("❌ Failed to copy channel messages. Check bot permissions.")

# ========================
# Run Bot
# ========================
bot.run("YOUR_BOT_TOKEN_HERE")