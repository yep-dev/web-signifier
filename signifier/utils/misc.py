def log_text(text):
    with open("/app/data/log.txt", "a") as file:
        file.write(f"{text}\n")


def log_article(article):
    def log(message):
        with open("/app/data/log.txt", "a") as file:
            title = article.title.replace("\n", "")
            file.write(f"{message}:   {title}\n")

    return log

def get_or_none(model, *args, **kwargs):
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None

def bytes_len(text):
    return len(text.encode("utf-8"))
