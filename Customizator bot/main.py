import discord
from discord.ext import commands
import random

intents = discord.Intents.all()

COLORS = {
    "Красный": discord.Color.red(),
    "Синий": discord.Color.blue(),
    "Зеленый": discord.Color.green(),
    "Желтый": discord.Color.gold(),
    "Фиолетовый": discord.Color.purple(),
    "Розовый": discord.Color.magenta(),
    "Белый": discord.Color.default(),
    "Черный": discord.Color.default(),
}

bot = commands.Bot(command_prefix='!', intents=intents)

bot.remove_command('help')


async def add_roles_to_channel(channel, roles):
    for role_name in roles:
        role = discord.utils.get(channel.guild.roles, name=role_name)
        if role:
            await channel.set_permissions(role, read_messages=True, connect=True)
        else:
            print(f"Роль '{role_name}' не найдена на сервере.")


@bot.command(name='create_role')
async def create_role(ctx, name: str):
    guild = ctx.guild
    color = discord.Color(random.randint(0, 0xFFFFFF))
    role = await guild.create_role(name=name, color=color)
    await ctx.send(f"Роль {name} успешно создана")
    message = await ctx.send(
        f"Выберите тип прав для роли {name}: \n1. Нет прав\n2. Ограниченные права\n3. Администратор")
    await message.add_reaction('1️⃣')  # Нет прав
    await message.add_reaction('2️⃣')  # Ограниченные права
    await message.add_reaction('3️⃣')  # Администратор

    def check(reaction, user):
        return user == ctx.author and reaction.message == message and str(reaction.emoji) in ['1️⃣', '2️⃣', '3️⃣']

    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        if str(reaction.emoji) == '1️⃣':
            await role.edit(permissions=discord.Permissions.none())
            await ctx.send(f"Роль {name} получила права: Нет прав")
        elif str(reaction.emoji) == '2️⃣':
            permissions = discord.Permissions()
            permissions.update(manage_nicknames=True)
            await role.edit(permissions=permissions)
            await ctx.send(f"Роль {name} получила права: Ограниченные права (с управлением никнеймами)")
        elif str(reaction.emoji) == '3️⃣':
            await role.edit(permissions=discord.Permissions.all())
            await ctx.send(f"Роль {name} получила права: Администратор")
    except asyncio.TimeoutError:
        await ctx.send("Время вышло, попробуйте снова.")


@bot.command(name='delete_role')
async def delete_role(ctx, role_name: str):
    if not role:
        await ctx.send(f"Роль с именем '{role_name}' не найдена.")
        return

    if role.permissions.administrator:
        await ctx.send("Бот не может удалять роли с правами администратора.")
        return

    await role.delete()
    await ctx.send(f"Роль {role_name} успешно удалена.")


@bot.command(name='change_role_color')
async def change_role_color(ctx, role_name: str, color_name: str):
    role = discord.utils.get(ctx.guild.roles, name=role_name)

    if not role:
        await ctx.send(f"Роль с именем '{role_name}' не найдена.")
        return

    if color_name.capitalize() not in COLORS:
        await ctx.send("Неверное название цвета.")
        return

    color = COLORS[color_name.capitalize()]

    await role.edit(color=color)
    await ctx.send(f"Цвет роли {role_name} успешно изменен на {color_name}.")


@bot.command(name='list_roles')
async def list_roles(ctx):
    roles = [role for role in ctx.guild.roles if role != ctx.guild.default_role]

    role_names = "\n".join([role.name for role in roles])

    await ctx.send(f"Список ролей на сервере:\n{role_names}")


@bot.command(name='create_channel')
async def create_channel(ctx, channel_name: str):
    await ctx.send("Введите тип канала ('текст' или 'голосовой'):")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=60)

        channel_type = msg.content.lower()
        if channel_type not in ['текст', 'голосовой']:
            await ctx.send("Неверный тип канала. Используйте 'текст' или 'голосовой'.")
            return

        await ctx.send("Введите статус канала ('открытый' или 'закрытый'):")
        msg = await bot.wait_for('message', check=check, timeout=60)

        overwrites = {}
        if msg.content.lower() == 'закрытый':
            overwrites[ctx.guild.default_role] = discord.PermissionOverwrite(read_messages=False, connect=False)

            await ctx.send("Введите роли, которые могут использовать канал (через запятую):")
            msg = await bot.wait_for('message', check=check, timeout=60)
            roles = msg.content.split(',')
            roles = [role.strip() for role in roles]
            role_objects = [discord.utils.get(ctx.guild.roles, name=role) for role in roles]
            for role_object in role_objects:
                if role_object is not None:
                    overwrites[role_object] = discord.PermissionOverwrite(read_messages=True, connect=True)
        else:
            overwrites = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True, connect=True)}

        if channel_type == 'текст':
            await ctx.guild.create_text_channel(name=channel_name, overwrites=overwrites)
            await ctx.send(f"Текстовый канал '{channel_name}' успешно создан.")
        else:
            await ctx.guild.create_voice_channel(name=channel_name, overwrites=overwrites)
            await ctx.send(f"Голосовой канал '{channel_name}' успешно создан.")

    except asyncio.TimeoutError:
        await ctx.send("Превышено время ожидания. Попробуйте снова.")


