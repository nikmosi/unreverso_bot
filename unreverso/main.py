import asyncio
import csv
import io
import os
from typing import List

import epitran
import magic
from dotenv import load_dotenv
from loguru import logger
from pyrogram import filters
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message


class ReWord:
    word: str
    translated_word: str
    extra_translation: str
    example: str
    translated_example: str
    pronouncing: str

    @property
    def translated_word_with_extra(self):
        words = [self.translated_word, self.extra_translation]
        ex_tr = " | ".join(filter(lambda a: len(a) > 0, words))
        return ex_tr

    def to_list(self) -> List[str]:
        return [
            self.word,
            self.pronouncing,
            self.translated_word_with_extra,
            self.example,
            self.translated_example,
        ]

    @staticmethod
    def parse(data: list, epit: epitran.Epitran) -> "ReWord":
        rw = ReWord()
        rw.word = data[2]
        rw.translated_word = data[3]
        rw.extra_translation = data[4]
        rw.example = data[5]
        rw.translated_example = data[6]
        rw.pronouncing = epit.transliterate(rw.word.lower())
        return rw


@logger.catch
def run():
    load_dotenv()

    api_id = os.getenv("api_id")
    api_hash = os.getenv("api_hash")

    if api_id is None or api_hash is None:
        raise Exception()

    app = Client("bot", api_id, api_hash)

    @app.on_message(
        filters.document
        & filters.private
        & (filters.user("nikmosi") | filters.user("nikmosi_alt"))
    )
    async def convert_document(client: Client, message: Message):
        epit = epitran.Epitran("eng-Latn")
        username = message.from_user.username
        file_name = message.document.file_name
        logger.info(f"get file from {username}")

        m = await message.reply_text("dowloading...")

        file = await client.download_media(message, "lan.csv", True)
        if not isinstance(file, io.BytesIO):
            return

        byte_view = bytes(file.getbuffer())
        mime_type = magic.from_buffer(byte_view, mime=True)
        if mime_type != "text/plain":
            logger.info(f"get bad type {mime_type} from {username}")
            await m.edit_text("bad type(")
            await asyncio.sleep(4)
            await m.delete()
            await message.delete()
            return
        reader = csv.reader(byte_view.decode().split("\n"))
        await m.edit_text("convering...")

        with io.BytesIO() as byt, io.TextIOWrapper(byt, encoding="utf-8") as f:
            byt.name = "words.csv"
            writer = csv.writer(f, delimiter=";", quoting=csv.QUOTE_ALL)

            for i in filter(lambda a: a[0] == "en", reader):
                rw = ReWord.parse(i, epit)
                writer.writerow(rw.to_list())
            f.flush()

            await message.delete()
            await m.edit_text("sending...")
            doc = await message.reply_document(byt)
            logger.info(f"send file to {username}")

        await m.delete()
        await asyncio.sleep(16)
        await doc.delete()

        logger.info(f"finish file from {username} with name {file_name}")

    logger.info("running")
    app.run()


if __name__ == "__main__":
    logger.add("unreverso.log", rotation="10 MB", compression="bz2", level="DEBUG")
    run()
