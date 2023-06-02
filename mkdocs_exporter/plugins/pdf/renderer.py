from __future__ import annotations

import os
import importlib_resources

from urllib.parse import unquote
from mkdocs_exporter.page import Page
from mkdocs_exporter.resources import js
from mkdocs_exporter.browser import Browser
from mkdocs_exporter.preprocessor import Preprocessor
from mkdocs_exporter.renderer import Renderer as BaseRenderer


class Renderer(BaseRenderer):
  """The renderer."""

  def __init__(self, browser: Browser = None):
    """The constructor."""

    self.scripts: list[str] = []
    self.stylesheets: list[str] = []
    self.browser = browser or Browser()


  def add_stylesheet(self, path: str) -> Renderer:
    """Adds a stylesheet to the renderer."""

    self.stylesheets.append(path)

    return self


  def add_script(self, path: str) -> Renderer:
    """Adds a script to the renderer."""

    self.scripts.append(path)

    return self


  def cover(self, template: str) -> Renderer:
    """Renders a cover."""

    content = template.strip('\n')

    return f'<div data-decompose="true">{content}</div>' + '\n'


  async def render(self, page: Page) -> bytes:
    """Renders a page as a PDF document."""

    if not self.browser.launched:
      await self.browser.launch()

    preprocessor = Preprocessor(theme=page.theme)
    base = os.path.dirname(page.file.abs_dest_path)
    root = base.replace(unquote(page.url).rstrip('/'), '', 1).rstrip('/')

    preprocessor.preprocess(page.html)
    preprocessor.set_attribute('details:not([open])', 'open', 'open')
    page.theme.preprocess(preprocessor)

    for stylesheet in self.stylesheets:
      with open(stylesheet, 'r', encoding='utf-8') as file:
        preprocessor.stylesheet(file.read())
    for script in self.scripts:
      with open(script, 'r', encoding='utf-8') as file:
        preprocessor.script(file.read())

    preprocessor.script(importlib_resources.files(js).joinpath('pagedjs.min.js').read_text())
    preprocessor.teleport()
    preprocessor.update_links(base, root)

    html = preprocessor.done()

    return await self.browser.print(html)


  async def dispose(self) -> None:
    """Dispose of the renderer."""

    if self.browser:
      await self.browser.close()
