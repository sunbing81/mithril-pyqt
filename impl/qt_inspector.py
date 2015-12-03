from PyQt5.QtWidgets import *

def auto_reparentable(element):
    if isinstance(element, QLayout):
        return True
    else:
        return False
    pass

def suggest_container1(parent, children):
    if isinstance(children, list):
        return 'h_box_layout'
    elif isinstance(children, tuple):
        return 'v_box_layout'

def suggest_container(parent, container_type_hint):
    if isinstance(parent, (QMenu, QMenuBar)):
        if container_type_hint is None:
            #return QActionGroup(parent)
            return 'action_group'
        else:
            return parent
    elif isinstance(parent, QActionGroup):
        return parent
    else:
        if container_type_hint is None:
            return parent if isinstance(parent, QWidget) else parent.parentWidget()
        else:
            if parent is not None and parent.layout() is None:
                return container_type_hint(parent)
            else:
                return container_type_hint()
            pass
        pass
    pass

def find_qt_class(name):
    name_ = name if name.startswith('Q') else 'Q' + name

    if name_ in globals():
        return globals()[name_]
    else:
        raise RuntimeError('Tag "{}" is not a supported widget type.'.format(name))
    return

def get_unbound_attach_method(Parent, Child):
    """Return an unbound method of Parent that will attach the child to the parent.
    """

    method = lambda *args: None

    if Parent is type(None) or Child is type(None):
        pass
    elif issubclass(Parent, QLayout):
        if issubclass(Child, QLayout):
            method = Parent.addLayout
        elif issubclass(Child, QWidget):
            method = Parent.addWidget
        else:
            method = None
    elif issubclass(Child, QLayout):
        pass
    elif issubclass(Child, QMenu):
        if issubclass(Parent, (QMenuBar, QMenu)):
            method = Parent.addMenu
        else:
            method = None
    elif issubclass(Child, QAction):
        method = Parent.addAction
    elif issubclass(Child, QActionGroup):
        method = lambda parent, child: Parent.addActions(parent, child.actions())
    elif issubclass(Parent, QWidget) and issubclass(Child, QWidget):
        ## already attached, but without a layout manager
        pass
    else:
        method = None
        pass

    if method is None:
        raise RuntimeError('Unsupported attach action {} -> {}'.format(Child, Parent))
        pass

    return method

def get_bound_attach_method(parent, child):
    """Return a bound method of type(parent) that binds both parent and child
    """
    return lambda *args, **kwargs: get_unbound_attach_method(type(parent), type(child))(parent, child, *args, **kwargs)

def apply_attach_method(parent, child, *args, **kwargs):
    get_bound_attach_method(parent, child)(*args, **kwargs)
    return

