import os
from io import BytesIO
from os import listdir
from os.path import isfile, join

from django.db.models import Q
from google.oauth2 import service_account
from pydub import AudioSegment

from config import celery_app
from google.cloud import texttospeech

from signifier.articles.models import Highlights, Article
from signifier.utils.misc import log_article, bytes_len

credentials = service_account.Credentials.from_service_account_file(
    "/app/.envs/tts-key.json"
)
client = texttospeech.TextToSpeechClient(credentials=credentials)

debug = True

class Breaks:
    after_title = '<break time="3s"/>'
    after_text = '<break time="6s"/>'
    after_text_highlights = '<break time="3s"/>'
    after_highlight = '<break time="2s"/>'
    before_heading = '<break time="2s"/>'
    after_heading = '<break time="1s"/>'


breaks = Breaks()


def process_text_and_append_audio(text_chunk, text_chunks, audio_chunks, split_text, index, rate):
    is_last_text = index == len(split_text) - 1
    if is_last_text or bytes_len(text_chunk) + bytes_len(split_text[index + 1]) > 4980:
        if is_last_text:
            text_chunk += breaks.after_text_highlights
        audio = get_audio(text_chunk, rate)
        audio_chunks.append(AudioSegment.from_ogg(BytesIO(audio)))
        text_chunks.append(text_chunk)
        return ""
    return text_chunk

@celery_app.task()
def highlights_tts():
    highlights_list = Highlights.objects.exclude(article__source__name='').filter(Q(has_audio=False) | Q(stale_audio=True))[:1]
    print(f"Will process {len(highlights_list)} highlights")

    for highlights in highlights_list:
        text_chunk = f'<p>{highlights.article.title}</p>{breaks.after_title}\n'
        text_chunks = []
        audio_chunks = []

        with open(f"/memex/{highlights.article.filename}.md") as file:
            text = file.read()

            if len(text) > 20000:  # ~20 minutes
                log_article(highlights.article)("Too long highligts")
                continue

        split_text = text.split("---")[3:]
        for index, paragraph in enumerate(split_text):
            clean_paragraph = ""
            for line in paragraph.splitlines():
                if not line.startswith("^"):
                    clean_paragraph += line + "\n"
            text_chunk += clean_paragraph + breaks.after_highlight
            text_chunk = process_text_and_append_audio(text_chunk, text_chunks, audio_chunks, split_text, index, 1.1)

        path = f"highlights/{highlights.article.filename}"
        log_tts_texts(path, text_chunks)
        save_audio(highlights, audio_chunks, path)

    safe = Highlights.objects.values_list("article__filename", flat=True)
    cleanup_dangling(safe)
    return {}

@celery_app.task()
def articles_tts():
    articles = Article.objects.exlcude(source__name='')[:1]
    print(f"Will process {len(articles)} articles")

    for article in articles:
        print(article)
        text_chunk = ""
        text_chunks = []
        audio_chunks = []
        log = log_article(article)

        with open(f"/articles/{article.filename}.txt") as file:
            text = file.read()
            if len(text) > 55000:  # 41 minutes
                log("Too long article")
                continue

        split_text = text.splitlines()
        split_text[0] = [
            f'<p>{article.title}</p>{breaks.after_title}\n\n'
        ]
        for index, line in enumerate(split_text):
            if line.startswith("##"):
                line = f'{breaks.before_heading}<p>{line.replace("#", "").strip()}</p>{breaks["after_heading"]}'
            if line.startswith(">"):
                line = line.replace(">", "").strip()
            text_chunk += f"<p>{line}</p>"
            text_chunk = process_text_and_append_audio(text_chunk, text_chunks, audio_chunks, split_text, index, 1.2)

        path = f"articles/{article.filename}"
        log_tts_texts(path, text_chunks)
        save_audio(article, audio_chunks, path)

    return {}


def get_audio(text, speaking_rate):
    input_text = texttospeech.SynthesisInput(ssml=f"<speak>{text}</speak>")
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.MALE,
        name="en-US-Wavenet-J",
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.OGG_OPUS, speaking_rate=speaking_rate
    )
    response = client.synthesize_speech(
        request={
            "input": input_text,
            "voice": voice,
            "audio_config": audio_config,
        }
    )
    return response.audio_content


def save_audio(obj, audio_chunks, path):
    path = "/output/audio/" + path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sum(audio_chunks).export(path + ".ogg", format="ogg", parameters=["-aq", "4"])
    obj.length = sum([chunk.duration_seconds for chunk in audio_chunks]) / 60
    obj.has_audio = True
    obj.stale_audio = False
    obj.save()


def cleanup_dangling(safe):
    path = "/output/audio/highlights/"
    files = [
        file[:-4]
        for file in listdir(path)
        if isfile(join(path, file))
           and file.endswith(".ogg")
           and not file.startswith("_")
    ]
    for file in set(files) - set(safe):
        os.remove(f"{path}{file}.ogg")
        try:
            os.remove(f"{path}{file}.txt")
        except:
            pass


# buggy, characters are read literally
def escape_for_ssml(text):
    return (
        text.replace('"', "&quot;")
        .replace("&", "&amp;")
        .replace("'", "&apos;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def log_tts_texts(path, text_chunks):
    with open(f"/output/tts/{path}.txt", "w") as out:
        out.write("".join(text_chunks))
