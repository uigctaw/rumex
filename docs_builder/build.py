import importlib
import inspect
import pathlib
import re
import textwrap
import typing
import sys

THIS_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_DIR = THIS_DIR.parent

sys.path.append(str(PROJECT_DIR))

from docs_builder.doc import NumpyesqueDocstring as Docstring  # noqa: E402


def _read_template():
    with THIS_DIR.joinpath('README.rst.template').open(encoding='utf8') as fio:
        return fio.read()


def _replace_placeholders(template):
    text = template
    pattern = re.compile(r'%%>(.*?)<%%')
    while match_ := re.search(pattern, text):
        items_str, = match_.groups()
        items = re.findall(r'([\w\.]+)', items_str)
        api = _get_api_for_items('rumex.' + item for item in items)
        pattern_start, pattern_end = match_.span()
        text = text[:pattern_start] + api + text[pattern_end:]
    return text


def _get_api_for_items(items):
    return '\n\n'.join(_iter_api_for_items(items))


def _iter_api_for_items(items):
    for item in items:
        api = _get_api(item)
        yield api


def _get_api(name):
    module_name, obj_name = name.rsplit('.', maxsplit=1)
    module = importlib.import_module(module_name)
    obj = getattr(module, obj_name)
    if getattr(obj, '_is_protocol', False):
        signature = _get_protocol_signature(obj, name=name)
    elif hasattr(obj, '__dataclass_fields__'):
        signature = _get_dataclass_signature(obj, name=name)
    elif inspect.isclass(obj):
        signature = _get_class_signature(obj, name=name)
    else:
        signature = _get_function_signature(obj, name=name)
    return signature


def _get_protocol_signature(proto, *, name):
    attrs = typing._get_protocol_attrs(proto)
    return _get_protocol_signature_for_attrs(
            name=name,
            cls=proto,
            attrs=attrs,
    )


def _get_protocol_signature_for_attrs(*, cls, attrs, name):
    return '\n'.join(
            _iter_protocol_signature(cls=cls, attrs=attrs, name=name))


def _iter_protocol_signature(*, cls, attrs, name):
    bases = '\n'.join(base.__qualname__ for base in cls.__bases__)
    full_name = f'{name}({bases})'
    yield full_name
    yield '~' * len(full_name) + '\n'
    yield 'Protocol methods'
    yield '................\n'
    for i, attr_name in enumerate(attrs):
        if i:
            yield '----\n'
        yield _get_fn_or_dc_signature(getattr(cls, attr_name), name=attr_name)


def _get_function_signature(obj, *, name):
    return '\n'.join([
        name,
        '~' * len(name) + '\n',
        _get_fn_or_dc_signature(obj, name=name),
    ])


def _get_class_signature(cls, *, name):
    return '\n'.join(_iter_class_signature(cls=cls, name=name))


def _iter_class_signature(*, cls, name):
    if cls.__bases__ == (object,):
        full_name = name
    else:
        bases = '\n'.join(base.__qualname__ for base in cls.__bases__)
        full_name = f'{name}({bases})'
    yield full_name
    yield '~' * len(full_name) + '\n'
    docs = cls.__doc__
    if not docs:
        raise ValueError(f'{cls} is missing class docstring.')
    yield cls.__doc__ + '\n'
    yield 'Methods'
    yield '.......\n'
    first_method = True
    for attr_name, attr in vars(cls).items():
        if attr_name in ('__module__', '__doc__', '__dict__', '__weakref__'):
            continue
        if attr_name.startswith('_'):
            if attr.__doc__:
                if not first_method:
                    yield '----\n'
                yield _get_fn_or_dc_signature(attr, name=attr_name) + '\n'
                first_method = False
        else:
            if not first_method:
                yield '----\n'
            yield _get_fn_or_dc_signature(attr, name=attr_name) + '\n'
            first_method = False


def _get_dataclass_signature(dc, *, name):
    if dc.__dataclass_params__.frozen:
        sub = 'Frozen dataclass\n'
    else:
        sub = 'Dataclass\n'
    return '\n'.join([
        name,
        '~' * len(name) + '\n',
        sub,
        _get_fn_or_dc_signature(dc, name=name),
    ])


