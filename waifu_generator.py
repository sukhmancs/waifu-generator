import discord
from discord.ext import commands
import requests
import os
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

class MyClient(commands.Bot):
    """A subclass of discord.Client that overrides the on_ready and on_message methods.

    Attributes:
        None"""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.command_in_progress = False  # flag to check if a command is in progress

    async def on_ready(self):
        print(f'Logged in as {self.user}')

    async def on_message(self, message):
        # Prevent the bot from responding to its own messages
        if message.author == self.user:
            return

        if message.content.startswith('!help'):
            help_message = (
                "Usage:\n"
                "\t`!waifu [OPTION]... [TAG]...`\n\n"
                "Options:\n"
                "\t`--segs`\tInclude this option for NSFW images.\n"
                "\t`--im`\tUse waifu.im API. You can use many tags.\n"
                "\t`--pics`\tUse waifu.pics API. Use 1 tag only.\n"
                "\t`--nekos`\tUse nekos.life (old) API. No tags.\n\n"
                "Tags:\n"
                "\t`waifu.im (type):\n`"
                "\t\tmaid waifu marin-kitagawa mori-calliope raiden-shogun oppai selfies uniform\n"
                "\t`waifu.im (nsfw tags):\n`"
                "\t\tecchi hentai ero ass paizuri oral milf"
            )
            await message.channel.send(help_message)
            return

        # this is required to process the commands
        await self.process_commands(message)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send('Invalid command. Type "!help" for more information.')
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('argumntsPlease provide the correct format. Type "!help" for more information.')
        else:
            await ctx.send('An error occurred while processing the command. Please try again later.')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == '👍':
            await reaction.message.channel.send('Thank you for the feedback!')

# Replace 'your_token_here' with your actual bot token
client = MyClient()

@client.command()
async def waifu(ctx, *args):
    """
    This is a command to generate an image based on the prompt and guidance scale.

    ctx: commands.Context
        The context used for command invocation.

    args: str
        A tuple of strings that represent the arguments passed to the command.
        eg, '!waifu --im maid' -> args = ('--im', 'maid')
    """
    # check if a command is already in progress
    if client.command_in_progress:
        await ctx.send('A command is already in progress. Please wait for the current command to finish.')
        return

    try:
        client.command_in_progress = True
        # Split the message content into command and arguments
        args = list(args)

        mode = 'im' # either 'im' (waifu.im), 'nekos' (nekos.life), or 'pics' (waifu.pics)
        segs = False  # Default NSFW setting
        # api_name = {'im': 'waifu.im', 'nekos': 'nekos.life', 'pics': 'waifu.pics', 'moe': 'nekos.moe'}
        debug = False
        taglist = []
        headers = {}
        output = {}

        # Process arguments
        for arg in args:
            if arg == '--segs':
                segs = True
            elif arg in ['--im', '--nekos', '--pics', '--moe']:
                mode = arg.replace('--', '') # '--im' -> 'im', '--nekos' -> 'nekos' etc.
            else: # no option was provided, so it must be a tag
                taglist.append(arg)

        # Prepare the API request based on mode and tags
        if mode == 'im':
            url = 'https://api.waifu.im/search'
            headers = {'Accept-Version': 'v5'}

        elif mode == 'nekos':
            if segs:
                url = 'https://nekos.life/api/lewd/neko'
            else:
                url = 'https://nekos.life/api/neko'

        elif mode == 'pics':
            if segs:
                url = 'https://api.waifu.pics/nsfw/'
            else:
                url = 'https://api.waifu.pics/sfw/'

            if len(taglist) > 0:
                url += taglist[0]
            else:
                url += 'waifu'

        elif mode == 'moe':
            url = 'https://nekos.moe/api/v1/random/image'
            if segs:
                url += '?nsfw=true'

        else: # default: waifu.im
            url = 'https://api.waifu.im/search'
            headers = {'Accept-Version': 'v5'}

        params = {
            'included_tags': taglist,
            'height': '>=600',
            'nsfw': segs
        }

        response = requests.get(url, params=params, headers=headers)

        ###### processing ######
        if response.status_code == 200:
            data = response.json()
            # Process the response data as needed
            if mode == 'im':
                output['link'] = data['images'][0]['url']
                output['sauce']  = data['images'][0]['source']
            elif mode == 'nekos':
                output['link'] = data['neko']
                output['sauce'] = data['neko']
            elif mode == 'moe':
                image_id = data['images'][0]['id']
                output['link'] = str('https://nekos.moe/image/' + image_id)
                output['sauce'] = str('https://nekos.moe/post/' + image_id)
            elif mode == 'pics':
                output['link'] = data['url']
                output['sauce'] = data['url']
            else: # default: waifu.im
                output['link'] = data['images'][0]['url']
                output['sauce']  = data['images'][0]['source']

            image_url = output['link']

            # Send the image URL as a message
            await ctx.send(image_url)
        else:
            await ctx.send('Failed to fetch image.')
    except Exception as e:
        await ctx.send('Please provide the correct format. Type "!help" for more information.')

    finally:
        # reset the flag
        client.command_in_progress = False

client.run(os.getenv('DISCORD_TOKEN'))
