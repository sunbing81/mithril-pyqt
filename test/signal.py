from config import *

_text = '1111'
def print_text(val):
    global _text
    _text = val
    print(_text)
    return

from PyQt5.QtCore import QObject, pyqtSignal
class Controller(QObject):
    text_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.set_text('2222')
        pass

    def set_text(self, val):
        self.text = val
        self.text_changed.emit(self.text)
        return
    pass
ctrl = Controller()

run([
    ('standard output', m('Widget', [
        label(_text),
        m('line_edit', {'on_text_edited': print_text})
    ])),

    ('connect signal by id (programmable)', m('Widget', [
        m('label#label1', 'init text'),
        m('line_edit', {'on_text_edited': lambda text: m.get_element_by_id('label1').setText(text)})
    ])),

    ('connect signal by id (declarative)', m('Widget', [
        m('label#label2', 'init text'),
        m('line_edit', {'on_text_edited': {'selector': '#label2', 'slot': 'set_text'}})
    ])),

    ('connect signal by id (shortcut)', m('Widget', [
        m('label#label3', 'init text'),
        m('line_edit', {'on_text_edited': {'slot': '#label3::set_text'}})
    ])),

    ('connect signal by id (flatten shortcut)', m('Widget', [
        m('label#label4', 'init text'),
        m('line_edit', {'on_text_edited': '#label4::set_text'})
    ])),

    ('connect by intermediate signal', m('Widget', [
        m('label', {'set_text_on': ctrl.text_changed}),
        m('line_edit', {'on_text_edited': ctrl.set_text})
    ]))
])
