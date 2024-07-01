def strip_whole_str(string : str, substring : str) -> str:
    """Strips a whole substring from a string if it is present at the beginning or end of the string.
    
    :param string: The string to strip the substring from.
    :param substring: The substring to strip from the string.
    :return: ``str`` The string with the substring stripped from it.

    """
    
    if string.startswith(substring):
        string = string[len(substring):]
    if string.endswith(substring):
        string = string[:-len(substring)]
    return string.strip()