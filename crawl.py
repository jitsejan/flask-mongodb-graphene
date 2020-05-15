""" crawl.py """
import json
import lxml.html
import pandas as pd
import requests

BASE_URL = "https://www.mariowiki.com"
SMB_LEVEL_URL = f"{BASE_URL}/Category:Super_Mario_Bros._Levels"


def _get_cell_text(cell):
    if cell.cssselect("a"):
        return cell.cssselect("a")[0].text.strip()
    else:
        return cell.text.strip()


def _get_key_from_dict_cell(cell):
    if pd.notnull(cell):
        for key, value in cell.items():
            return key
    return cell


def _get_value_from_dict_cell(cell):
    if pd.notnull(cell):
        for key, value in cell.items():
            return value
    return cell


def _get_table_data(tree):
    table_data = {}
    for row in tree.cssselect('table.infobox tr[style*="vertical-align:top"]'):
        if _get_cell_text(row.cssselect("td")[1]):
            key = row.cssselect("td b")[0].text.strip()
            value = _get_cell_text(row.cssselect("td")[1])
            table_data[key] = value
    return table_data


def _get_description(tree):
    return tree.cssselect('meta[name="description"]')[0].get("content")


def _replace_string_with_numbers(input_str):
    numbers = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
    for number in numbers:
        input_str = input_str.lower()
        input_str = input_str.replace(number, str(numbers[number]))
    return input_str


def _get_powerups(input_str, powerups):
    powerup_list = []
    for pup in powerups:
        if pup.lower() in input_str:
            pattern = f"(?r)(\d).*?{pup.lower()}"
            powerup_list.append(
                {"name": pup, "amount": regex.search(pattern, input_str).group(1)}
            )

    return powerup_list


def _get_enemies(tree):
    enemy_list = []
    span = tree.cssselect("span#Enemies")[0]
    table = span.getparent().getnext()
    for row in table.cssselect("tr"):
        if row.cssselect("td"):
            key = row.cssselect("td")[0].cssselect("a[class!='image']")[0].text.strip()
            value = row.cssselect("td")[1].text.strip()
            enemy_list.append({"name": key, "amount": value})
    return enemy_list


def _get_level_statistics(tree):
    stats_list = []
    try:
        span = tree.cssselect("span#Level_statistics")[0]
        table = span.getparent().getnext()
        for row in table.cssselect("tr"):
            if row.cssselect("td"):
                try:
                    key = (
                        row.cssselect("td")[0]
                        .cssselect("a[class!='image']")[0]
                        .text.strip()
                    )
                    value = int(row.cssselect("td")[1].text.split("(")[0].strip())
                    stats_list.append({"name": key, "amount": value})
                except:
                    pass
        try:
            stats_list = _get_powerups(
                _replace_string_with_numbers(table.cssselect("li")[0].text_content()),
                powerups,
            )
            stats_list.append(
                {
                    "name": "1 up Mushroom",
                    "amount": int(
                        table.cssselect("li")[1].text_content().split(":")[-1]
                    ),
                }
            )

        except:
            pass
    except:
        pass
    return stats_list


def get_lxml_tree_from_url(url):
    """ Convert URL to XML tree """
    return lxml.html.fromstring(requests.get(url).content)


def get_all_tables():
    """ Retrieve all the tables """
    tree = get_lxml_tree_from_url(SMB_LEVEL_URL)
    for elem in tree.cssselect("#mw-pages a"):
        url = f"{BASE_URL}{elem.get('href')}"
        print(f"Crawling data for `{url}`")
        if "Minus" not in url:
            subtree = get_lxml_tree_from_url(url)
            yield {
                "table_data": _get_table_data(subtree),
                "description": _get_description(subtree),
                "enemies": _get_enemies(subtree),
                "statistics": _get_level_statistics(subtree),
            }


def main():
    """ Main function """
    df = pd.DataFrame.from_dict(get_all_tables())
    print(f"Found {len(df)} results")
    df.to_json("smb.json", orient="records")
    print(json.dumps(df.iloc[0].to_dict(), indent=4))


if __name__ == "__main__":
    main()