@bot.command(name='delete_channel')
async def delete_channel(ctx, channel_name: str):
    channel = discord.utils.get(ctx.guild.channels, name=channel_name)
    if channel:
        await channel.delete()
        await ctx.send(f"Канал '{channel_name}' успешно удален.")
    else:
        await ctx.send(f"Канал '{channel_name}' не найден.")


@bot.command(name='add_roles_to_channel')
async def add_roles_to_channel_command(ctx, channel_name: str, *roles):
    channel = discord.utils.get(ctx.guild.channels, name=channel_name)

    if channel:
        if isinstance(channel, discord.TextChannel) or isinstance(channel, discord.VoiceChannel):
            await add_roles_to_channel(channel, roles)
            await ctx.send(f"Роли успешно добавлены к каналу '{channel_name}'.")
        else:
            await ctx.send("Указанный канал не является текстовым или голосовым.")
    else:
        await ctx.send(f"Канал '{channel_name}' не найден.")


@bot.command(name='create_category')
async def create_category(ctx, category_name: str):
    try:
        await ctx.guild.create_category(category_name)
        await ctx.send(f"Категория каналов '{category_name}' успешно создана.")
    except discord.Forbidden:
        await ctx.send("У меня нет прав на создание категорий каналов.")
    except discord.HTTPException:
        await ctx.send("Не удалось создать категорию каналов. Попробуйте снова.")


@bot.command(name='delete_category')
async def delete_category(ctx, category_name: str):
    category = discord.utils.get(ctx.guild.categories, name=category_name)
    if category:
        try:
            await category.delete()
            await ctx.send(f"Категория каналов '{category_name}' успешно удалена.")
        except discord.Forbidden:
            await ctx.send("У меня нет прав на удаление этой категории каналов.")
        except discord.HTTPException:
            await ctx.send("Не удалось удалить категорию каналов. Попробуйте снова.")
    else:
        await ctx.send(f"Категория каналов '{category_name}' не найдена.")


@bot.command(name='list_categories')
async def list_categories(ctx):
    categories = [category.name for category in ctx.guild.categories]
    if categories:
        categories_str = '\n'.join(categories)
        await ctx.send(f"Список категорий каналов:\n{categories_str}")
    else:
        await ctx.send("На сервере нет категорий каналов.")


@bot.command(name='move_channels_to_category')
async def move_channels_to_category(ctx, category_name: str, *, channels: str):
    category = discord.utils.get(ctx.guild.categories, name=category_name)

    if category:
        channel_names = [channel.strip() for channel in channels.split(',')]
        for channel_name in channel_names:
            channel = discord.utils.get(ctx.guild.channels, name=channel_name)
            if channel:
                try:
                    await channel.edit(category=category)
                    await ctx.send(f"Канал '{channel_name}' успешно перемещен в категорию '{category_name}'.")
                except discord.Forbidden:
                    await ctx.send("У меня нет прав на перемещение канала.")
                except discord.HTTPException:
                    await ctx.send("Не удалось переместить канал. Попробуйте снова.")
            else:
                await ctx.send(f"Канал '{channel_name}' не найден.")
    else:
        await ctx.send(f"Категория '{category_name}' не найдена.")


@bot.command(name='clear_channel')
async def clear_channel(ctx):
    deleted_messages = []

    while True:
        deleted = await ctx.channel.purge(limit=100)
        deleted_messages.extend(deleted)
        if len(deleted) < 100:
            break

    await ctx.send(f"Удалено {len(deleted_messages)} сообщений.", delete_after=5)


@bot.command(name='help')
async def custom_help(ctx):
    commands_list = [f'`{command.name}`' for command in bot.commands if not command.hidden]
    help_message = f"List of available commands: {'     '.join(commands_list)}"
    await ctx.send(help_message)


@bot.event
async def on_message(message):
    forbidden_words = ["bad_word1", "bad_word2", "bad_word3"]

    for word in forbidden_words:
        if word in message.content.lower():
            await message.delete()
            await message.channel.send(f"{message.author.mention}, ваше сообщение содержит запрещенное слово.")
            break

    await bot.process_commands(message)


bot.run('ТОКЕН')
