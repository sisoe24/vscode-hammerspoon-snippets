import os
import re
import json
import logging

logging.basicConfig(format='%(levelname)s: %(message)15s',
                    filename='report.log', level=logging.INFO)

HAMMERSPOON_DOCS_PATH = '/Applications/Hammerspoon.app/Contents/Resources/docs.json'
EXCLUDED_MODULES = ('hs.appfinder', 'hs.applescript')


def hammerspoon_documentation() -> list:
    """Open and return then hammerspoon documentation."""
    with open(HAMMERSPOON_DOCS_PATH) as h_doc:
        return json.load(h_doc)


def insert_placeholders(args, body):
    """Insert placeholder sign "$" to arguments inside the snippets body.

    Args:

        body (str): body snippet

    Returns:

        str: body snippet with placeholders
    """
    # TODO: some code is `a,[,b[,c]]` so split will make ugly groups.
    # but it works...

    args_list = [arg.strip() for arg in args.split(',')]
    for index, arg in enumerate(args_list, 1):
        placeholders = "${%i:%s}" % (index, arg)
        body = body.replace(arg, placeholders, 1)

    return body


def clean_body(string):
    """Clean some extra characters from the body snippet like returning signs
    and empty square brackets.

    I am deleting square brackets even if for Lua could be syntatically correct
    because you can call the `table` `hs.alert.defaultStyle` and receive no error
    but if you add the square brackets it expects an argument or wil fail to execute.
    So its easier to add them when you know the key you need inside the table.

    Example:

        hs.menuIcon([state]) -> bool : hs.menuIcon([state])
        hs.alert.defaultStyle[]      : hs.alert.defaultStyle

    """
    patterns = {
        r'\s->.+': '',
        r'\[\]': '',
    }

    for pattern, sub in patterns.items():
        string = re.sub(pattern, sub, string)

    return string


def format_body(body: str) -> str:
    """Perform some formatting/cleaning of the snippet body code.

    Args:

        body (str)

    Returns:

        str: formatted/cleaned body code.
    """
    body = clean_body(body)

    if args := re.search(r'(?<=\()[^)]+', body):
        body = insert_placeholders(args.group(), body)

    return body


def compose_snippet(title: str, prefix: str, body: str, description: str) -> dict:
    """Compose the snippet in vscode style paragraph.

        "title": {
            "prefix": "",
            "body: "",
            "description": ""
        }

    Args:

        title (str)
        prefix (str)
        body (str)
        description (str)

    Returns:

        dict: vscode style snippet paragraph
    """
    return {
        title: {
            "prefix": prefix,
            "body": format_body(body),
            "description": description
        }
    }


def hammersoon_snippets():
    """ Generate snippets from hammerspoon documentation."""
    snippets = {}
    title = ""
    index = 1

    for module in hammerspoon_documentation():
        if module['name'] not in EXCLUDED_MODULES:

            for item in module['items']:

                # clean trailing index for comparison
                title = re.sub(r'_\d{1,2}$', '', title)

                # some item description are identical so it will not create a key dict
                if item['desc'] == title:
                    title = title + "_" + str(index)
                    index += 1
                else:
                    title = item['desc']
                    index = 1

                logging.debug("%s -> %s -> %s",
                              module['name'], item['def'], title)

                snippets.update(compose_snippet(
                    title=title,
                    prefix=item['def'],
                    body=item['def'],
                    description=item['doc'])
                )

    return snippets


def generate_snippets():
    """Create json snippets file."""
    snippets_filepath = 'snippets/snippets.json'

    if os.path.exists(snippets_filepath):
        os.rename(snippets_filepath, snippets_filepath + '.old')

    with open(snippets_filepath, 'w') as snippets_file:
        snippets_file.write("{}")
        snippets_file.seek(0)
        json.dump(hammersoon_snippets(), snippets_file, indent=4)


if __name__ == '__main__':
    generate_snippets()
