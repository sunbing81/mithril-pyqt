from config import *

run([
    ('H', m('Widget', [label('1'), label('2'), label('3')])),
    ('V', m('Widget', (label('1'), label('2'), label('3')))),

    ('HH', m('Widget', [
        [label('1'), label('2'), label('3')],
        [label('4'), label('5'), label('6')],
    ])),
    ('HV', m('Widget', [
        (label('1'), label('2'), label('3')),
        (label('4'), label('5'), label('6')),
    ])),
    ('VH', m('Widget', (
        [label('1'), label('2'), label('3')],
        [label('4'), label('5'), label('6')],
    ))),
    ('VV', m('Widget', (
        (label('1'), label('2'), label('3')),
        (label('4'), label('5'), label('6')),
    ))),

    ## ambiguous: setSpacing or addSpacing?
    #('H+config', m('Widget', [{'spacing': 20,}])),

    ('H+config', m('Widget', [  # [] denotes a HBox by default
        {
            'layout': 'v_box',  # but use VBox instead
            'spacing': 20,      # setSpacing
        },

        label('1'),             # item begin
        label('2'),
        {'spacing': 60},        # addSpacing
        label('3')
    ])),

    ('H+item', m('Widget', [label('1'), 'stretch', label('2'), label('3')])),
    ('H+item(arg)', m('Widget', ['stretch', label('1'), {'spacing': 80}, label('2'), label('3')])),
])
