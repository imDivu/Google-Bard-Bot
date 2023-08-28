import asyncio, io, sys, traceback
from config import *
from telethon import events
from telethon.sync import TelegramClient
from bardapi import Bard


async def aexec(code, event):
    exec(
        (
            (
                ("async def __aexec(e, client): " + "\n message = event = e")
                + "\n reply = await event.get_reply_message()"
            )
            + "\n chat = (await event.get_chat()).id"
        )
        + "".join(f"\n {l}" for l in code.split("\n"))
    )

    return await locals()["__aexec"](event, event.client)

async def emval(event):
    xx = await event.edit('...')
    try:
        cmd = event.text.split(" ", maxsplit=1)[1]
    except IndexError as IE:
        return await event.edit(IE)
    if event.reply_to_msg_id:
        reply_to_id = event.reply_to_msg_id
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None
    reply_to_id = event.message.id
    try:
        await aexec(cmd, event)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ''
    if exc:
        evaluation += str(exc)
    elif stderr:
        evaluation += str(stderr)
    elif stdout:
        evaluation += str(stdout)
    else:
        evaluation += 'Success'
    final_output = (
        "__►__ **EVALPy**\n```{}``` \n\n __►__ **OUTPUT**: \n```{}``` \n".format(
            cmd,
            evaluation,
        )
    )
    if len(final_output) > 4090:
        ultd = final_output.replace("`", "").replace("**", "").replace("__", "")
        with io.BytesIO(str.encode(ultd)) as out_file:
            out_file.name = "eval.txt"
            await event.client.send_file(
                event.chat_id,
                out_file,
                force_document=True,
                allow_cache=False,
                caption=f"```{cmd}```" if len(cmd) < 990 else None,
                reply_to=reply_to_id,
            )
    else:
        await xx.reply(final_output)


def bard(prompt: str, image_path: None):
   if image_path is not None:
       image = open(image_path, 'rb').read() # (jpeg, png, webp) are supported.
       bard_answer = Bard().ask_about_image(prompt, image)
   else:
       bard_answer = bard.get_answer(prompt)
   try:
       return str(bard_answer['content'])
   except KeyError:
       return "Sorry, I didn't understand your prompt."



with TelegramClient(name='google-bard-bot', bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH) as client:

    @client.on(events.NewMessage(incoming=True, pattern=r"/eval (.*)"))
    async def eval(event):
        await emval(event)
      
    @client.on(events.NewMessage(incoming=True, pattern=r"/ask (.*)"))
    async ask(event):
        prompt = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        if reply.photo:
            image_path = await client.download_media(reply)
            response = bard(prompt, image_path)
        else:
            response = bard(prompt)
          
        if len(response) > 4090:
           ultd = response.replace("`", "").replace("**", "").replace("__", "")
           with io.BytesIO(str.encode(ultd)) as out_file:
              out_file.name = "response.txt"
              await event.client.send_file(
                event.chat_id,
                out_file,
                force_document=True,
                allow_cache=False,
                caption=f"```{prompt}```" if len(prompt) < 990 else None,
                reply_to=reply_to_id,
              )
        else:
            await xx.reply(response)
        
        

    print("Bot Ded, Server Daun!")
    client.run_until_disconnected()
