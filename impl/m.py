import impl.cell
import impl.qt_inspector
import impl.util

def m(tag, *args):
    ## self
    cell = impl.cell.make_cell({})

    ## parse args in reverse order
    # for list::pop()
    args = list(args)

    ## attached children: a list, tuple, or _Cell
    if args and impl.cell.can_be_coverted_to_children_cells(args[-1]):
        cell['children'] = impl.cell.make_cell(args.pop())
        pass

    ## attributes for the tag: a dict
    if args and isinstance(args[-1], dict):
        cell['attrs'] = args.pop()
        pass

    ## extract tag and its arguments
    if not isinstance(tag, tuple):
        tag = (tag,)
        pass

    ## parse tag string
    tag_name = tag[0]
    if isinstance(tag[0], str):
        ## extract tag id
        splitted = tag[0].split('#')
        if len(splitted) == 2:
            tag_name = splitted[0]
            cell['attrs'] = cell.get('attrs', {})
            cell['attrs']['id'] = splitted[1]
        elif len(splitted) == 1:
            pass
        else:
            raise RuntimeError('malformat tag name: {}'.format(tag[0]))

        ## pythonic tag name
        tag_name = impl.util.snake_to_camel(tag_name, capitalize_first=True)
        pass

    ## set tag
    cell['tag'] = (tag_name,) + tag[1:] + tuple(args)

    return cell

def apply_attribute_to(element, key, val):
    if hasattr(element, impl.util.snake_to_camel('set_'+key)):
        if impl.cell.is_cell(val):
            ## set_central_widget alike methods
            ##
            ## auto re-parent
            getattr(element, impl.util.snake_to_camel('set_'+key))(build(None, val))
        else:
            getattr(element, impl.util.snake_to_camel('set_'+key))(val)
            pass
    elif key.startswith('on_') and hasattr(element, impl.util.snake_to_camel(key[3:])):
        signal = getattr(element, impl.util.snake_to_camel(key[3:]))

        ## the `val' is a slot, just connect them and return
        if callable(val):
            signal.connect(val)
            ### NOTE exit point
            return

        ## normalize the `val' if it is a flatten shortcut, e.g.,
        ## '#label4::set_text'
        if isinstance(val, str):
            val = {'slot': val}
            pass

        ## pass the slot specification
        if isinstance(val, dict):
            if 'selector' not in val:
                parts = val['slot'].split('::')
                selector = parts[0]
                method = parts[1]
            else:
                selector = val['selector']
                method = val['slot']
                pass

            if selector.startswith('#'):
                from impl.query import get_element_by_id
                target_element = get_element_by_id(selector[1:])
                if target_element is not None:
                    signal.connect(getattr(target_element, impl.util.snake_to_camel(method)))
                    pass
                pass
            pass
        else:
            raise RuntimeError('slot value {} to signal {} is malformed'.format(val, key))
    elif key.endswith('_on') and hasattr(element, impl.util.snake_to_camel(key[:-3])):
        slot = getattr(element, impl.util.snake_to_camel(key[:-3]))
        val.connect(slot)
    elif key == 'id':
        from impl.query import _m_constructed_elements
        if val in _m_constructed_elements:
            raise RuntimeError('The element with id {} already exists.'.format(val))
        else:
            _m_constructed_elements[val] = element
            pass
        pass
    else:
        raise RuntimeError('Unexpected attribute {}'.format(key))
    pass

def build_dict(parent, data, cached):
    ## find the element type
    if isinstance(data['tag'][0], str):
        element_type = impl.qt_inspector.find_qt_class(data['tag'][0])
    else:
        element_type = data['tag'][0]
        pass

    ## recursively build the element arguments (without parent)
    element_args = [build(None, arg) if impl.cell.is_cell(arg) else arg for arg in data['tag'][1:]]

    ## append parent argument if necessary
    if impl.qt_inspector.accept_parent(element_type):
        element_args.append(parent)
        pass

    ## build the element
    element = element_type(*element_args)

    ## apply attributes on this element
    for key, val in data.get('attrs',{}).items():
        apply_attribute_to(element, key, val)
        continue

    ## create child elements automatically parenting this element
    if 'children' in data:
        build(element, data['children'], cached)
        pass

    ## additional actions to attach the element (because making an child
    ## element in QT is mainly for memory management, and sometimes for
    ## display, e.g., QMenu(parent=QMenuBar) doesn't show the menu in the menu
    ## bar)
    ##
    ## BEWARE must be after the children creation 'cause it is possible that
    ## the children are actually attached to parent (e.g., QActionGroup)
    impl.qt_inspector.apply_attach_method(parent, element)

    return element

