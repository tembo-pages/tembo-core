# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['tembo', 'tembo.cli', 'tembo.journal', 'tembo.utils']

package_data = \
{'': ['*']}

install_requires = \
['Jinja2>=3.0.2,<4.0.0',
 'click>=8.0.3,<9.0.0',
 'panaetius>=2.3.2,<3.0.0',
 'pendulum>=2.1.2,<3.0.0']

entry_points = \
{'console_scripts': ['tembo = tembo.cli.cli:main']}

setup_kwargs = {
    'name': 'tembo',
    'version': '0.0.8',
    'description': 'A simple folder organiser for your work notes.',
    'long_description': '# Tembo\n\n<img\n    src="https://raw.githubusercontent.com/tembo-pages/tembo-core/main/assets/tembo_logo.png"\n    width="200px"\n/>\n\nA simple folder organiser for your work notes.\n\n![](https://img.shields.io/codecov/c/github/tembo-pages/tembo-core?style=flat-square)\n\n![Sonar Coverage](https://img.shields.io/sonar/coverage/tembo-pages_tembo-core?server=https%3A%2F%2Fsonarcloud.io&style=flat-square)\n![Sonar Tests](https://img.shields.io/sonar/tests/tembo-pages_tembo-core?compact_message&failed_label=failed&passed_label=passed&server=https%3A%2F%2Fsonarcloud.io&skipped_label=skipped&style=flat-square)\n![Sonar Tech Debt](https://img.shields.io/sonar/tech_debt/tembo-pages_tembo-core?server=https%3A%2F%2Fsonarcloud.io&style=flat-square)\n\n## config.yml\n\n```yaml\n# time tokens: https://strftime.org\ntembo:\n  base_path: ~/tembo\n  # template_path: ~/tembo/templates\n  scopes:\n    - name: scratchpad\n      example: tembo new scratchpad\n      path: "scratchpad/{d:%B_%Y}"\n      filename: "{d:%B_%W}"\n      extension: md\n      template_filename: scratchpad.md.tpl\n    - name: wtodo\n      example: tembo new wtodo | directory is month_year, filename is month_week-of-year\n      path: "wtodo/{d:%B_%Y}"\n      filename: "week_{d:%W}"\n      extension: todo\n      template_filename: weekly.todo.tpl\n    - name: meeting\n      example: tembo new meeting $meeting_title\n      path: "meetings/{d:%B_%y}"\n      filename: "{d:%a_%d_%m_%y}-{input0}"\n      extension: md\n      template_filename: meeting.md.tpl\n    - name: knowledge\n      example: tembo new knowledge $project $filename\n      path: "knowledge/{input0}"\n      filename: "{input1}"\n      extension: md\n      template_filename: knowledge.md.tpl\n  logging:\n    level: INFO\n    path: ~/tembo/.logs\n```\n\n## templates\n\n###\xa0knowledge\n\n```\n---\ncreated: {d:%d-%m-%Y}\n---\n\n# {input0} - {input1}.md\n```\n\n### meeting\n\n```\n---\ncreated: {d:%d-%m-%Y}\n---\n\n# {d:%A %d %B %Y} - {input0}\n\n## People\n\nHead:\n\nAttendees:\n\n## Actions\n\n\n## Notes\n\n```\n\n### scratchpad\n\n```\n---\ncreated: {d:%d-%m-%Y}\n---\n\n# Scratchpad - Week {d:%W} - {d:%B-%y}\n```\n\n### wtodo\n\n```\n---\ncreated: {d:%d-%m-%Y}\n---\n\nWeekly TODO | Week {d:%W} {d:%B}-{d:%Y}\n\nWork:\n\nDocumentation:\n```\n',
    'author': 'dtomlinson',
    'author_email': 'dtomlinson@panaetius.co.uk',
    'maintainer': None,
    'maintainer_email': None,
    'url': 'https://tembo-pages.github.io/tembo-core/',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.8,<4.0',
}


setup(**setup_kwargs)
