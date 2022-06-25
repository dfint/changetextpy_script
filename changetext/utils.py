import functools
import re

import pymorphy2

morph = pymorphy2.MorphAnalyzer()
unwanted_tags = ("Name", "Surn", "Infr")


def custom_parse(text):
    if text.lower().startswith("адамантин"):
        return morph.parse(text)  # Pymorphy2 thinks that adamantine is a surname and treats it properly
    else:
        return [p for p in morph.parse(text) if all(tag not in p.tag for tag in unwanted_tags)]


def tag_to_set(tag):
    return set(sum((ss.split() for ss in str(tag).split(",")), list()))


def common_tags(parse):
    common = tag_to_set(parse[0].tag)
    for p in parse[1:]:
        common &= tag_to_set(p.tag)
    return common


def any_in_tag(gram, parse):
    return any(gram in p.tag for p in parse)


def is_adjective(word: str, parse=None):
    if parse is None:
        parse = custom_parse(word)
    return any("ADJF" in p.tag or "PRTF" in p.tag for p in parse)


def inflect_collocation(s, tags):
    # print('inflect_collocation(%r, %r)' % (s, tags))
    words = [x for x in s.split(" ") if x]  # skip empty strings
    j = None
    main_word = None
    for i, word in enumerate(words):
        parse = custom_parse(word)
        if any_in_tag({"NOUN"}, parse):
            p0 = next(p for p in parse if {"NOUN"} in p.tag)
            p = p0.inflect(tags)
            assert p is not None, p0
            words[i] = p.word if word[0].islower() else p.word.capitalize()
            j = i
            main_word = p
            break

    if main_word:
        if main_word.tag.number == "plur":
            tags.add("plur")
        else:
            tags.add(main_word.tag.gender)

        if "accs" in tags and "plur" not in tags and "masc" in tags:
            tags.add(main_word.tag.animacy)

    for i, word in enumerate(words[:j]):
        parse = custom_parse(word)
        if not is_adjective(word, parse):
            raise ValueError("%s is not an adjective" % word)
        p = next(p for p in parse if {"ADJF"} in p.tag)
        # print(p)
        # print(tags)
        p = p.inflect(tags)
        words[i] = p.word

    # print(words)
    return " ".join(words) + (" " if s.endswith(" ") else "")


re_number = re.compile(r"^(\d+)(.*)")


def cut_number(text):
    search_result = re_number.search(text)
    return search_result.group(1), search_result.group(2)


re_sentence = re.compile(r'^([^\.!"]*)([\.!"].*)$')


def split_sentence(text):
    sentence = re_sentence.search(text)
    if sentence:
        return sentence.groups()
    else:
        return text, ""


def is_enumeration_delimiter(text):
    return text in {",", " и "}


def any_cyr(text):
    return any("а" <= x <= "я" or x == "ё" for x in text.lower())


def add_spaces(text_parts):
    add_space = False
    for part in text_parts:
        part = part.strip()
        if part:
            if add_space and part[0].isalnum():
                part = " " + part

            yield part
            if part[-1] not in set('"('):
                add_space = True


def smart_join(text_parts):
    return "".join(add_spaces(text_parts))


re_split_enumeration = re.compile(r"(,| и )")


def _inflect_enumeration(text, form):
    do_not_inflect = False
    for part in re_split_enumeration.split(text):
        if is_enumeration_delimiter(part) or do_not_inflect:
            yield part
        else:
            try:
                part = inflect_collocation(part, form)
            except ValueError:
                do_not_inflect = True
            yield part


def inflect_enumeration(s, form):
    return smart_join(_inflect_enumeration(s, form))


def get_form(word):
    common = common_tags(custom_parse(word))
    if "plur" in common:
        common -= {"masc", "femn", "neut"}
    if "masc" not in common:
        common -= {"anim", "inan"}
    return {tag for tag in ["sing", "plur", "masc", "femn", "neut", "anim", "inan"] if tag in common}


