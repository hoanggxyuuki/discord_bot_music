import discord
from discord.ext import commands
import os
import asyncio
import random

BOT_TOKEN = "bottoken_here" 
MUSIC_FOLDER = "music_remix" 
COMMAND_PREFIX = "!" 

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

queues = {}

def play_next(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice_client and voice_client.is_connected():
            song_path = queues[ctx.guild.id].pop(0)
            queues[ctx.guild.id].append(song_path)
            song_name = os.path.splitext(os.path.basename(song_path))[0]
            source = discord.FFmpegPCMAudio(song_path)
            voice_client.play(source, after=lambda e: play_next(ctx))
            
            asyncio.run_coroutine_threadsafe(ctx.send(f"🎶 Vòng lặp: Đang phát **{song_name}**"), bot.loop)

@bot.event
async def on_ready():
    print(f'Đã đăng nhập với tên {bot.user}')
    print('Bot đã sẵn sàng hoạt động trên server!')
    print('------------------------------------')

@bot.command(name='play', help='Phát nhạc. Nếu có tên bài hát thì phát bài đó, nếu không thì phát lặp lại cả thư mục.')
async def play(ctx, *, song_name: str = None):
    if not ctx.author.voice:
        await ctx.send(f"{ctx.author.name} ơi, bạn cần phải ở trong một kênh thoại để dùng lệnh này!")
        return

    voice_channel = ctx.author.voice.channel
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if not voice_client:
        voice_client = await voice_channel.connect()
    elif voice_client.channel != voice_channel:
        await voice_client.move_to(voice_channel)
    
    if voice_client.is_playing():
        voice_client.stop()

    if ctx.guild.id in queues:
        del queues[ctx.guild.id]

    if song_name:
        song_path = os.path.join(MUSIC_FOLDER, f"{song_name}.mp3")
        
        if not os.path.exists(song_path):
            found = False
            for ext in ['.wav', '.ogg', '.m4a']:
                temp_path = os.path.join(MUSIC_FOLDER, f"{song_name}{ext}")
                if os.path.exists(temp_path):
                    song_path = temp_path
                    found = True
                    break
            if not found:
                await ctx.send(f"Xin lỗi, không tìm thấy bài hát nào có tên '{song_name}' 😥")
                return
        
        source = discord.FFmpegPCMAudio(song_path)
        voice_client.play(source)
        await ctx.send(f"🎶 Đang phát: **{song_name}**")

    else:
        all_songs = []
        for file in os.listdir(MUSIC_FOLDER):
            if file.endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                all_songs.append(os.path.join(MUSIC_FOLDER, file))
        
        if not all_songs:
            await ctx.send(f"Thư mục `{MUSIC_FOLDER}` không có bài hát nào để phát!")
            return
            
        random.shuffle(all_songs)
        
        queues[ctx.guild.id] = all_songs
        
        await ctx.send(f"▶️ Bắt đầu phát lặp lại **{len(all_songs)}** bài hát trong thư mục `{MUSIC_FOLDER}`.")
        
        play_next(ctx)


@bot.command(name='stop', help='Dừng nhạc, xóa hàng đợi và ngắt kết nối.')
async def stop(ctx):
    if ctx.guild.id in queues:
        del queues[ctx.guild.id]
    voice_client = discord.utils.get(bot.voice_clients, guild=ctx.guild)
    if voice_client and voice_client.is_connected():
        voice_client.stop()
        await voice_client.disconnect()
        await ctx.send("Đã dừng nhạc, xóa hàng đợi và ngắt kết nối. Hẹn gặp lại! 👋")
    else:
        await ctx.send("Bot đang không ở trong kênh thoại nào cả.")
bot.run(BOT_TOKEN)