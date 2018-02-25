import sr4
import diceroll


def test_simple_roll():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5}}})
    assert sr4.roll('cha1.strength').roll.dices == 4

def test_recipe():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5}}})
    sr4.configure({'recipes': {'hack': {'type': 'simple', 'attrs': ['hacking', 'exploit']}}})
    assert sr4.roll('cha1.hack').roll.dices == 10

def test_recipe_mods():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5}}})
    sr4.configure({'recipes': {'hack': {'type': 'simple', 'attrs': ['hacking', 'exploit'], 'mods': 3}}})
    assert sr4.roll('cha1.hack').roll.dices == 13

def test_roll_data():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5}}})
    sr4.configure({'recipes': {'hack': {'type': 'simple', 'attrs': ['hacking', 'exploit']}}})
    result = sr4.roll('cha1.hack')
    assert result.charname == 'cha1'
    assert result.attrs == [('hacking', 5), ('exploit', 5)]

def test_glitch_not():
    assert not sr4.glitch(diceroll.SuccessRollResult(None, [1, 2, 3], 5))

def test_glitch():
    assert sr4.glitch(diceroll.SuccessRollResult(None, [1, 1, 3], 5))

def test_edge_roll():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5, 'edge': 3}}})
    assert sr4.roll('cha1.strength', edge=True).roll.dices == 7
    assert sr4.roll('cha1.strength', edge=True).roll.explode_on == [6]

def test_positive_mod():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5, 'edge': 3}}})
    assert sr4.roll('cha1.strength', 2).roll.dices == 6

def test_negative_mod():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5, 'edge': 3}}})
    assert sr4.roll('cha1.strength', -2).roll.dices == 2

def test_opposed():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5, 'edge': 3}}})
    result = sr4.roll_opposed('cha1.strength', -2, 5)
    assert result.roll.dices == 2
    assert result.opposed_result.roll.dices == 5
    result.rolls = [5,5]
    result.opposed_result.rolls = [5,5,5,2,2]
    assert result.success() == -1

def test_extended():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5, 'edge': 3}}})
    generator = sr4.roll('cha1.strength', -1, extended=True)
    next(generator)
    assert generator.send((0,False)).roll.dices == 3
    next(generator)
    assert generator.send((0, False)).roll.dices == 2
    next(generator)
    assert generator.send((0, False)).roll.dices == 1
    try:
        next(generator)
        assert False
    except StopIteration:
        pass

def test_extended_recipe():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5}}})
    sr4.configure({'recipes': {'hack': {'type': 'extended', 'attrs': ['hacking', 'exploit']}}})
    generator = sr4.roll('cha1.hack', -1)
    next(generator)
    assert generator.send((0, False)).roll.dices == 9
    next(generator)
    assert generator.send((0, False)).roll.dices == 8

def test_extended_recipe_with_mods_and_edge():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5}}})
    sr4.configure({'recipes': {'hack': {'type': 'extended', 'attrs': ['hacking', 'exploit']}}})
    generator = sr4.roll('cha1.hack', -1)
    next(generator)
    assert generator.send((0, False)).roll.dices == 9
    next(generator)
    result = generator.send((2, True))
    assert result.roll.dices == 10
    assert result.roll.explode_on == [6]
    next(generator)
    result = generator.send((0, False))
    assert result.roll.dices == 7
    assert not hasattr(result.roll, 'explode_on')

def test_default_char():
    sr4.configure({'chars': {'cha1': {'strength': 4, 'hacking': 5, 'exploit': 5}}})
    sr4.configure({'recipes': {'hack': {'type': 'simple', 'attrs': ['hacking', 'exploit']}}})
    sr4.configure({'default_char': 'cha1'})
    assert sr4.roll('hack').roll.dices == 10

