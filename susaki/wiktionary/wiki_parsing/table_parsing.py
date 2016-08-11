import re

import logging

from lxml import etree

FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.INFO, format=FORMAT)
logger = logging.getLogger('__name__')


########################################
# Utility functions
########################################
def clean_text(text):
    """ Removes line break characters and unneeded spaces from the text
    """
    clean = text.replace('\n', '')
    clean = clean.strip()
    clean = re.sub(r'  *', ' ', clean)
    return clean


########################################
# Meta info parsing
########################################
def parse_meta_information(headline_row):
    logger.debug('Extracting meta info from table')
    headline_element = headline_row.th
    headline_text = headline_element.text
    logger.debug('Headline text: {}'.format(headline_text))
    word, kotus_type, kotus_word, gradation = extract_meta_information(headline_text)
    meta_element = create_meta_tree(word, kotus_type, kotus_word, gradation)
    return meta_element


def extract_meta_information(headline_text):
    """ Extract meta information from the headline text"""
    meta_info = re.match(r' *Inflection of (\w+) \(Kotus type (\d\d?)/(\w+), (.*) gradation\)', headline_text)
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
    logger.debug('Inflection table type: Noun')
    table_root = etree.Element('table')
    in_accusative = False
    noun_case_element = None

    start_row = find_noun_table_start(rows)

    for i, row in enumerate(rows[start_row:]):
        logger.debug('Parsing row {}'.format(i + start_row))
        noun_case_name = row.th.text
        noun_case_name = clean_text(noun_case_name)
        logger.debug('Creating new noun case element: {}'.format(
            noun_case_name))
        noun_case_element = etree.Element(noun_case_name)
        if in_accusative:
            logger.debug('Entering second accusative row (genitive)')
            parse_second_accusative_row(noun_case_element, row)
            in_accusative = False
        else:
            table_root.append(noun_case_element)
            if noun_case_name == 'accusative':
                logger.debug('Found the accusative case')
                in_accusative = True
                noun_case_element = etree.SubElement(
                    noun_case_element, 'nominative')
            parse_noun_table_row(
                row, noun_case_element, noun_case_name)
    return table_root


def find_noun_table_start(rows):
    """ The noun table has to parts. The first part contains nominative,
    genitive, partitive and illative.
    After these four cases the main table begins and those four cases
    are repeated there but not in the same other. Because of this we want to
    ignore the first lines and first start parsing on the main table.
    Rows: The rows of the table
    Returns: the id of the row where the first entry of the main table exists.
             (After the table headers)
    """
    logger.debug('Starting search for the main table')
    for i, row in enumerate(rows[1:]):
        noun_case_name = row.th.text
        noun_case_name = clean_text(noun_case_name)
        try:
            etree.Element(noun_case_name)
        except ValueError as err:
            if str(err) == 'Empty tag name':
                # We found the headers of the real table
                logger.debug('Found the table headers')
                return i + 1
            else:
                raise
    raise ValueError("Couldn't find the start of the main table")


def parse_second_accusative_row(noun_case_element, row):
    noun_case_element = noun_case_element.getparent()
    noun_case_element = etree.SubElement(noun_case_element, 'genitive')
    noun_case_element.text = clean_text(row.find('td').text)


def parse_noun_table_row(row, noun_case_element, noun_case_name):
    """Extracts the singular and plural form from the table row"""
    row_elements = row.find_all('td')
    singular = row_elements[0].text
    if noun_case_name == 'genitive':
        logger.debug('Entering genitive case')
        plural = clean_text(row_elements[1].find('span').text)
    else:
        plural = clean_text(row_elements[1].text)
    singular_element = etree.SubElement(noun_case_element, 'singular')
    singular_element.text = clean_text(singular)
    plural_element = etree.SubElement(noun_case_element, 'plural')
    plural_element.text = clean_text(plural)


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
    logger.debug('Inflection table type: verb')
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
            try:
                mood_element = _create_mood_element(row)
            except LookupError as err:
                if str(err) == 'Nominal form':
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
            element_dict, tense_titles = _create_tense_elements(
                mood_element, table_headers)

        elif num_table_headers == 6:
            logger.debug('Header row')
            pass
    return table_root


def _clean_verb_table_titles(text):
    """ Connects all words in the title with underscore so they can be used as
    keys.
    """
    clean_title = clean_text(text)
    if 'tense' in clean_text:
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

    logger.debug('Element dict: {}'.format(str(element_dict)))
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
    logger.debug('table cells: {}'.format(row.text))
    person_title = row.find('th').text
    logger.debug('Dirty title: {}'.format(person_title))
    person_title = _clean_verb_table_titles(person_title)
    logger.debug('Clean title: {}'.format(person_title))
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
    times = ['active', 'passive']
    for i, time in enumerate(times):
        element = etree.SubElement(root_element, time)
        element.text = clean_text(cell_values[i + offset].text)


def _extract_first_two_nominal_form_lines(table_rows, row_id, infinitives_element, participles_element):
    names = [
        ['first', 'present'],
        ['long_first', 'past']
    ]
    for i, row in enumerate(table_rows[row_id: row_id + 2]):
        cell_values = row.find_all('td')

        infinitive = etree.SubElement(infinitives_element, names[i][0])
        infinitive.text = clean_text(cell_values[0].text)

        participle_element = etree.SubElement(participles_element, names[i][1])
        _extract_active_and_passive_forms(cell_values, participle_element)


def _extract_nominal_form_lines_3_to_4(table_rows, row_id, infinitives_element, participles_element):
    second_infinitive_element = etree.SubElement(infinitives_element, 'second')
    names = [
        ['inessive', 'instructive'],
        ['agent', 'negative']
    ]
    for i, row in enumerate(table_rows[row_id: row_id + 2]):
        cell_values = row.find_all('td')

        infinitive = etree.SubElement(second_infinitive_element, names[0][i])
        _extract_active_and_passive_forms(cell_values, infinitive, offset=0)

        participle_element = etree.SubElement(participles_element, names[1][i])
        participle_element.text = clean_text(cell_values[2].text)


def _extract_third_infinitives(table_rows, row_id, infinitives_element):
    third_infinitive_element = etree.SubElement(infinitives_element, 'third')
    for i, row in enumerate(table_rows[row_id: row_id + 6]):
        cell_values = row.find_all('td')
        headlines = row.find_all('th')
        if i == 0:
            # First row is special since it also contains the title row for the infinitive
            headlines = list(headlines[1:])
            cell_values = cell_values[:-1]
        name = clean_text(headlines[0].text)
        infinitive = etree.SubElement(third_infinitive_element, name)
        _extract_active_and_passive_forms(cell_values, infinitive, offset=0)


def _extract_fourth_infinitives(table_rows, row_id, infinitives_element):
    fourth_infinitive_element = etree.SubElement(infinitives_element, 'fourth')
    for i, row in enumerate(table_rows[row_id: row_id + 2]):
        cell_values = row.find_all('td')
        headlines = row.find_all('th')
        if i == 0:
            # First row is special since it also contains the title row for the infinitive
            headlines = list(headlines[1:])
        name = clean_text(headlines[0].text)
        infinitive = etree.SubElement(fourth_infinitive_element, name)
        text = cell_values[0].text
        infinitive.text = clean_text(text)


def _extract_fifth_infinitives(table_rows, row_id, infinitives_element):
    element = etree.SubElement(infinitives_element, 'fifth')
    row = table_rows[row_id]
    cell_values = row.find_all('td')
    text = cell_values[0].text
    element.text = clean_text(text)


def _parse_nominal_forms(table_rows, row_id):
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


########################################
# Adjective table parsing
########################################
