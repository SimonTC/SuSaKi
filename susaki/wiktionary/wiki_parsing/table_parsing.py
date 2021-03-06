import re

import logging

from lxml import etree

from susaki.wiktionary.wiki_parsing import util

logger = logging.getLogger(__name__)


########################################
# Entry parsing function
########################################
def parse_inflection_table(table_soup, table_type):
    """
    Parse the table soup according to the table type given.
    Return the root of the element tree for the inflection table.
    """
    logger.debug('Parsing inflection table of type {}'.format(table_type))
    inflection_root = etree.Element('Inflection_Table')
    if table_type == 'pronoun':
        table_soup = table_soup.find('table')
    table_rows = table_soup.find_all('tr', recursive=False)
    logger.debug('Number of table rows: {}'.format(len(table_rows)))
    headline = table_rows[0]
    if table_type != 'pronoun':
        meta_element = parse_meta_information(headline)
        inflection_root.append(meta_element)

    if table_type in ['verb', 'suffix']:
        if len(table_rows) < 30:
            # This is not a full verb inflection table so we ignore it.
            # This happens when a single case of a verb has its own article
            return None
        else:
            table_root = parse_verb_table(table_rows)
    elif table_type in ['noun', 'adjective', 'adverb', 'proper_noun']:
        table_root = parse_noun_table(table_rows)
    elif table_type in ['pronoun', 'numeral']:
        table_root = parse_pronoun_table(table_rows)
    else:
        raise ValueError(
            'No method implemented for parsing tables of type "{}"'.format(table_type))

    inflection_root.append(table_root)
    logger.debug('Finished inflection table of type {}'.format(table_type))
    return inflection_root


########################################
# Meta info parsing
########################################
def parse_meta_information(headline_row):
    logger.debug('Starting extracting meta info from table')
    headline_element = headline_row.th
    headline_text = util.clean_text(headline_element.text)
    logger.debug('Headline text: {}'.format(headline_text.replace('\n', '')))
    word, kotus_type, kotus_word, gradation = extract_meta_information(headline_text)
    meta_element = create_meta_tree(word, kotus_type, kotus_word, gradation)
    logger.debug('Finished extracting meta info from table')
    return meta_element


def extract_meta_information(headline_text):
    """ Extract meta information from the headline text"""
    meta_info = re.match(r" *Inflection of (-?[\w -'']+) \(Kotus type (\d\d?)/(\w+), (.*) gradation\)", headline_text)
    word = meta_info.group(1)
    kotus_type = meta_info.group(2)
    kotus_word = meta_info.group(3)
    gradation = meta_info.group(4)
    logger.debug('Word: {}'.format(word))
    logger.debug('Kotus type: {}'.format(kotus_type))
    logger.debug('Kotus word: {}'.format(kotus_word))
    logger.debug('Gradation {}'.format(gradation))
    return word, kotus_type, kotus_word, gradation


def create_meta_tree(word, kotus_type, kotus_word, gradation):
    meta_element = etree.Element('meta')
    kotus_element = etree.SubElement(meta_element, 'kotus')
    kotus_type_element = etree.SubElement(kotus_element, 'type')
    kotus_type_element.text = kotus_type
    kotus_word_element = etree.SubElement(kotus_element, 'word')
    kotus_word_element.text = kotus_word
    gradation_element = etree.SubElement(meta_element, 'gradation')
    gradation_element.text = gradation
    word_element = etree.SubElement(meta_element, 'word')
    word_element.text = word
    return meta_element


