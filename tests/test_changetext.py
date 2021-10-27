import changetext

from changetext import ChangeText


class TestTags:
    def test_not_tags(self):
        # проверка ложных срабатываний:
        assert ChangeText("<-") is None
        assert ChangeText("<1в") is None
        assert ChangeText(" <> ") is None

    def test_invalid_tags(self):
        assert ChangeText('asdfa <aeger:etrhrt> ehsge') == 'asdfa etrhrt ehsge'
        assert ChangeText('asdfa <aeger> ehsge') == 'asdfa ehsge'

    def test_tag_wrap(self):
        ChangeText('whatever <gent>')
        assert ChangeText('голова') == 'головы'

    def test_capitalize_tag(self):
        assert ChangeText("<capitalize>капитан ополчения встаёт.") == "Капитан ополчения встаёт."

    def test_consecutive_tags(self):
        assert (ChangeText('Она   гражданин   <gent>   <capitalize>    Ochre   Girders.   Она   член   <gent>')
                == 'Она   гражданин Ochre   Girders.   Она   член')
        changetext.init()
        assert (ChangeText('Она  гражданин  <gent>  <capitalize>  Livid Dyes.  Она  член <gent>  <capitalize>')
                == 'Она  гражданин Livid Dyes.  Она  член')

    def test_tag_spaces(self):
        changetext.init()
        assert (ChangeText('Lyrical Wisp. По  возможности она предпочитает употреблять<accs>  ячий сыр и')
                == 'Lyrical Wisp. По  возможности она предпочитает употреблять ячий сыр и')
        assert (ChangeText('вино из плодов восковницы. Она совершенно не выносит<accs> комары.')
                == 'вино из плодов восковницы. Она совершенно не выносит комаров.')
        assert ChangeText('Anurnir, " <capitalize> Wondrous Land"') == 'Anurnir, "Wondrous Land"'

    def test_commas(self):
        assert ChangeText('летящий {+железный болт+} бьёт <accs> индюк в <accs> голова, разрывая <accs>') == \
                          'летящий {+железный болт+} бьёт индюка в голову, разрывая'


def test_corr_color_of_color():
    assert ChangeText("цвет серебристого цвета") == "серебристый цвет"
    assert ChangeText("цвет цвета морской волны") == "цвет морской волны"


def test_corr_contextual():
    ChangeText('  Dwarf Fortress  ')  # switch to the 'main' context
    assert ChangeText('Повар') in {'Повар', None}
    assert ChangeText('Рыба') in {'Рыба', None}

    ChangeText('Овощи/фрукты/листья')  # switch to the 'kitchen' context
    assert ChangeText('Повар') == 'Готовить'

    ChangeText('Граждане (10)')  # switch to the 'units' context
    assert ChangeText('Рыба') == 'Рыбачить'


def test_corr_has_verb():
    # Test 'has' + verb fix
    assert ChangeText(' имеет создал ') == ' создал '
    assert ChangeText(' имеет пришёл ') == ' пришёл '
    assert ChangeText(' имеет упал ') == ' упал '
    assert ChangeText(' имеет стрямкал ') == ' стрямкал '