make_adjective = {
    # металл
    "из меди": "медный",
    "из железа": "железный",
    "из серебра": "серебряный",
    "из бронзы": "бронзовый",
    "из стали": "стальной",
    "из золота": "золотой",
    "из никеля": "никелевый",
    "из цинка": "цинковый",
    "из латуни": "латунный",
    "из чугуна": "чугунный",
    "из платины": "платиновый",
    "из электрума": "электрумный",
    "из олова": "оловянный",
    "из свинца": "свинцовый",
    "из алюминия": "алюминиевый",
    "из нейзильбера": "нейзильберовый",
    "из биллона": "билонный",
    "из стерлинга": "стерлинговый",
    "из висмута": "висмутовый",
    "из адамантина": "адамантиновый",
    # дерево
    "из сосны": "сосновый",
    "из кедра": "кедровый",
    "из дуба": "дубовый",
    "дуб": "дубовый",
    "из ореха": "ореховый",
    "из клёна": "кленовый",
    "клён": "кленовый",
    "из ивы": "ивовый",
    "из мангров": "мангровый",
    "из пальмы": "пальмовый",
    "из лиственницы": "лиственничный",
    "из каштана": "каштановый",
    "из ольхи": "ольховый",
    "из берёзы": "берёзовый",
    "из лумбанга": "лумбанговый",
    # неорганическое
    "из кремня": "кремневый",
    "из аргиллита": "аргилитовый",
    "из песчаника": "песчаниковый",
    "из алевролита": "алевролитовый",
    "из сланца": "сланцевый",
    "из известняка": "известняковый",
    "из конгломерата": "конгломератный",
    "из доломита": "доломитовый",
    "из мела": "меловый",
    "из гранита": "гранитный",
    "из диорита": "диоритовый",
    "из габбро": "габбровый",
    "из риолита": "риолитовый",
    "из базальта": "базальтовый",
    "из андезита": "андезитовый",
    "из дацита": "дацитовый",
    "из обсидиана": "обсидиановый",
    "из кварцита": "кварцитовый",
    "из филита": "филитовый",
    "из гнейса": "гнейсовый",
    "из мрамора": "мраморный",
    "из каменной глины": "из каменной глины",
    "из каменной соли": "из каменной соли",
    "из грифельного сланца": "из грифельного сланца",
    "из аспидного сланца": "из аспидного сланца",
    # неорганические камни минералы
    "из красного железняка": "из красного железняка",
    "из бурого железняка": "из бурого железняка",
    "из самородного золота": "из самородного золота",
    "из гарниерита": "гарниеритовый",
    "из самородной меди": "из самородной меди",
    "из малахита": "малахитовый",
    "из галенита": "галенитовый",
    "из сфалерита": "сфалеритовый",
    "из касситерита": "касситеритовый",
    "из каменного угля": "из каменного угля",
    "из бурого угля": "из бурого угля",
    "из самородной платины": "из самородной платины",
    "из киновари": "киноварный",
    "из кобальтита": "кобальтитовый",
    "из тетраэдрита": "тетраэдритовый",
    "из рогового серебра": "из рогового серебра",
    "из гипса": "гипсовый",
    "из талька": "тальковый",
    "из гагата": "гагатовый",
    "из пудингового конгломерата": "из пудингового конгломерата",
    "из окаменелой древесины": "из окаменелой древесины",
    "из графита": "графитовый",
    "из серы": "серный",
    "из кимберлита": "кимберлитовый",
    "из висмутина": "висмутиновый",
    "из реальгара": "реальгаровый",
    "из аурипигмента": "аурипигментовый",
    "из стибнита": "стибнитовый",
    "из марказита": "марказитовый",
    "из сильвина": "сильвиновый",
    "из криолита": "криолитовый",
    "из периклаза": "периклазовый",
    "из ильменита": "ильменитовый",
    "из рутила": "рутиловый",
    "из магнетита": "магнетитовый",
    "из хромита": "хромитовый",
    "из пиролюзита": "пиролюзитовый",
    "из уранинита": "уранинитовый",
    "из боксита": "бокситовый",
    "из самородного алюминия": "из самородного алюминия",
    "из буры": "буровый",
    "из оливина": "оливиновый",
    "из роговой обманки": "из роговой обманки",
    "из каолинита": "каолинитовый",
    "из серпентина": "серпентиновый",
    "из ортоклаза": "ортоклазовый",
    "из микроклина": "микроклиновый",
    "из слюды": "слюдяной",
    "из кальцита": "кальцитовый",
    "из селитры": "селитровый",
    "из алебастра": "алебастровый",
    "из селенита": "селенитовый",
    "из шелковистого шпата": "из шелковистого шпата",
    "из ангидрита": "ангедритовый",
    "из алунита": "алунитовый",
    "из необработанного адамантина": "из необработанного адамантина",
    "из слейда": "слейдовый",
    # стекло и камни из одного слова
    "хрусталь": "из хрусталя",
    "морион": "из мориона",
    "моховой опал": "из мохового опала",
    "шерл": "из шерла",
    "лазурит": "из лазурита",
    "прозапал": "из прозапала",
    "кровавик": "из кровавика",
    "моховой агат": "из мохового агата",
    "хризопраз": "из хризопраза",
    "сердолик": "из сердолика",
    "вишнёвый опал": "из вишнёвого опала",
    "пейзажная яшма": "из пейзажной яшмы",
    "дымчатый кварц": "из дымчатого кварца",
    "цитрин": "из цитрина",
    "смолистый опал": "из смолистого опала",
    "пирит": "из пирита",
    "чистый турмалин": "из чистого турмалина",
    "серый халцедон": "из серого халцедона",
    "ракушечный опал": "из ракушечного опала",
    "костяной опал": "из костяного опала",
    "бастионный агат": "из бастионного агата",
    "молочный кварц": "из молочного кварца",
    "лунный камень": "из лунного камня",
    "яшмовый опал": "из яшмого опала",
    "ониксовый опал": "из ониксового опала",
    "горный хрусталь": "из горного хрусталя",
    "сардоникс": "из сардоникса",
    "чёрный циркон": "из чёрного циркона",
    "чёрный пироп": "из чёрного пиропа",
    "индиговый турмалин": "из индигового турмалина",
    "синий гранат": "из синего граната",
    "зелёный турмалин": "из зелёного турмалина",
    "демантоид": "из демантоида",
    "зелёный циркон": "из зелёного циркона",
    "красный циркон": "из красного циркона",
    "красный турмалин": "из красного турмалина",
    "красный пироп": "из красного пиропа",
    "биксбит": "из биксбита",
    "пурпурная шпинель": "из пурпурной шпинели",
    "александрит": "из александрита",
    "морганит": "из морганита",
    "фиолетовый спессартин": "из фиолетового спессартина",
    "кунцит": "из кунцита",
    "голиодор": "из голиодора",
    "жилейный опал": "из жилейного опала",
    "коричневый циркон": "из коричневого опала",
    "жёлтый циркон": "из жёлтого циркона",
    "жёлтый спессартин": "из жёлтого спессартина",
    "топаз": "из топаза",
    "рубицелл": "из рубицелла",
    "гошенит": "из гошенита",
    "кошачий глаз": "из кошачего глаза",
    "чистый циркон": "из чистого циркона",
    "аметист": "из аметиста",
    "аквамарин": "из аквамарина",
    "красная шпинель": "из красной шпинели",
    "хризоберилл": "из хризоберилла",
    "кристаллический опал": "из кристаллического опала",
    "опал арлекин": "из опала-арлекина",
    "слоистый огненный опал": "из слоистого огненного опала",
    "изумруд": "из изумруда",
    "зеленое стекло": "из зеленого стекла",
    "бесцветное стекло": "из бесцветного стекла",
    "гелиодор": "из гелиодора",
    "желейный опал": "из желейного опала",
    "лавандовый нефрит": "из лавандового нефрита",
    "розовый нефрит": "из розового нефрита",
    "восковой опал": "из воскового опала",
    "янтарный опал": "из янтарного опала",
    "золотистый опал": "из золотистого опала",
    "празеолит": "из празеолита",
    "белый нефрит": "из белого нефрита",
    "ананасовый опал": "из ананасового опала",
    "трубчатый опал": "из трубчатого опала",
    "авантюрин": "из авантюрина",
    "розовый кварц": "из розового кварца",
    "зелёный нефрит": "из зелёного нефрита",
    "альмандин": "из альмандина",
    "розовый турмалин": "из розового турмалина",
    "огненный опал": "из огненного опала",
    "родолит": "из родолита",
    "танзанит": "из танзанита",
    "золотистый берилл": "из огненного опала",
    "топазолит": "из топазолита",
    "чистый гранат": "из чистого граната",
    "чёрный опал": "из чёрного опала",
    "светло-жёлтый алмаз": "из светло-жёлтого алмаза",
    "зелeное стекло": "из зеленого стекла",
    "прозрачное стекло": "из прозрачного стекла",
    "белый халцедон": "из белого халцедона",
    # размеры и др
    "большой": "большой",
    "гигантский": "гигантский",
    "заточенный": "заточенный",
    "огромный": "огромный",
    "шипованный": "шипованный",
    "зазубренный": "зазубренный",
    "кольчужный": "кольчужный",
    "изысканный": "изысканный",
    "большой,": "большой",
    "грубый": "грубый",
    # Формы огранки
    "бриолетовый": "бриолетовый",
    "огранённый розой": "огранённый розой",
    "огранённый подушечкой": "огранённый подушечкой",
    "плоскогранный": "плоскогранный",
    "прямоугольный": "прямоугольный",
    "гладкий": "гладкий",
    "овальный": "овальный",
    "круглый": "круглый",
    "сглаженный": "сглаженный",
    # кожа, шёлк
    "из кожи": "кожаный",
    "из шёлка": "шёлковый",
    "шёлк": "шёлковый",
    # разные материалы
    "металл": "металлический",
    "кожа": "кожаный",
    "растительное волокно": "из растительного волокна",
    "дерево": "деревянный",
    "кость": "костяной",
    "камень": "каменный",
}
dict_ending_s = {
    "готовая еда": "готовая еда",
    "питьё": "питьё",
    "стул": "стулья",
    "доспешная стойка": "доспешные стойки",
    "оружейная стойка": "оружейные стойки",
    "дублёная шкура": "дублёные шкуры",
    "большой самоцвет": "большие самоцветы",
    "баклер": "баклеры",
    "оружие": "оружие",
    "крышка люка": "крышки люка",
    "ручная мельница": "ручные мельницы",
    "ловушка для животных": "ловушки для животных",
    "часть ловушки": "части ловушек",
    "музыкальный инструмент": "музыкальные инструменты",
    "наконечник стрелы баллисты": "наконечники стрелы баллисты",
    "часть тела": "части тела",
    "конечность/тело гипс": "гипс для конечностей тела",
    "Элитный борец": "Элитные борцы",
    "Лорд топора": "Лорды топора",
    "Лорд булавы": "Лорды булавы",
    "Лорд молота": "Лорды молота",
    "Мастер меча": "Мастера меча",
    "Мастер копья": "Мастера копья",
}
gender_exceptions = {
    "шпинель": "femn",
    "гризли": "masc",
}


