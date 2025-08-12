from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker import BaseChunk
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.types.doc import ImageRefMode

from dotenv import dotenv_values


def create_converter():
    pipeline_options = PdfPipelineOptions(
        generate_picture_images=True,  # Generate base64-encoded images
        # do_picture_classification=True,  # Classify images (optional, but aligns with CLI)
        images_scale=3.0,
    )

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )
    return converter


def create_chunker():
    chunker = HybridChunker()
    return chunker


class Node(object):

    def __init__(self, title, children=None):
        self.title = title
        self.children = children or []

    def __str__(self):
        return self.title

    # depth first search
    def __iter__(self):
        yield self
        for child in self.children:
            for node in child:
                yield node


def construct_chunk_tree(chunks: list[BaseChunk], tree_title: str = 'root'):
    tree = Node(tree_title)
    node_dict = {tree_title: tree}

    for idx, chunk in enumerate(chunks):
        chunk_json_dict = chunk.export_json_dict()
        headings = [tree_title]
        headings.extend(chunk_json_dict['meta']['headings'])

        for heading in headings:
            if heading not in node_dict:
                node_dict[heading] = Node(heading)

        while len(headings) >= 2:
            node = node_dict[headings[0]]
            child_node = node_dict[headings[1]]
            if child_node not in node.children:
                node.children.append(child_node)
            headings.pop(0)

    return tree


def save_as_html(result: ConversionResult, filename: str, image_mode: ImageRefMode, save_dir: str = 'saves'):
    save_dir = Path(save_dir)
    save_dir.mkdir(exist_ok=True)
    filename = Path(save_dir, filename).with_suffix(".html")

    artifacts_dir = filename.with_suffix("")
    artifacts_dir = artifacts_dir.with_name(artifacts_dir.name + "_artifacts")

    result.document.save_as_html(filename=filename, artifacts_dir=artifacts_dir, image_mode=image_mode)

    return filename, artifacts_dir


def extract_exported_content(soup: BeautifulSoup):
    children_of_body = soup.body.find_all(name=True, recursive=False)

    if len(children_of_body) != 1:
        raise Exception(f'eyyo {len(children_of_body)} children in body. Expected only body_content')

    body_content = children_of_body[0]
    body_content = body_content.find_all(name=True, recursive=False)
    return body_content


async def upload_image(artifact: Path, imgbb_api_key: str):
    """
    upload one
    """
    url = "https://api.imgbb.com/1/upload"
    params = {
        # "expiration": 600,  # what is this
        "key": imgbb_api_key,
    }
    try:
        with open(artifact, 'rb') as f:
            files = {
                'image': f
            }
            response = requests.post(url, params=params, files=files)

        if response.status_code == 200:
            print("Upload successful!")
            print(response.json())
            return response.json()['data']['url']
        else:
            raise Exception(f"Upload failed with status code: {response.status_code}")
    except Exception as e:
        print(e, response.text)


async def upload_images(body_content: list[Tag], artifacts_dir: Path, config: dict):
    figures = []
    for child in body_content:
        if child.name == 'figure':
            child_of_child = child.find_all(name=True, recursive=False)
            if len(child_of_child) == 1 and child_of_child[0].name == 'img':
                figures.append(child)

    artifacts = list(artifacts_dir.glob('*.png'))

    for figure, artifact in zip(figures, artifacts):
        img = figure.find_all(name=True, recursive=False)[0]
        img_path = Path(artifact.parent.parent, unquote(img['src']))

        # validate 2 ways of manually get image reference
        if img_path != artifact:
            raise Exception(f'paths unmatched. \n{img_path}\n{artifact}')

    for figure, artifact in zip(figures, artifacts):
        img_url = await upload_image(artifact, imgbb_api_key=config['IMGBB_API_KEY'])

        img = figure.find_all(name=True, recursive=False)[0]
        img['src'] = img_url


def generate_output(body_content: list[Tag], chunk_tree: Node):
    indexes_chunk_begin = []
    chunks_headings = [str(chunk) for chunk in chunk_tree]
    chunks_headings.pop(0)
    for idx, child in enumerate(body_content):
        if 'h' not in child.name:
            continue
        if child.string in chunks_headings:
            indexes_chunk_begin.append(idx)
            chunks_headings.pop(0)
    indexes_chunk_begin.append(len(body_content))
    print(chunks_headings)
    print(indexes_chunk_begin)
    html_chunks = []
    for idx in range(len(indexes_chunk_begin) - 1):
        print(body_content[indexes_chunk_begin[idx]:indexes_chunk_begin[idx + 1]])
        html_chunks.append(
            ''.join([str(child) for child in body_content[indexes_chunk_begin[idx]:indexes_chunk_begin[idx + 1]]]))

    return html_chunks # output tree also


async def process(source: str):
    converter = create_converter()
    result = converter.convert(source)
    chunker = create_chunker()

    chunk_iter = chunker.chunk(result.document)
    chunks = list(chunk_iter)

    chunk_tree = construct_chunk_tree(chunks)

    filename: str = 'my_raw' #todo
    save_results: tuple[Path, Path,] = save_as_html(result=result, filename=filename,
                                                    image_mode=ImageRefMode.REFERENCED)
    filename, artifacts_dir = save_results

    with open(filename, encoding='utf-8') as f:
        soup = BeautifulSoup(''.join([line.strip() for line in f.readlines()]), 'html.parser')

    body_content = extract_exported_content(soup)

    config = dotenv_values()

    await upload_images(body_content=body_content, artifacts_dir=artifacts_dir, config=config)

    html_chunks = generate_output(body_content=body_content, chunk_tree=chunk_tree)
    return html_chunks