########################################
# Noun table parsing
########################################
def parse_noun_table(rows):
    logger.debug('Starting noun table parsing')
    table_root = etree.Element('table')
    in_accusative = False
    noun_case_element = None

    start_row = find_noun_table_start(rows)

    for i, row in enumerate(rows[start_row:]):
        logger.debug('Parsing row {}'.format(i + start_row))
        if in_accusative:
            logger.debug('Entering second accusative row (genitive)')
            parse_second_accusative_row(noun_case_element, row)
            in_accusative = False
        else:
            noun_case_name = row.th.text
            noun_case_name = util.clean_text(noun_case_name)
            logger.debug('Creating new noun case element: {}'.format(
                noun_case_name))
            noun_case_element = etree.Element(noun_case_name)
            table_root.append(noun_case_element)
            if noun_case_name == 'accusative':
                logger.debug('Found the accusative case')
                in_accusative = True
                noun_case_element = etree.SubElement(
                    noun_case_element, 'nominative')
            parse_noun_table_row(
                row, noun_case_element, noun_case_name)
    logger.debug('Finished noun table parsing')
    return table_root


def find_noun_table_start(rows):
    """ The noun table has to parts. The first part contains nominative,
    genitive, partitive and illative.
    After these four cases the main table begins and those four cases
    are repeated there but not in the same other. Because of this we want to
    ignore the first lines and first start parsing on the main table.
    Rows: The rows of the table
    Returns: the id of tgen.he row where the first entry of the main table exists.
             (After the table headers)
    """
    logger.debug('Starting search for the main table')
    for i, row in enumerate(rows[1:]):
        noun_case_name = row.th.text
        noun_case_name = util.clean_text(noun_case_name)
        logger.debug(noun_case_name)
        try:
            etree.Element(noun_case_name)
        except ValueError as err:
            if str(err) == 'Empty tag name':
                # We found the headers of the real table
                logger.debug('Found the table headers in row {}'.format(i + 1))
                return i + 2
            else:
                raise
    raise ValueError("Couldn't find the start of the main table")


def parse_second_accusative_row(noun_case_element, row):
    noun_case_element = noun_case_element.getparent()
    noun_case_element = etree.SubElement(noun_case_element, 'genitive')
    noun_case_element.text = util.clean_text(row.find('td').text)


def parse_noun_table_row(row, noun_case_element, noun_case_name):
    """Extracts the singular and plural form from the table row"""
    row_elements = row.find_all('td')
    singular = row_elements[0].text
    if noun_case_name == 'genitive':
        logger.debug('Entering genitive case')
        try:
            plural = util.clean_text(row_elements[1].find('span').text)
        except AttributeError:
            # Not all words has plural forms of the genitive cases
            plural = '—'
    else:
        plural = util.clean_text(row_elements[1].text)
    singular_element = etree.SubElement(noun_case_element, 'singular')
    singular_element.text = util.clean_text(singular)
    plural_element = etree.SubElement(noun_case_element, 'plural')
    plural_element.text = util.clean_text(plural)


########################################
# Verb table parsing
#######################################
person_dict = {
    '1st_sing.': ('first', 'singular'),
    '2nd_sing.': ('second', 'singular'),
    '3rd_sing.': ('third', 'singular'),
    '1st_plur.': ('first', 'plural'),
    '2nd_plur.': ('second', 'plural'),
    '3rd_plur.': ('third', 'plural'),
    'passive': ('passive', 'passive')
}


def parse_verb_table(table_rows):
    logger.debug('Starting verb table parsing')
    table_root = etree.Element('table')
    tense_titles = []
    element_dict = {}
    for i, row in enumerate(table_rows[1:]):
        # Figure out which kind of line we have
        table_headers = row.find_all('th', recursive=False)
        table_cells = row.find_all('td', recursive=False)
        num_table_headers = len(table_headers)
        num_table_cells = len(table_cells)
        logger.debug('Number of headers: {}'.format(num_table_headers))
        logger.debug('Number of table cells: {}'.format(num_table_cells))
        if num_table_cells > 0:
            _parse_verb_inflection_row(
                row, person_dict, tense_titles, table_cells, element_dict)
        elif num_table_headers == 1:
            # New mood
            logger.debug('Starting new mood')
            try:
                mood_element = _create_mood_element(row)
            except LookupError as err:
                if str(err) == 'Nominal form':
                    # Parse the nominal forms and exit
                    nominal_forms_element = _parse_nominal_forms(table_rows, i + 1)
                    table_root.append(nominal_forms_element)
                    logger.debug('Got to the nominal forms. Breaking')
                    break
                else:
                    raise
            else:
                # New mood
                table_root.append(mood_element)
                logger.debug('Parsing new mood: {}'.format(
                    mood_element.text))

        elif num_table_headers == 2:
            # New tenses
            logger.debug('Starting new tenses')
            element_dict, tense_titles = \
                _create_tense_elements(mood_element, table_headers)

        elif num_table_headers == 6:
            logger.debug('Found header row')
            pass
    logger.debug('Finished verb table parsing')
    return table_root