def pm_gender(parse):
    tag = parse.tag
    # print(tag)
    if tag.number == "plur":
        gender = tag.number
    else:
        gender = tag.gender
    # print(gender)
    return str(gender)  # explicitly convert to a string any internal types returned from pymorphy2


def get_gender(obj, known_tags=None):
    # print("get_gender(%r, known_tags=%r)" % (obj, known_tags))
    assert " " not in obj, "get_gender() is not suitable for word collocations"

    if "-" in obj:
        obj = obj.split("-")
        if obj[0] in {"мини"}:
            obj = obj[1]
            # print('Using the second part of the hyphen-compound: %r' % obj)
        else:
            obj = obj[0]
            # print('Using the first part of the hyphen-compound: %r' % obj)

    parse = custom_parse(obj)
    if known_tags is not None:
        parse = [p for p in parse if known_tags in p.tag]

    if obj.lower() in gender_exceptions:
        return gender_exceptions[obj.lower()]
    else:
        if len(parse) > 0:
            gender = pm_gender(parse[0])
            for p in parse:
                if pm_gender(p) != gender:
                    # print("Gender cannot be recognized definitely for %r. Try to specify known tags (eg. case)" % obj)
                    return None
        else:
            # print("Gender not recoginzed for %r" % obj)
            return None
        return pm_gender(parse[0])