def _get_fn_or_dc_signature(obj, *, name):
    sig = inspect.signature(obj)
    p = inspect.Parameter
    accumulator = {
            p.POSITIONAL_ONLY: [],
            'slash': None,
            p.POSITIONAL_OR_KEYWORD: [],
            'asterisk': None,
            p.KEYWORD_ONLY: [],
    }

    for param in sig.parameters.values():
        if param.kind not in accumulator:
            1/0
        accumulator[param.kind].append(_format_param(param))
        if param.kind == p.POSITIONAL_ONLY:
            accumulator['slash'] = ['/']
        elif param.kind == p.KEYWORD_ONLY:
            accumulator['asterisk'] = ['*']

    args = '    ' + ',\n    '.join(sum(filter(None, accumulator.values()), []))
    return (
            _as_code(f'{name}(\n{args}\n)')
            + '\n\n'
            + _general_description(obj)
            + '\n\n'
            + _params_description(obj, signature=sig)
    )


def _general_description(obj):
    docstring = obj.__doc__
    if docstring is None:
        raise ValueError(f'{obj} in {obj.__module__} is missing a docstring.')
    docs = Docstring(obj.__doc__)
    return '\n'.join(_iter_general_description(docs.description))


def _iter_general_description(description):
    lines = description.splitlines()
    in_code = False
    code_section = []
    for line in lines:
        if line.strip() == '```':
            in_code = not in_code
            if in_code:
                yield '\n.. code:: python\n'
            else:
                should_add_indent = any(
                        not line.startswith('    ') for line in code_section)
                indent = '    ' if should_add_indent else ''
                for line in code_section:
                    indent_for_line = indent if line.strip() else ''
                    yield indent_for_line + line
                yield ''
                code_section.clear()
            continue
        if in_code:
            code_section.append(line)
        else:
            yield line


def _params_description(obj, *, signature):
    docs = Docstring(obj.__doc__)
    documented_params = [param.name for param in docs.parameters]
    actual_params = list(signature.parameters)
    if actual_params and actual_params[0] in ('self', 'cls'):
        actual_params.pop(0)
    if documented_params != actual_params and documented_params:
        raise ValueError(
            f'Could not generate documentation for parameters for {obj}.'
            + f' Was expecting documentation for parameters {actual_params},'
            + f' but found: {documented_params}.'
        )
    return '\n'.join(_iter_params_description(docs))


def _iter_params_description(docs):
    if docs.parameters:
        yield '\n.. rubric:: Parameters\n'
    for param in docs.parameters:
        if param.name.endswith('_'):
            name = param.name[:-1] + '\\' + '_'
        else:
            name = param.name
        desc = map(str.strip, param.description.splitlines())
        yield f'- {name}: {" ".join(desc)}'


def _format_annotation(annotation):
    if isinstance(annotation, str):
        return annotation
    return annotation.__qualname__


def _format_param(param):
    empty = param.empty
    name = param.name
    default = param.default
    annotation = param.annotation
    if default is empty:
        if annotation is empty:
            return name
        return f'{name}: {_format_annotation(annotation)}'

    if annotation is empty:
        return f'{name}={_default_to_str(default)}'

    return (
            f'{name}: {_format_annotation(annotation)}'
            + f' = {_default_to_str(default)}'
    )


def _default_to_str(default):
    if default is None:
        return repr(None)

    ret = default.__module__ + '.' + default.__name__
    return ret


def _as_code(text):
    return '\n'.join(_iter_as_code(text))


def _iter_as_code(text):
    yield '.. code::\n'
    lines = textwrap.dedent(text).splitlines()
    for line in lines:
        if line.strip():
            yield '    ' + line
        else:
            yield ''


def save_readme(readme_text):
    with PROJECT_DIR.joinpath('README.rst').open('w', encoding='utf8') as fio:
        fio.write(readme_text)


def get_built_text(name):
    template_text = _read_template()
    readme_text = _replace_placeholders(template_text)
    return readme_text


def main():
    readme_text = get_built_text('TODO')
    save_readme(readme_text)


if __name__ == '__main__':
    main()
