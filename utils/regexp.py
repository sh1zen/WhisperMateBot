import re


def regexp(php_regex, delimiter='#', py_flags=re.NOFLAG):
    # Remove PHP regex delimiters and flags
    regex_parts = php_regex.split(delimiter)
    pattern = regex_parts[1]
    flags = regex_parts[2] if len(regex_parts) > 2 else ""

    # Translate PHP-specific patterns
    pattern = pattern.replace('\\/', '/')
    pattern = pattern.replace('(?i)', '(?i:)')
    pattern = pattern.replace('(?-i)', '(?-i:)')

    # Translate PHP-specific flags
    flag_mapping = {
        'i': re.IGNORECASE,
        'm': re.MULTILINE,
        's': re.DOTALL,
        'x': re.VERBOSE
    }

    for flag in flags:
        py_flags = py_flags | flag_mapping.get(flag, re.NOFLAG)

    return re.compile(pattern, py_flags)