def get_main_word_gender(text):
    if " " not in text:
        return get_gender(text, known_tags={"nomn"})
    else:
        for word in text.split():
            if any_in_tag({"NOUN", "nomn"}, custom_parse(word)):
                return get_gender(word, known_tags={"NOUN", "nomn"})


def parse_as_adjective(adjective: str) -> list:
    parse = [p for p in custom_parse(adjective) if "ADJF" in p.tag or "PRTF" in p.tag]
    assert len(parse) > 0, "parse: %r" % parse
    return parse


def inflect_adjective(adjective: str, gender: str, case="nomn", animated=None):
    # print('inflect_adjective(%s, %s)' % (adjective, case))
    assert gender is not None
    parse = parse_as_adjective(adjective)
    p = parse[0]
    form_set = {gender, case}
    if animated is not None and gender in {"masc", "plur"}:
        form_set.add("anim" if animated else "inan")
    # print('form_set:', form_set)
    new_form = p.inflect(form_set)
    if new_form is None:
        form_set = {gender, case}
        # print('form_set:', form_set)
        new_form = p.inflect(form_set)
    ret = new_form.word
    # print('%s -> %s' % (adjective, ret))
    return ret


gent_case_except = {
    "шпинель": "шпинели",  # определяет как сущ. м.р.
    "стена": "стены",  # определяет как сущ. м.р.
    "лиса": "лисы",  # определяет как сущ. м.р.
    "споры": "спор",  # в родительный падеж ставит как "споров"
}


