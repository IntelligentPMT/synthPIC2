"""Tests for the boolean_expression_parsing module."""

import unittest

from pyparsing import ParseException

from synthpic2.recipe.process_conditions.boolean_expression_parsing import \
    parse_boolean_string


class TestBooleanExpressionParsing(unittest.TestCase):
    """Tests for the boolean_expression_parsing module."""

    def test_parse_boolean_string(self) -> None:
        """Test parsing."""

        valid_test_strings = [
            ("True or False", True),
            ("True and False", False),
            ("True and not False", True),
            ("True and False and (False or True)", False),
            ("True and not (False and True)", True),
        ]

        for valid_test_string, expected in valid_test_strings:
            result = parse_boolean_string(valid_test_string)
            self.assertEqual(result, expected)

        # cspell: disable-next-line
        invalid_test_strings = ["True | False", "", "a", "Trueb", "True |"]

        for invalid_test_string in invalid_test_strings:
            with self.assertRaises(ParseException):
                parse_boolean_string(invalid_test_string)