def _clean_verb_table_titles(text):
    """ Connects all words in the title with underscore so they can be used as
    keys.
    """
    clean_title = util.clean_text(text)
    if 'tense' in clean_title:
        clean_title = clean_title.split()[0]
    else:
        clean_title = '_'.join(clean_title.split())  # For some reason a simple str.replace didn't work
    return clean_title


def _create_mood_element(row):
    """ Create the etree node that contains the mood information"""
    mood = _clean_verb_table_titles(row.text)
    if mood == 'Nominal_forms':
        raise LookupError('Nominal form')
    mood_element = etree.Element(mood)
    return mood_element


def _create_tense_elements(mood_element, table_headers):
    tense_titles = [
        _clean_verb_table_titles(table_headers[0].text),
        _clean_verb_table_titles(table_headers[1].text)
    ]
    logger.debug('Starting on new tense pair: {}'.format(str(tense_titles)))
    tense_elements = [etree.SubElement(mood_element, x)
                      for x in tense_titles]
    element_dict = {}
    for tense in tense_elements:
        for feeling in ['positive', 'negative']:
            feel_element = etree.SubElement(tense, feeling)
            for person in ['singular', 'plural', 'passive']:
                element_dict[(tense.tag, feeling, person)] = \
                    etree.SubElement(feel_element, person)
    return element_dict, tense_titles


def _fill_inflection_form_element(key, person, is_passive,
                                  element_dict, text):
    if is_passive:
        new_element = element_dict[key]
    else:
        new_element = etree.SubElement(element_dict[key], person)
    new_element.text = text


def _parse_verb_inflection_row(row, person_dict, tense_titles,
                               table_cells, element_dict):
    person_title = row.find('th').text
    person_title = _clean_verb_table_titles(person_title)
    person, number = person_dict[person_title]
    logger.debug('title, person, number: {}, {}, {}'.format(
        person_title, person, number))
    is_passive = person == 'passive'

    table_column = 0
    for tense in tense_titles:
        for negation in ['positive', 'negative']:
            key = (tense, negation, number)
            text = table_cells[table_column].text.strip()
            _fill_inflection_form_element(
                key, person, is_passive, element_dict, text)
            table_column += 1


def _extract_active_and_passive_forms(cell_values, root_element, offset=1):
    logger.debug('Extracting active and passive forms')
    times = ['active', 'passive']
    for i, time in enumerate(times):
        element = etree.SubElement(root_element, time)
        element.text = util.clean_text(cell_values[i + offset].text)


def _parse_nominal_forms(table_rows, row_id):
    logger.debug('Parsing the nominal forms')
    mood_element = etree.Element('nominal_forms')
    infinitives_element = etree.SubElement(mood_element, 'infinitives')
    participles_element = etree.SubElement(mood_element, 'participles')

    # The first couple of lines needs to be done outside a loop since they
    # are too different from the rest

    start_id = row_id + 3
    _extract_first_two_nominal_form_lines(table_rows, start_id, infinitives_element, participles_element)

    start_id += 2
    _extract_nominal_form_lines_3_to_4(table_rows, start_id, infinitives_element, participles_element)

    start_id += 2
    _extract_third_infinitives(table_rows, start_id, infinitives_element)

    start_id += 6
    _extract_fourth_infinitives(table_rows, start_id, infinitives_element)

    start_id += 2
    _extract_fifth_infinitives(table_rows, start_id, infinitives_element)

    return mood_element