def inflect_noun(word: str, case: str, orig_form=None):
    # print('inflect_noun(%r, %r, %r)' % (word, case, orig_form))
    parse = list(filter(lambda x: x.tag.POS == "NOUN", custom_parse(word)))

    if orig_form:
        parse = [p for p in parse if orig_form in p.tag]

    if len(parse) == 0:
        # print('Failed to set %r to %s case.' % (word, case))
        return None

    new_form = parse[0].inflect({case})

    return new_form.word


def genitive_case_single_noun(word: str):
    # print('genitive_case_single_noun')
    # print(word)
    if word.lower() in gent_case_except:
        return gent_case_except[word.lower()]
    else:
        return inflect_noun(word, case="gent")


def genitive_case_list(words: list):
    # print("genitive_case_list(%r)" % words)
    if len(words) == 1:
        gender = get_gender(words[0], {"nomn"})
    else:
        gender = None
        for word in words:
            if any_in_tag({"NOUN", "nomn"}, custom_parse(word)):
                gender = get_gender(word, {"NOUN", "nomn"})
                break
        assert gender is not None

    for word in words:
        if is_adjective(word):
            word = inflect_adjective(word, gender, "gent")
        else:
            word = genitive_case_single_noun(word)
        assert word is not None
        yield word


def genitive_case(word: str):
    return " ".join(genitive_case_list(word.split()))


opening = {"!", "(", "*", "+", "-", "[", "{", "«", "р", "☼", "X", "x"}
closing = {"«": "»", "[": "]", "(": ")", "{": "}"}


def open_brackets(func):
    @functools.wraps(func)
    def wrapper(text):
        start_i = 0
        end_i = len(text) - 1
        for c in text:
            if c in opening:
                start_i += 1
                if text[end_i] == closing.get(c, c):
                    end_i -= 1
            else:
                break

        if (
            start_i > 0
            and text[start_i - 1] == "р"
            and (end_i == len(text) - 1 or text[end_i + 1] != "р")
            and not text[start_i:].startswith("из")
        ) and not text[start_i].isupper():
            start_i -= 1

        leading_symbols = text[:start_i].replace("р", "≡")
        trailing_symbols = text[end_i + 1 :].replace("р", "≡")

        return leading_symbols + func(text[start_i : end_i + 1]) + trailing_symbols

    return wrapper
