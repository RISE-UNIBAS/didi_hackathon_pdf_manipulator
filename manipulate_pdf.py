"""Simple script to manipulate images in a PDF file."""
import argparse
import base64
import io
import os
import fitz
import requests
from PIL import Image, ImageFilter, ImageFont, ImageDraw


def get_image_description(image_path, prompt, model, openai_key, max_tokens, is_verbose=False):
    """Gets an image description using OpenAI's API.

    Args:
        image_path (str): The path to the image.
        prompt (str): The prompt to use.
        model (str): The model to use.
        openai_key (str): The OpenAI key. You can get one at https://platform.openai.com/api-keys
        max_tokens (int): The maximum number of tokens to be used (per request, e.g. per image!)
        is_verbose (bool): Whether to print debug information.

    Returns:
        str: The description of the image."""

    # Check if the image path is valid
    if not os.path.exists(image_path):
        print(f"Error: The image path '{image_path}' does not exist.")
        return

    try:
        # Encode the image to base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        # Make the request to OpenAI's API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {openai_key}"
        }

        payload = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }],
            "max_tokens": max_tokens
        }

        response = requests.post(url="https://api.openai.com/v1/chat/completions",
                                 headers=headers,
                                 json=payload)

        # Get the description from the response
        response = response.json()
        if is_verbose:
            print(f"get_image_description::Response: {response}")
        description = response['choices'][0]['message']['content']
        return description
    except Exception as e:
        print("get_image_description::Error:", e)
        return ""
    except KeyError:
        print(f"get_image_description::Key Error in response")
        return ""


def text_wrap(text, font, max_width):
    """Wrap text to fit a given width to print on an image.

    Args:
        text (str): The text to wrap.
        font (PIL.ImageFont): The font to use.
        max_width (int): The maximum width."""

    if text is None or font is None or max_width is None:
        print(f"text_wrap::Error: text, font, or max_width is None ({text}, {font}, {max_width})")
        return []

    lines = []
    words = text.split(' ')
    i = 0
    line = ''
    while i < len(words):
        test_line = line + words[i] + ' '
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]

        if text_width > max_width:
            lines.append(line.strip())
            line = words[i] + ' '
        else:
            line = test_line
        i += 1
    lines.append(line.strip())
    return lines


def extract_pdf(args):
    """Extracts images from a PDF file and applies some transformations to them.

    Args:
        args (argparse.Namespace): The arguments from the command line."""

    # Create a temporary image path
    orig_tmp_path = f"o_tmp.jpg"
    tmp_image_path = f"tmp.jpg"

    # Check if the OpenAI key is provided (only if the describe flag is set)
    if args.describe:
        if not args.openai_key:
            print("Please provide an OpenAI key with the --openai-key flag.")
            return

    # Open the PDF file
    pdf = args.pdf_file
    doc = fitz.open(pdf)

    # Iterate over the pages
    for page in doc:
        if args.verbose:
            print(f"Processing page {page.number}")

        # Get the images on the page and iterate over them
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            # Create an image to apply the transformations
            base_image = doc.extract_image(img[0])
            pil_img = Image.open(io.BytesIO(base_image["image"]))

            # If the describe flag is set, get the description of the image
            description = None
            if args.describe:
                if args.verbose:
                    print(f">> Describing image {img_index} on page {page.number}")

                # Save the image to a temporary file
                try:
                    pil_img.save(orig_tmp_path, format='JPEG')
                except Exception as e:
                    print(f"extract_pdf::Error saving image to {orig_tmp_path}: {e}")

                description = get_image_description(orig_tmp_path,
                                                    args.description_prompt,
                                                    "gpt-4-vision-preview",
                                                    args.openai_key,
                                                    args.max_openai_tokens,
                                                    is_verbose=args.verbose)
                if os.path.exists(orig_tmp_path):
                    os.remove(orig_tmp_path)

            if args.blur > 0:
                pil_img = pil_img.filter(ImageFilter.GaussianBlur(args.blur))
                if args.verbose:
                    print(f">> Blurring image {img_index} on page {page.number}")
            if args.emboss:
                pil_img = pil_img.filter(ImageFilter.EMBOSS)
                if args.verbose:
                    print(f">> Embossing image {img_index} on page {page.number}")
            if args.gray:
                pil_img = pil_img.convert('L')
                if args.verbose:
                    print(f">> Gray-scaling image {img_index} on page {page.number}")
            if args.black:
                pil_img = pil_img.convert('1')
                if args.verbose:
                    print(f">> Blackening image {img_index} on page {page.number}")

            if args.describe:
                draw = ImageDraw.Draw(pil_img)
                max_width = pil_img.width
                font = ImageFont.truetype('arial.ttf', args.font_size)
                lines = text_wrap(description, font, max_width)
                y_text = 10
                for line in lines:
                    bbox = font.getbbox(line)
                    text_height = bbox[3] - bbox[1]

                    draw.text((10, y_text), line, font=font, fill='white')
                    # Draw a shadow
                    draw.text((10 + 1, y_text + 1), line, font=font, fill='black')
                    y_text += text_height

            try:
                pil_img.save(tmp_image_path, format='JPEG')
            except Exception as e:
                print(e)

            img_info = page.get_image_info()[img_index]
            bbox = img_info['bbox']
            page.insert_image(bbox, filename=tmp_image_path, keep_proportion=True)

        if os.path.exists(tmp_image_path):
            os.remove(tmp_image_path)

    doc.save(args.output_file)
    doc.close()


def main():
    # Create the parser
    parser = argparse.ArgumentParser(description='Change images in a PDF file.')

    # Add arguments
    parser.add_argument('pdf_file', type=str, help='Input')

    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose mode')
    parser.add_argument('-o', '--output-file', type=str, help='Output file', default='output.pdf')

    parser.add_argument('--blur', type=int, help="[0-50] Apply a blur effect to the images of the PDF.",
                        default=0)
    parser.add_argument('--gray', action='store_true', help="Gray scale the images of the PDF")
    parser.add_argument('--black', action='store_true', help="Blacken the images of the PDF")
    parser.add_argument('--emboss', action='store_true',
                        help="Apply a emboss effect to the images of the PDF")

    parser.add_argument('--describe', action='store_true',
                        help="Apply a description to the content of the PDF")
    parser.add_argument('--openai-key', type=str, help="OpenAI key", default='')
    parser.add_argument('--description-prompt', type=str, help="Prompt for the description",
                        default='Describe the image in less than 20 words. Include the number of people and objects.')
    parser.add_argument('--max-openai-tokens', type=int, help="Max tokens", default=300)
    parser.add_argument('--font-size', type=int, help="Font size", default=18)

    # Parse the arguments
    args = parser.parse_args()

    # Perform the operation
    extract_pdf(args)


if __name__ == "__main__":
    main()

