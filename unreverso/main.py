import codecs
import io
import epitran
from loguru import logger
import csv
import os
from dotenv import load_dotenv
from pyrogram.client import Client
from pyrogram import filters
from pyrogram.types.messages_and_media.message import Message


@logger.catch
def run():
    load_dotenv()

    api_id = os.getenv("api_id")
    api_hash = os.getenv("api_hash")

    if api_id is None or api_hash is None:
        raise Exception()

    app = Client("bot", api_id, api_hash)

    @app.on_message(
        filters.document &
        filters.private &
        (filters.user("nikmosi") | filters.user("nikmosi_alt"))
    )
    async def hello(client: Client, message: Message):
        epit = epitran.Epitran("eng-Latn")
        m = await message.reply_text("dowloading...")
        file = await client.download_media(message, "lan.csv", True)
        if not isinstance(file, io.BytesIO):
            return
        s = bytes(file.getbuffer()).decode().split("\n")
        await m.edit_text("convering...")
        reader = csv.reader(s)

        byt = io.BytesIO()
        byt.name = "words.csv"
        f = io.TextIOWrapper(byt, encoding="utf-8")
        writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)
        for i in reader:
            if i[0] != "en":
                continue
            word = i[2]
            tr = i[3]
            p_tr = i[4]
            ex = i[5]
            tr_ex = i[6]
            pronoun = epit.transliterate(word.lower())

            writer.writerow([word, pronoun, f"{tr} | {p_tr}", ex, tr_ex])

        f.flush()
        await m.edit_text("sending...")
        await message.reply_document(byt)
        await m.delete()
        logger.info(f"procced file from {message.from_user.username}")

    logger.info("runing")
    app.run()


if __name__ == "__main__":
    logger.add("unreverso.log", rotation="10 MB", compression="bz2", level="DEBUG")
    run()
