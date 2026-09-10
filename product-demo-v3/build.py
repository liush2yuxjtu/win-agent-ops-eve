import os
from pathlib import Path

root=Path(__file__).resolve().parent
previous=(root.parent/'product-demo-v2/index.html').read_text()
fixtures=previous[previous.index('const problems='):previous.index('const resultNames=')]
page=(root/'template.html').read_text().replace('__FIXTURES__',fixtures).replace('__SESSION__',os.environ.get('PI_SESSION_ID','unavailable via shell'))
(root/'index.html').write_text(page)
print(root/'index.html')
