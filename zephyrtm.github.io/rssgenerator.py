import os
import yaml
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from datetime import datetime

# ---------------- CONFIG ----------------
CONTENT_DIRS = ['content/posts/mylinuxjourney', 'content/about']  # Add all directories you want
OUTPUT_FILE = '.\index.xml'  # Where to save the RSS feed
SITE_URL = 'https://zephyruszt.github.io/'  # Your site URL
SITE_TITLE = 'zephyruszt'

# ---------------- HELPERS ----------------
def prettify(elem):
    """Return pretty-printed XML string."""
    rough_string = tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def parse_front_matter(filepath):
    """Parse TOML (+++) or YAML (---) front matter from a markdown file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if not lines:
        return {}
    if lines[0].strip() in ('+++', '---'):
        delimiter = lines[0].strip()
        try:
            end_index = lines[1:].index(delimiter + '\n') + 1
        except ValueError:
            return {}
        fm_content = ''.join(lines[1:end_index])
        try:
            if delimiter == '+++':
                import toml
                return toml.loads(fm_content)
            else:
                return yaml.safe_load(fm_content)
        except Exception as e:
            print(f"Failed to parse front matter for {filepath}: {e}")
    return {}

def collect_rss_pages():
    """Walk all content directories and collect pages with RSS output."""
    pages = []
    for dir_path in CONTENT_DIRS:
        if not os.path.exists(dir_path):
            continue
        for root, dirs, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.md'):
                    path = os.path.join(root, file)
                    fm = parse_front_matter(path)
                    if fm.get('outputs') and 'RSS' in fm['outputs']:
                        pages.append((path, fm))
    return pages

# ---------------- BUILD RSS ----------------
rss = Element('rss', version='2.0')
channel = SubElement(rss, 'channel')
SubElement(channel, 'title').text = SITE_TITLE
SubElement(channel, 'link').text = SITE_URL
SubElement(channel, 'description').text = f'RSS feed for {SITE_TITLE}'
SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

pages = collect_rss_pages()
for path, fm in pages:
    item = SubElement(channel, 'item')
    title = fm.get('title', 'Untitled')
    SubElement(item, 'title').text = title
    # Build link based on site URL + relative path from content root
    rel_url = os.path.relpath(path, 'content').replace('.md','/').replace('\\','/')
    SubElement(item, 'link').text = SITE_URL.rstrip('/') + '/' + rel_url
    SubElement(item, 'guid').text = SITE_URL.rstrip('/') + '/' + rel_url
    SubElement(item, 'description').text = fm.get('description','')
    date_str = fm.get('date')
    if date_str:
        try:
            dt = datetime.fromisoformat(date_str)
            SubElement(item, 'pubDate').text = dt.strftime('%a, %d %b %Y %H:%M:%S +0000')
        except:
            pass

# ---------------- WRITE RSS ----------------
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(prettify(rss))

print(f"RSS feed generated: {OUTPUT_FILE}")