import i18n


def error_text(error_code: int, acc: str) -> str:
    """
    Returns error message for user.
    Args:
        error_code: code returned by urllib lib or any number for convention
        acc: account name raised the error, to make error more pleasible
    """
    error_dict = {
        403: i18n.t("news_builders.403", acc=acc),
        404: i18n.t("news_builders.404", acc=acc),
        90: i18n.t("news_builders.90"),
    }
    some_error_text = i18n.t("news_builders.some_error", err=error_code, acc=acc)
    return error_dict.get(error_code, some_error_text)
