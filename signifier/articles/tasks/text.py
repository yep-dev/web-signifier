import json
import os
import subprocess

from config import celery_app

from signifier.articles.models import Article, Source
from signifier.utils.misc import log_article
from signifier.utils.postlightToText import postlight_main


breaks = {
    "after_title": '<break time="3s"/>',
    "after_text": '<break time="6s"/>',
    "after_text_highlights": '<break time="3s"/>',
    "after_highlight": '<break time="2s"/>',
    "before_heading": '<break time="2s"/>',
    "after_heading": '<break time="1s"/>',
}


@celery_app.task()
def articles_text():
    for article in Article.objects.exclude(author__name='').filter(downloaded=False, author__name='LW').order_by("?")[:1]:
        log = log_article(article)
        try:
            data = subprocess.run(
                ["postlight-parser", article.url, '--extend', 'lw_author=.PostsAuthors-authorName .UsersNameDisplay-noColor'], stdout=subprocess.PIPE
            ).stdout.decode("utf-8")
        except Exception as e:
            print("URL", article.url)
            print(e)
        else:
            data = json.loads(data)
            data = postlight_main(data, None)

            if len(data["content"]["text"]) > 500:
                folder = article.author.name
                if author := data['lw_author']:
                    article.author = Source.objects.get_or_create(site='lesswrong', name='LW', author=author)[0]
                    folder = f"LW {author}"
                path = f"/articles/{folder}/{article.filename}.md"
                os.makedirs(os.path.dirname(path), exist_ok=True)

                with open(path, "w") as f:
                    print(data['content'])
                    text = f"# {article.title}\n\n" + data["content"]["text"]
                    f.write(text)

                article.downloaded = True
                article.save()
            else:
                log("Couldn't parse article content")
    return {}
