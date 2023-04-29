import json
from dataclasses import dataclass

import rumex

example_file = rumex.InputFile(
    text='''
        Name: Steps with data

        Scenario: A table and a text block

            Given data:
                | Units | Price |
                |    10 |   1.5 |
                |     4 |     4 |

            And modifiers:
                """
                    {
                        "discount_pc": 20,
                        "comment": "json example"
                    }
                """

            Then the total price is 24.8
    ''',
    uri='A unique identifier',
)

steps = rumex.StepMapper()


@dataclass
class Context:

    total_price_before_discount: float | None = None
    discount: float | None = None


@steps(r'Given data')
def store_price(*, context: Context, data):
    context.total_price_before_discount = sum(
        int(row['Units']) * float(row['Price']) for row in data
    )


@steps(r'modifiers')
def store_discount(*, context: Context, data):
    context.discount = json.loads(data)['discount_pc'] / 100


@steps(r'total price is (\d+\.\d+)')
def claculate_result(expected_result: float, *, context: Context):
    assert context.total_price_before_discount is not None
    assert context.discount is not None
    assert expected_result == context.total_price_before_discount * (
            1 - context.discount)


rumex.run(
    files=[example_file],
    steps=steps,
    context_maker=Context,
)