def _extract_first_two_nominal_form_lines(
        table_rows, row_id, infinitives_element, participles_element):
    names = [
        ['first', 'present'],
        ['long_first', 'past']
    ]
    logger.debug('Extracting first two lines of the nominal forms')
    for i, row in enumerate(table_rows[row_id: row_id + 2]):
        cell_values = row.find_all('td')

        infinitive = etree.SubElement(infinitives_element, names[i][0])
        infinitive.text = util.clean_text(cell_values[0].text)

        participle_element = etree.SubElement(participles_element, names[i][1])
        _extract_active_and_passive_forms(cell_values, participle_element)


def _extract_nominal_form_lines_3_to_4(
        table_rows, row_id, infinitives_element, participles_element):
    second_infinitive_element = etree.SubElement(infinitives_element, 'second')
    names = [
        ['inessive', 'instructive'],
        ['agent', 'negative']
    ]
    logger.debug('Extracting third and fourth lines of the nominal forms')
    for i, row in enumerate(table_rows[row_id: row_id + 2]):
        cell_values = row.find_all('td')

        infinitive = etree.SubElement(second_infinitive_element, names[0][i])
        _extract_active_and_passive_forms(cell_values, infinitive, offset=0)

        participle_element = etree.SubElement(participles_element, names[1][i])
        participle_element.text = util.clean_text(cell_values[2].text)


def _extract_third_infinitives(table_rows, row_id, infinitives_element):
    logger.debug('Extracting the third infinitives')
    third_infinitive_element = etree.SubElement(infinitives_element, 'third')
    for i, row in enumerate(table_rows[row_id: row_id + 6]):
        cell_values = row.find_all('td')
        headlines = row.find_all('th')
        if i == 0:
            # First row is special since it also contains the title row for the infinitive
            headlines = list(headlines[1:])
            cell_values = cell_values[:-1]
        name = util.clean_text(headlines[0].text)
        infinitive = etree.SubElement(third_infinitive_element, name)
        _extract_active_and_passive_forms(cell_values, infinitive, offset=0)


def _extract_fourth_infinitives(table_rows, row_id, infinitives_element):
    logger.debug('Extracting the fourth infinitives')
    fourth_infinitive_element = etree.SubElement(infinitives_element, 'fourth')
    for i, row in enumerate(table_rows[row_id: row_id + 2]):
        cell_values = row.find_all('td')
        headlines = row.find_all('th')
        if i == 0:
            # First row is special since it also contains the title row for the infinitive
            headlines = list(headlines[1:])
        name = util.clean_text(headlines[0].text)
        infinitive = etree.SubElement(fourth_infinitive_element, name)
        text = cell_values[0].text
        infinitive.text = util.clean_text(text)


def _extract_fifth_infinitives(table_rows, row_id, infinitives_element):
    logger.debug('Extracting the fifth infinitives')
    element = etree.SubElement(infinitives_element, 'fifth')
    row = table_rows[row_id]
    cell_values = row.find_all('td')
    text = cell_values[0].text
    element.text = util.clean_text(text)


########################################
# Pronoun table parsing
########################################
def parse_pronoun_table(table_rows):
    logger.debug('Starting pronoun table parsing')
    table_root = etree.Element('table')
    for i, row in enumerate(table_rows[1:]):
        logger.debug('Parsing row {}'.format(i + 1))
        case_element = parse_pronoun_table_row(row)
        table_root.append(case_element)
    logger.debug('Finished pronoun table parsing')
    return table_root


def parse_pronoun_table_row(row):
    row_elements = row.find_all('td')
    case_name = util.clean_text(row_elements[0].text)
    singular = util.clean_text(row_elements[1].text)
    plural = util.clean_text(row_elements[2].text)
    case_element = etree.Element(case_name)
    singular_element = etree.SubElement(case_element, 'singular')
    singular_element.text = util.clean_text(singular)
    plural_element = etree.SubElement(case_element, 'plural')
    plural_element.text = util.clean_text(plural)
    return case_element
