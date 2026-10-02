import discord
from discord.ext import commands
import os
import io
import random
from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv

# Load the .env file for local testing
load_dotenv()

# --- CONFIGURATIONS ---
SH_LOG_ID = 1555548732341227520
SH_WELCOME_ID = 1555524708672475187
SH_GOODBYE_ID = 1555524784475996252
SH_RULES_ID = 1555556556416749649
SH_BIDDERS_ROLE_ID = 1555555456242552902

BG_IMAGE = "StorageHunters.png"
LAYOUT = {
    "avatar_size": (235, 235),   # Shrunk slightly to fit inside the neon ring
    "avatar_offset": (85, 95),   # Nudged Right (from 50 to 85) and Up (from 115 to 95)
    "text_main_pos": (450, 250), # Nudged Right to get away from the garage door
    "text_sub_pos": (450, 320),  # Nudged Right to align with main text
    "text_anchor": "ls"
}

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user.name} - Ready for the Hunt!')


# --- IMAGE GENERATOR ---
async def generate_image(member, text_main, text_sub):
    background = Image.open(BG_IMAGE).convert("RGBA")
    background = background.resize((1024, 500))
    av_size = LAYOUT["avatar_size"]

    try:
        avatar_bytes = await member.display_avatar.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
    except:
        avatar = Image.new("RGBA", av_size, (44, 47, 51, 255))

    avatar = avatar.resize(av_size)
    mask = Image.new('L', av_size, 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, av_size[0], av_size[1]), fill=255)

    background.paste(avatar, LAYOUT["avatar_offset"], mask)
    draw = ImageDraw.Draw(background)

    try:
        main_font = ImageFont.truetype("font.ttf", 45)
        sub_font = ImageFont.truetype("font.ttf", 30)
    except:
        main_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    text_anchor = LAYOUT["text_anchor"]
    draw.text(LAYOUT["text_main_pos"], text_main, fill="white", font=main_font, anchor=text_anchor)
    draw.text(LAYOUT["text_sub_pos"], text_sub, fill="lightgray", font=sub_font, anchor=text_anchor)

    buffer = io.BytesIO()
    background.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="card.png")


# --- WELCOME & GOODBYE ---
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(SH_WELCOME_ID)
    if not channel: return
    try:
        file = await generate_image(member, f"{member.name} has joined the hunt!",
                                    f"Hunter ID: #{len(member.guild.members)}")
        welcome_messages = [
            f"A new Hunter has located the lobby! Welcome, {member.mention}.",
            f"Hope you brought your keys, {member.mention}. Welcome to **Storage Hunters PH**!",
            f"Everyone welcome {member.mention} to the syndicate. 📦",
        ]
        await channel.send(content=random.choice(welcome_messages), file=file)
    except Exception as e:
        print(f"Error sending welcome: {e}")


@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(SH_GOODBYE_ID)
    if not channel: return
    try:
        file = await generate_image(member, f"{member.name} cleared their locker.", "Safe travels out there!")
        await channel.send(content=f"**{member.name}** has departed. We'll keep your keys safe. 🛩️", file=file)
    except Exception as e:
        print(f"Error sending goodbye: {e}")


# --- VOICE CALL LOGS ---
@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = bot.get_channel(SH_LOG_ID)
    if not log_channel: return

    if before.channel is None and after.channel is not None:
        await log_channel.send(embed=discord.Embed(
            description=f"🔊 **{member.mention}** joined `{after.channel.name}`", color=0x43B581))
    elif before.channel is not None and after.channel is None:
        await log_channel.send(embed=discord.Embed(
            description=f"🔇 **{member.mention}** left `{before.channel.name}`", color=0xF04747))
    elif before.channel != after.channel:
        await log_channel.send(embed=discord.Embed(
            description=f"🔄 **{member.mention}** moved: `{before.channel.name}` ➔ `{after.channel.name}`",
            color=0xFAA61A))


# --- SERVER RULES COMMAND ---
@bot.command(name="rules")
@commands.has_permissions(administrator=True)
async def rules(ctx):
    embed = discord.Embed(
        title="📦 Storage Hunters PH | Official Directives",
        color=0x00FFFF,
        description="Welcome to the syndicate. Read the rules below and click the ✅ reaction to verify your account and get the **Bidders** role."
    )
    embed.add_field(name="🤝 1. Respect Your Fellow Hunters",
                    value="No toxicity, harassment, or slurs. Keep the environment clean and welcoming for all players.",
                    inline=False)
    embed.add_field(name="🚫 2. No Spamming or Self-Promotion",
                    value="Avoid spamming text channels, and do not advertise other Discord servers or external links.",
                    inline=False)
    embed.add_field(name="🔞 3. Keep Content SFW",
                    value="No inappropriate, NSFW, or explicit content allowed in text, images, or voice channels.",
                    inline=False)
    embed.add_field(name="🔊 4. Clear Comms",
                    value="No mic spamming, soundboards, or earrape in the voice lobbies while people are hunting.",
                    inline=False)
    embed.add_field(name="⚠️ 5. No Exploiting or Game Cheats",
                    value="Keep the hunt fair. Anyone caught using executors or hacking the game will be permanently locked out.",
                    inline=False)

    embed.set_footer(text="Storage Hunters Philippines • Stay safe out there.")

    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")  # Bot adds the checkmark automatically
    await ctx.message.delete()


# --- START BOT ---
bot.run(os.environ.get("DISCORD_TOKEN"))