def build_list(parent, data, cached):
    ## find a container for data before we actually insert them
    if not impl.cell.is_cell(data, 'contained'):
        supported_custom_attributes = {'container', 'columns'}

        ## extract the attributes from the list
        if len(data) and isinstance(data[0], dict) and not impl.cell.is_cell(data[0]):
            attrs = data[0]
            meta_attrs = {k:attrs.pop(k) for k in supported_custom_attributes & attrs.keys()}
            data = data[1:]
        else:
            attrs = {}
            meta_attrs = {}
            pass

        ## get a container tag or object
        container = impl.qt_inspector.suggest_container(parent, data, meta_attrs.get('container', True))

        ## mark the data as with a container, and keep the meta_attrs
        cells = impl.cell.make_cell(data, meta_attrs)

        ## build the container and its children
        if isinstance(container, (str,type)):
            ## returned container is a tag for m(), which means an intermediate
            ## element is required as a container
            container = build(parent, m(container, attrs, cells))
        else:
            ## no intermediate container in need
            if attrs or (meta_attrs and meta_attrs.get('container') is not None):
                raise RuntimeError('Unhandled container attributes: {}'.format(attrs.update(meta_attrs) or attrs))
            container = build(parent, cells)
            pass

        return container

    ## now have the container
    for i, cell in enumerate(data):
        ## create the adder object
        adder = cell if isinstance(cell, impl.util._Adder) else impl.util.add(cell)

        ## get the callback to add
        if isinstance(adder.target, str):
            ## the callback is specified by name, e.g., `spacing' -> `addSpacing'
            adder.target = getattr(parent, impl.util.snake_to_camel('add_{}'.format(adder.target)))
        elif impl.cell.can_be_coverted_to_children_cells(adder.target):
            ## if the target is actually the children, deduce a callback by the
            ## types of parent and child
            element = build(impl.qt_inspector.suggest_parent(parent), impl.cell.make_cell(adder.target))
            adder.target = impl.qt_inspector.get_bound_attach_method(parent, element)
        elif adder.target is None:
            ## a placeholder (currently only used in grid layout)
            adder.target = lambda *args: None
            pass
        else:
            raise RuntimeError('Unsupported adder target {}'.format(adder.target))
            pass

        ## build cells inside the adder arguments
        adder.forwarder.args = tuple(
            build(impl.qt_inspector.suggest_parent(parent), impl.cell.make_cell(arg))
            if impl.cell.is_or_has_a_cell(arg) else arg
            for arg in adder.forwarder.args
        )

        ## quirks
        if 'columns' in data.meta_attrs:
             ## a grid layout: insert position arguments
            adder.forwarder.args = divmod(i, data.meta_attrs['columns']) + adder.forwarder.args
            pass

        ## fine
        adder.apply()
        continue

    return None

def build(parent_element, data, cached=None):
    ### FIXME use an OO way to build elements? e.g., list_cell.build(),
    ### dict_cell.build()??

    ## dispatch on data type
    if not data:
        ## could be None when trying to build children
        element = None
    elif impl.cell.is_cell(data):
        ## FIXME hackish cache manipulation
        if hasattr(data, '_cached_pyqt_object') and impl.qt_inspector.allow_duplicates(data._cached_pyqt_object):
            element = data._cached_pyqt_object
        else:
            if isinstance(data, dict):
                element = build_dict(parent_element, data, cached)
            elif isinstance(data, (list, tuple)):
                element = build_list(parent_element, data, cached)
            else:
                raise RuntimeError('Unsupported cell "{}: {}"'.format(type(data), data))
            data._cached_pyqt_object = element
            pass
    else:
        raise RuntimeError('Unsupported cell "{}: {}"'.format(type(data), data))

    return element

def render(root, cell, forceRecreation=False):
    obj_guard = build(root, cell)
    obj_guard.show()
    #configs()
    return obj_guard
    
def mount(parent, Component, mount_method=None):
    app = QApplication(sys.argv)

    if hasattr(Component, 'Controller'):
        ctrl = Component.Controller()
        view = Component.view(ctrl)
    else:
        view = Component.view()
        pass

    if view is None:
        raise RuntimeError('{}.view() does not return a widget factory'.format(component))
    else:
        widget = view()
        widget.show()
        pass

    sys.exit(app.exec_())
