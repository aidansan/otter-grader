"""
Abstract base classes for working with test files and classes to represent collections of test and 
their results
"""

from abc import ABC, abstractmethod
from collections import namedtuple
from textwrap import dedent
from typing import Tuple, List, Dict, Any
from jinja2 import Template
from pygments import highlight
from pygments.lexers import PythonConsoleLexer
from pygments.formatters import HtmlFormatter


# class for storing the test cases themselves
#   - body is the string that gets run for the test
#   - hidden is the visibility of the test case
#   - points is the number of points this test case is worth
TestCase = namedtuple("TestCase", ["name", "body", "hidden", "points"])


# class for storing the results of a single test _case_ (within a test file)
#   - message should be a string to print out to the student (ignored if passed is True)
#   - passed is whether the test case passed
#   - hidden is the visibility of the test case
TestCaseResult = namedtuple("TestCaseResult", ["test_case", "message", "passed"])


# TODO: fix reprs
class TestFile(ABC):
    """
    A (abstract) single test file for Otter. This ABC defines how test results are represented and sets
    up the instance variables tracked by tests. Subclasses should implement the abstract class method
    ``from_file`` and the abstract instance method ``run``.

    Args:
        name (``str``): the name of test file
        path (``str``): the path to the test file
        test_cases (``list`` of ``TestCase``): a list of parsed tests to be run
        all_or_nothing (``bool``, optional): whether the test should be graded all-or-nothing across
            cases

    Attributes:
        name (``str``): the name of test file
        path (``str``): the path to the test file
        test_cases (``list`` of ``TestCase``): a list of parsed tests to be run
        all_or_nothing (``bool``): whether the test should be graded all-or-nothing across
            cases
        test_case_results (``list`` of ``TestCaseResult``): a list of results for the test cases in
            ``test_cases``
    """

    html_result_pass_template = Template("""
    <p><strong>{{ name }}</strong> passed!</p>
    """)

    plain_result_pass_template = Template("{{ name }} passed!")

    html_result_fail_template = Template("""
    <p><strong style='color: red;'>{{ name }}</strong></p>
    <p><strong>Test result:</strong></p>
    {% for test_case_result in test_case_results %}
        <p><em>{{ test_case_result.test_case.name }}</em>
        {% if not test_case_result.passed %}
            <pre>{{ test_case_result.message }}</pre>
        {% else %}
            <pre>Test case passed!</pre>
        {% endif %}
        </p>
    {% endfor %}
    """)

    plain_result_fail_template = Template(dedent("""\
    {{ name }} results:
    {% for test_case_result in test_case_results %}{% if not test_case_result.passed %}
    {{ test_case_result.message }}{% endif %}{% endfor %}"""))

    def _repr_html_(self):
        if self.passed_all:
            return type(self).html_result_pass_template.render(name=self.name)
        else:
            return type(self).html_result_fail_template.render(
                name=self.name,
                # test_code=highlight(self.failed_test, PythonConsoleLexer(), HtmlFormatter(noclasses=True)),
                test_case_results=self.test_case_results
            )

    def __repr__(self):
        if self.passed_all:
            return type(self).plain_result_pass_template.render(name=self.name)
        else:
            return type(self).plain_result_fail_template.render(
                name=self.name,
                # test_code=self.failed_test,
                test_case_results=self.test_case_results
            )

    # @abstractmethod
    def __init__(self, name, path, test_cases, all_or_nothing=True):
        self.name = name
        self.path = path
        self.test_cases = test_cases
        self.all_or_nothing = all_or_nothing
        self.test_case_results = []

    @staticmethod
    def resolve_test_file_points(total_points, test_cases):
        point_values = []
        for i, test_case in enumerate(test_cases):
            if test_case.points is not None:
                assert type(test_case.points) in (int, float), f"Invalid point type: {type(test_case.points)}"
                point_values.append(test_case.points)
            else:
                point_values.append(None)

        pre_specified = sum(p for p in point_values if p is not None)
        if total_points is not None:
            if pre_specified > total_points:
                raise ValueError(f"More points specified in test cases that allowed for test")
            else:
                per_remaining = (total_points - pre_specified) / sum(1 for p in point_values if p is None)
        else:
            # assume all other tests are worth 0 points
            if pre_specified == 0 and total_points != 0:
                per_remaining = 1 / len(point_values)
            else:
                per_remaining = 0.0

        point_values = [p if p is not None else per_remaining for p in point_values]
        return [tc._replace(points=p) for tc, p in zip(test_cases, point_values)]

    @property
    def passed_all(self):
        return all(tcr.passed for tcr in self.test_case_results)

    @property
    def grade(self):
        if self.all_or_nothing and not self.passed_all:
            return 0
        elif self.all_or_nothing and self.passed_all:
            return 1
        else:
            return sum(tcr.test_case.points for tcr in self.test_case_results if tcr.passed) / \
                sum(tc.points for tc in self.test_cases)

    @classmethod
    @abstractmethod
    def from_file(cls, path):
        ...

    @abstractmethod
    def run(self, global_environment):
        ...
