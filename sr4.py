import os
import types
import diceroll
import click
import yaml


config = {
    'roll': 'd6>5',
    'edge_roll': 'd6!>5',
    'chars': {},
    'recipes': {},
}

def configure(new):
    config.update(new)

def character(charname):
    return config['chars'].get(charname, None)

def recipe(recipename):
    return config['recipes'].get(recipename, {'type': 'simple', 'attrs': [recipename]})

def base_roll(charname, attrs, mods, roll_pattern='roll', edge=False):
    if edge:
        roll_pattern = 'edge_roll'
        attrs = attrs + [('edge', character(charname).get('edge', 0))]
    attr_value = sum([v for a, v in attrs]) + mods
    result = diceroll.parse('%d%s' % (attr_value, config[roll_pattern])).roll()
    result.charname = charname
    result.attrs = attrs
    result.mods = mods
    return result

def chained_roll(rolls):
    for charname, attrs, mods, edge in rolls:
        extra_mods, extra_edge = yield
        yield base_roll(charname, attrs, mods + extra_mods, edge or extra_edge)


def extended_roll(charname, attrs, mods):
    runs = 0
    extra_mods, edge = yield
    result = base_roll(charname, attrs, mods + extra_mods, edge=edge)
    yield result
    while result.roll.dices > 1:
        runs += 1
        extra_mods, edge = yield
        result = base_roll(charname, attrs, mods + extra_mods - runs, edge=edge)
        yield result

def roll(stuff, mods=0, edge=False, extended=False):
    charname, stuff = stuff.lower().strip().split('.')
    char = character(charname)
    if not char:
        return

    _recipe = recipe(stuff)
    attrs = _recipe.get('attrs')
    mods += _recipe.get('mods', 0)

    attrs = [(attr, char.get(attr)) for attr in attrs]

    if extended or _recipe.get('type', 'simple') == 'extended':
        return extended_roll(charname, attrs, mods)
    return base_roll(charname, attrs, mods, edge=edge)

def roll_opposed(stuff, mods=0, opposition=0, edge=False):
    result = roll(stuff, mods, edge)

    result.opposed_result = diceroll.parse('%d%s' % (opposition, config['roll'])).roll()

    result._success = result.success
    result.success = lambda: result._success() - result.opposed_result.success()
    return result

def glitch(result):
    return len([x for x in result.rolls if x == 1]) >= (len(result.rolls)/2.0)


def echo(result, verbose=False):
    if verbose:
        click.echo('Character: %s' % result.charname)
        for attr, attr_value in result.attrs:
            click.echo('\t%s: %d' % (attr, attr_value))
        if result.mods:
            click.echo('Total modifiers: %d' % result.mods)
        click.echo('DICE ROLLS (%d): %s' % (result.roll.dices, ', '.join(map(str, result.rolls))))
        if hasattr(result, 'opposed_result'):
            click.echo('OPPOSED ROLLS (%d): %s' % (result.opposed_result.roll.dices, ', '.join(map(str, result.opposed_result.rolls))))
            click.echo('OPPOSED NET HITS: %d' % (result.opposed_result.success()))

    if result.success():
        click.echo('NET HITS: %d' % result.success())
    else:
        click.echo('FAIL!')

    if glitch(result):
        if result.success():
            click.echo(click.style('*** GLITCH ***', fg='red'))
        else:
            click.echo(click.style('*** CRITICAL GLITCH! ***', fg='white', bg='red'))


def is_int(x):
    try:
        int(x)
        return True
    except:
        return False

def extended_params():
    click.echo()
    while True:
        value = [x for x in click.prompt('Continue? (help for more)', default='Y').lower().strip().split(' ') if x]
        click.echo()

        if 'help' in value:
            click.echo('  split params with space:')
            click.echo('    e/edge  = use edge in this roll')
            click.echo('    any int = specific mod for this roll (+/-)')
            click.echo('    n/no    = stop the extended test')
            click.echo('    <ENTER> or anything else to continue as is')
            continue

        if 'n' in value or 'no' in value:
            return None

        mods = sum([int(x) for x in value if is_int(x)])
        edge = 'edge' in value or 'e' in value
        return (mods, edge)


@click.command()
@click.argument('stuff')
@click.argument('mods', default=0.0, type=float)
@click.option('-v', '--verbose', is_flag=True)
@click.option('-e', '--edge', is_flag=True)
@click.option('-o', '--opposed', default=0, type=int)
@click.option('-x', '--extended', default=0, type=int)
def roll_cmd(stuff, mods, verbose, edge, opposed, extended):
    if mods < 1.0:
        mods = -10 * mods
    mods = int(mods)

    if opposed:
        echo(roll_opposed(stuff, mods, opposed, edge), verbose=verbose)
    else:
        result = roll(stuff, mods, edge, extended=extended>0)
        if isinstance(result, types.GeneratorType):
            total_net_hits = 0
            for i,_ in enumerate(result):
                if i == 0:
                    _result = result.send((0, edge))
                else:
                    params = extended_params()
                    if not params:
                        break
                    _result = result.send(params)

                click.echo('%d# EXTENDED ROLL (%d)' % (i+1, _result.roll.dices))
                echo(_result, verbose=verbose)
                total_net_hits += _result.success()
                click.echo('TOTAL NET HITS: %d' % total_net_hits)
                if _result.roll.dices == 1:
                    break
        else:
            echo(result, verbose=verbose)


if __name__ == '__main__':
    if os.path.isfile('sr4-config.yml'):
        with open('sr4-config.yml', 'r') as configfile:
            configure(yaml.load(configfile))

    roll_cmd()
