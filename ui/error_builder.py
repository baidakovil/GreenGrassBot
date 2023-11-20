from services.message_service import i34g


async def error_text(error_code: int, acc: str, user_id: int) -> str:
    """
    Returns error message for user.
    Args:
        error_code: code returned by urllib lib or any number for convention
        acc: account name raised the error, to make error more pleasible
    """
    error_dict = {
        403: await i34g("news_builders.403", acc=acc, user_id=user_id),
        404: await i34g("news_builders.404", acc=acc, user_id=user_id),
        90: await i34g("news_builders.90", user_id=user_id),
    }
    some_error_text = await i34g(
        "news_builders.some_error", err=error_code, acc=acc, user_id=user_id
    )
    return error_dict.get(error_code, some_error_text)
