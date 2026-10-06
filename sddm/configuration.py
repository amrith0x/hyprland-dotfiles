"""Small SDDM config edits that preserve unrelated settings and comments."""
import configparser
import re


def set_ini_option(text, section_name, key, value):
    lines = text.splitlines(keepends=True)
    section_start = next((i for i, line in enumerate(lines)
                          if line.strip() == '[' + section_name + ']'), None)
    entry = key + '=' + value + '\n'
    if section_start is None:
        return text.rstrip() + '\n\n[' + section_name + ']\n' + entry
    section_end = next((i for i in range(section_start + 1, len(lines))
                        if lines[i].lstrip().startswith('[')), len(lines))
    matches = [i for i in range(section_start + 1, section_end)
               if re.match(r'^[ \t]*' + re.escape(key) + r'[ \t]*=', lines[i])]
    if matches:
        for i in matches:
            lines[i] = entry
    else:
        if section_end and not lines[section_end - 1].endswith('\n'):
            lines[section_end - 1] += '\n'
        lines.insert(section_end, entry)
    return ''.join(lines)


def disable_keyboard(text):
    settings = configparser.ConfigParser(interpolation=None, strict=False)
    settings.read_string(text)
    environment = settings.get("General", "GreeterEnvironment", fallback="")
    variables = [item.strip() for item in environment.split(",")
                 if item.strip() and not item.strip().startswith("QT_IM_MODULE=")]
    variables.append("QT_IM_MODULE=compose")
    text = set_ini_option(text, "General", "InputMethod", "compose")
    return set_ini_option(text, "General", "GreeterEnvironment", ",".join(variables))
