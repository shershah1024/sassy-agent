#!/usr/bin/env python3
import os
import uuid
from enum import Enum
from typing import Dict, Any, Optional, List
import logging
import requests
from urllib.parse import urlparse
from presentation_themes import THEMES, ThemeColors, SlideType, Position, Size, FontStyle, RgbColor

logger = logging.getLogger(__name__)

# We only use a BLANK layout for every slide.
class SlideLayout(Enum):
    BLANK = "BLANK"

# Define some shape types to use.
class ShapeType(Enum):
    TEXT_BOX = "TEXT_BOX"
    RECTANGLE = "RECTANGLE"
    OVAL = "OVAL"

class MultiStylePresentation:
    def __init__(self, credentials):
        """Initialize with credentials from the frontend token"""
        from googleapiclient.discovery import build
        self.service = build('slides', 'v1', credentials=credentials)
        self.current_theme: Optional[ThemeColors] = None

    def set_theme(self, theme_name: str):
        """Set the current theme for the presentation"""
        if theme_name not in THEMES:
            raise ValueError(f"Unknown theme: {theme_name}")
        self.current_theme = THEMES[theme_name]

    def create_presentation(self, title: str, theme_name: str = "MINIMAL") -> str:
        """Creates a new presentation with the given title and theme."""
        self.set_theme(theme_name)
        body = {'title': title}
        presentation = self.service.presentations().create(body=body).execute()
        return presentation['presentationId']

    def batch_update(self, presentation_id: str, requests_list: list) -> Dict[str, Any]:
        """Sends a batchUpdate request to the presentation."""
        body = {'requests': requests_list}
        response = self.service.presentations().batchUpdate(
            presentationId=presentation_id, body=body).execute()
        return response

    def add_slide(self, presentation_id: str, slide_type: SlideType, content: Dict[str, Any],
                  insertion_index: int = 0) -> Optional[str]:
        """Adds a new slide with the specified layout and content."""
        slide_id = self._generate_random_id()
        
        # Create the slide first
        request = {
            'createSlide': {
                'objectId': slide_id,
                'insertionIndex': str(insertion_index),
                'slideLayoutReference': {'predefinedLayout': "BLANK"}
            }
        }
        
        response = self.batch_update(presentation_id, [request])
        if not response.get('replies'):
            return None

        # Add background with theme color
        if self.current_theme:
            self.add_shape(
                presentation_id,
                slide_id,
                'RECTANGLE',
                Position(left=0, top=0),
                Size(width=720, height=405),
                fill_color=self.current_theme.background
            )

        # Add content based on slide type
        if slide_type in [SlideType.TITLE_CENTERED, SlideType.TITLE_LEFT, SlideType.TITLE_GRADIENT]:
            self._add_title_slide_content(presentation_id, slide_id, slide_type, content)
        elif slide_type in [SlideType.TWO_COLUMNS_EQUAL, SlideType.TWO_COLUMNS_LEFT_WIDE, SlideType.TWO_COLUMNS_RIGHT_WIDE]:
            self._add_two_column_content(presentation_id, slide_id, slide_type, content)
        elif slide_type == SlideType.IMAGE_CENTERED:
            self._add_image_slide_content(presentation_id, slide_id, content)
        elif slide_type in [SlideType.QUOTE_CENTERED, SlideType.QUOTE_SIDE]:
            self._add_quote_slide_content(presentation_id, slide_id, slide_type, content)
        elif slide_type in [SlideType.BULLET_POINTS, SlideType.NUMBER_POINTS]:
            self._add_points_slide_content(presentation_id, slide_id, slide_type, content)

        return slide_id

    def _add_title_slide_content(self, presentation_id: str, slide_id: str, 
                                slide_type: SlideType, content: Dict[str, Any]):
        """Add content for title slides"""
        if not self.current_theme:
            return

        if slide_type == SlideType.TITLE_GRADIENT:
            # Add gradient background
            darker_primary = {
                'red': self.current_theme.primary['red'] * 0.8,
                'green': self.current_theme.primary['green'] * 0.8,
                'blue': self.current_theme.primary['blue'] * 0.8
            }
            self.add_shape(
                presentation_id, slide_id, 'RECTANGLE',
                Position(left=0, top=0),
                Size(width=720, height=405),
                fill_color=darker_primary
            )
            text_color = self.current_theme.textLight
        else:
            text_color = self.current_theme.primary

        # Add title
        title_pos = Position(
            left=50 if slide_type == SlideType.TITLE_LEFT else 50,
            top=80 if slide_type == SlideType.TITLE_LEFT else 120
        )
        title_size = Size(
            width=300 if slide_type == SlideType.TITLE_LEFT else 620,
            height=200 if slide_type == SlideType.TITLE_LEFT else 60
        )
        self.add_text_box(
            presentation_id,
            slide_id,
            content['title'],
            title_pos,
            title_size,
            FontStyle(
                bold=True,
                fontSize={'magnitude': 36 if slide_type == SlideType.TITLE_LEFT else 40, 'unit': 'PT'},
                foregroundColor={'opaqueColor': {'rgbColor': text_color}}
            )
        )

        # Add subtitle if present
        if content.get('subtitle'):
            subtitle_pos = Position(
                left=50 if slide_type == SlideType.TITLE_LEFT else 50,
                top=200 if slide_type == SlideType.TITLE_LEFT else 220
            )
            subtitle_size = Size(
                width=300 if slide_type == SlideType.TITLE_LEFT else 620,
                height=60 if slide_type == SlideType.TITLE_LEFT else 40
            )
            self.add_text_box(
                presentation_id,
                slide_id,
                content['subtitle'],
                subtitle_pos,
                subtitle_size,
                FontStyle(
                    fontSize={'magnitude': 20 if slide_type == SlideType.TITLE_LEFT else 24, 'unit': 'PT'},
                    foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.secondary}}
                )
            )

    def _add_two_column_content(self, presentation_id: str, slide_id: str,
                               slide_type: SlideType, content: Dict[str, Any]):
        """Add content for two-column slides"""
        if not self.current_theme:
            return

        # Calculate column widths based on layout
        if slide_type == SlideType.TWO_COLUMNS_EQUAL:
            left_width, right_width = 300, 300
            right_start = 370
        elif slide_type == SlideType.TWO_COLUMNS_LEFT_WIDE:
            left_width, right_width = 400, 200
            right_start = 470
        else:  # TWO_COLUMNS_RIGHT_WIDE
            left_width, right_width = 200, 400
            right_start = 270

        # Add title
        self.add_text_box(
            presentation_id,
            slide_id,
            content['title'],
            Position(left=50, top=40),
            Size(width=620, height=60),
            FontStyle(
                bold=True,
                fontSize={'magnitude': 28, 'unit': 'PT'},
                foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.primary}}
            )
        )

        # Add column titles if present
        y_position = 120
        if content.get('leftTitle'):
            self.add_text_box(
                presentation_id,
                slide_id,
                content['leftTitle'],
                Position(left=50, top=y_position),
                Size(width=left_width, height=30),
                FontStyle(
                    bold=True,
                    fontSize={'magnitude': 16, 'unit': 'PT'},
                    foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.secondary}}
                )
            )
            y_position = 160

        # Add left column content
        self.add_text_box(
            presentation_id,
            slide_id,
            content['leftContent'],
            Position(left=50, top=y_position),
            Size(width=left_width, height=200),
            FontStyle(
                fontSize={'magnitude': 14, 'unit': 'PT'},
                foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.text}}
            )
        )

        # Reset y_position for right column
        y_position = 120
        if content.get('rightTitle'):
            self.add_text_box(
                presentation_id,
                slide_id,
                content['rightTitle'],
                Position(left=right_start, top=y_position),
                Size(width=right_width, height=30),
                FontStyle(
                    bold=True,
                    fontSize={'magnitude': 16, 'unit': 'PT'},
                    foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.secondary}}
                )
            )
            y_position = 160

        # Add right column content
        self.add_text_box(
            presentation_id,
            slide_id,
            content['rightContent'],
            Position(left=right_start, top=y_position),
            Size(width=right_width, height=200),
            FontStyle(
                fontSize={'magnitude': 14, 'unit': 'PT'},
                foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.text}}
            )
        )

    def _add_image_slide_content(self, presentation_id: str, slide_id: str,
                                content: Dict[str, Any]):
        """Add content for image-centered slides"""
        if not self.current_theme:
            return

        # Add title
        self.add_text_box(
            presentation_id,
            slide_id,
            content['title'],
            Position(left=50, top=30),
            Size(width=620, height=50),
            FontStyle(
                bold=True,
                fontSize={'magnitude': 28, 'unit': 'PT'},
                foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.primary}}
            )
        )

        # Add image if URL is present
        if content.get('imageUrl'):
            logger.info(f"Adding image with URL: {content['imageUrl']}")
            try:
                # Validate image URL
                if self._validate_image_url(content['imageUrl']):
                    self.add_image(
                        presentation_id,
                        slide_id,
                        content['imageUrl'],
                        Position(left=110, top=100),
                        Size(width=500, height=260)
                    )
                    logger.info("Image added successfully")
                else:
                    logger.error(f"Invalid image URL: {content['imageUrl']}")
            except Exception as e:
                logger.error(f"Error adding image: {str(e)}")

        # Add caption if present
        if content.get('caption'):
            self.add_text_box(
                presentation_id,
                slide_id,
                content['caption'],
                Position(left=110, top=370),
                Size(width=500, height=25),
                FontStyle(
                    fontSize={'magnitude': 14, 'unit': 'PT'},
                    foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.text}}
                )
            )

    def _add_quote_slide_content(self, presentation_id: str, slide_id: str,
                                slide_type: SlideType, content: Dict[str, Any]):
        """Add content for quote slides"""
        if not self.current_theme:
            return

        if slide_type == SlideType.QUOTE_CENTERED:
            # Add centered quote
            self.add_text_box(
                presentation_id,
                slide_id,
                f'"{content["quote"]}"',
                Position(left=100, top=100),
                Size(width=520, height=100),
                FontStyle(
                    bold=True,
                    fontSize={'magnitude': 32, 'unit': 'PT'},
                    foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.primary}}
                )
            )

            # Add author
            self.add_text_box(
                presentation_id,
                slide_id,
                f"- {content['author']}",
                Position(left=100, top=220),
                Size(width=520, height=40),
                FontStyle(
                    fontSize={'magnitude': 20, 'unit': 'PT'},
                    foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.secondary}}
                )
            )

            # Add context if present
            if content.get('context'):
                self.add_text_box(
                    presentation_id,
                    slide_id,
                    content['context'],
                    Position(left=100, top=270),
                    Size(width=520, height=60),
                    FontStyle(
                        fontSize={'magnitude': 16, 'unit': 'PT'},
                        foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.text}}
                    )
                )
        else:  # QUOTE_SIDE
            # Add side quote
            self.add_text_box(
                presentation_id,
                slide_id,
                f'"{content["quote"]}"',
                Position(left=50, top=80),
                Size(width=400, height=200),
                FontStyle(
                    bold=True,
                    fontSize={'magnitude': 24, 'unit': 'PT'},
                    foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.primary}}
                )
            )

            # Add author
            self.add_text_box(
                presentation_id,
                slide_id,
                f"- {content['author']}",
                Position(left=470, top=80),
                Size(width=200, height=40),
                FontStyle(
                    fontSize={'magnitude': 18, 'unit': 'PT'},
                    foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.secondary}}
                )
            )

            # Add context if present
            if content.get('context'):
                self.add_text_box(
                    presentation_id,
                    slide_id,
                    content['context'],
                    Position(left=470, top=130),
                    Size(width=200, height=150),
                    FontStyle(
                        fontSize={'magnitude': 16, 'unit': 'PT'},
                        foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.text}}
                    )
                )

    def _add_points_slide_content(self, presentation_id: str, slide_id: str,
                                 slide_type: SlideType, content: Dict[str, Any]):
        """Add content for bullet or number points slides"""
        if not self.current_theme:
            return

        # Add title
        self.add_text_box(
            presentation_id,
            slide_id,
            content['title'],
            Position(left=50, top=40),
            Size(width=620, height=60),
            FontStyle(
                bold=True,
                fontSize={'magnitude': 28, 'unit': 'PT'},
                foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.primary}}
            )
        )

        # Format points
        points_text = ""
        for i, point in enumerate(content['points']):
            prefix = f"{i + 1}. " if slide_type == SlideType.NUMBER_POINTS else "• "
            points_text += f"{prefix}{point}\n"

        # Add points
        self.add_text_box(
            presentation_id,
            slide_id,
            points_text.strip(),
            Position(left=70, top=120),
            Size(width=580, height=250),
            FontStyle(
                fontSize={'magnitude': 18, 'unit': 'PT'},
                foregroundColor={'opaqueColor': {'rgbColor': self.current_theme.text}}
            )
        )

    def add_text_box(self, presentation_id: str, slide_id: str, text: str,
                     position: Position, size: Size, style: FontStyle) -> str:
        """Creates a text box with specified position, size, and style."""
        shape_id = "TextBox_" + self._generate_random_id()
        requests = [{
            'createShape': {
                'objectId': shape_id,
                'shapeType': 'TEXT_BOX',
                'elementProperties': {
                    'pageObjectId': slide_id,
                    'size': {
                        'height': {'magnitude': size.height, 'unit': 'PT'},
                        'width': {'magnitude': size.width, 'unit': 'PT'}
                    },
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': position.left,
                        'translateY': position.top,
                        'unit': 'PT'
                    }
                }
            }
        }, {
            'insertText': {
                'objectId': shape_id,
                'insertionIndex': 0,
                'text': text
            }
        }]

        if style:
            style_request = {
                'updateTextStyle': {
                    'objectId': shape_id,
                    'style': {
                        'bold': style.bold,
                        'fontSize': style.fontSize,
                        'foregroundColor': style.foregroundColor
                    },
                    'textRange': {'type': 'ALL'},
                    'fields': 'bold,fontSize,foregroundColor'
                }
            }
            requests.append(style_request)

        self.batch_update(presentation_id, requests)
        return shape_id

    def add_image(self, presentation_id: str, slide_id: str, image_url: str,
                  position: Position, size: Size) -> str:
        """Inserts an image with specified position and size."""
        image_id = "Image_" + self._generate_random_id()
        logger.info(f"\nAdding image to slide {slide_id}:")
        logger.info(f"Image URL: {image_url}")
        logger.info(f"Position: left={position.left}, top={position.top}")
        logger.info(f"Size: width={size.width}, height={size.height}")
        
        requests = [{
            'createImage': {
                'objectId': image_id,
                'url': image_url,
                'elementProperties': {
                    'pageObjectId': slide_id,
                    'size': {
                        'height': {'magnitude': size.height, 'unit': 'PT'},
                        'width': {'magnitude': size.width, 'unit': 'PT'}
                    },
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': position.left,
                        'translateY': position.top,
                        'unit': 'PT'
                    }
                }
            }
        }]
        
        logger.info(f"Sending request to Google Slides API: {requests}")
        try:
            response = self.batch_update(presentation_id, requests)
            logger.info(f"Google Slides API response: {response}")
            return image_id
        except Exception as e:
            logger.error(f"Error in batch_update while adding image: {str(e)}")
            raise

    def add_shape(self, presentation_id: str, slide_id: str, shape_type: str,
                  position: Position, size: Size, fill_color: Optional[RgbColor] = None) -> str:
        """Creates a shape with specified position, size, and fill color."""
        shape_id = f"{shape_type}_" + self._generate_random_id()
        requests = [{
            'createShape': {
                'objectId': shape_id,
                'shapeType': shape_type,
                'elementProperties': {
                    'pageObjectId': slide_id,
                    'size': {
                        'height': {'magnitude': size.height, 'unit': 'PT'},
                        'width': {'magnitude': size.width, 'unit': 'PT'}
                    },
                    'transform': {
                        'scaleX': 1,
                        'scaleY': 1,
                        'translateX': position.left,
                        'translateY': position.top,
                        'unit': 'PT'
                    }
                }
            }
        }]

        if fill_color:
            fill_request = {
                'updateShapeProperties': {
                    'objectId': shape_id,
                    'shapeProperties': {
                        'shapeBackgroundFill': {
                            'solidFill': {
                                'color': {'rgbColor': fill_color}
                            }
                        }
                    },
                    'fields': 'shapeBackgroundFill'
                }
            }
            requests.append(fill_request)

        self.batch_update(presentation_id, requests)
        return shape_id

    def _validate_image_url(self, image_url: str) -> bool:
        """Validates if the image URL is accessible and in a supported format."""
        try:
            parsed = urlparse(image_url)
            if not all([parsed.scheme, parsed.netloc]):
                logger.error(f"Invalid URL format: {image_url}")
                return False

            # For Supabase URLs, we assume they are valid since they are from our storage
            if 'supabase' in image_url:
                logger.info(f"Supabase URL detected, assuming valid: {image_url}")
                return True

            # For other URLs, verify they are accessible
            response = requests.head(image_url, allow_redirects=True, timeout=5)
            if response.status_code != 200:
                logger.error(f"URL not accessible (status {response.status_code}): {image_url}")
                return False

            content_type = response.headers.get('content-type', '')
            supported_types = ['image/jpeg', 'image/png', 'image/gif']
            is_supported = any(t in content_type.lower() for t in supported_types)
            if not is_supported:
                logger.error(f"Unsupported content type {content_type}: {image_url}")
            return is_supported
        except Exception as e:
            logger.error(f"Error validating image URL {image_url}: {str(e)}")
            return False

    def _generate_random_id(self) -> str:
        """Generates a random ID for elements."""
        return uuid.uuid4().hex[:10]

    def create_multi_style_presentation(self, title: str, num_slides: int = 10,
                                      custom_shapes: Optional[List[ShapeType]] = None,
                                      custom_colors: bool = False) -> Dict[str, str]:
        """Creates a multi-style presentation with the specified number of slides."""
        try:
            # Create the presentation
            pres_id = self.create_presentation(title)
            logger.info(f"Created presentation with ID: {pres_id}")

            # Default shapes if none provided
            shapes_to_use = custom_shapes if custom_shapes else [ShapeType.RECTANGLE, ShapeType.OVAL]

            # Validate image URL before proceeding
            image_url = "https://mbjkvwatoiryvmskgewn.supabase.co/storage/v1/object/public/igcse_spanish_images//generated_image_1740134345_3db63289.png"
            is_valid_image = self._validate_image_url(image_url)
            logger.info(f"Image URL validation result: {is_valid_image}")

            # Create slides
            for i in range(num_slides):
                slide_index = i
                slide_id = self.add_slide(pres_id, SlideType.BLANK, {}, insertion_index=slide_index)
                logger.info(f"Created slide {i+1} with ID: {slide_id}")

                # Heading text box
                heading_text = f"Slide {i+1}"
                heading_id = self.add_text_box(pres_id, slide_id, heading_text, 
                                            position=Position(left=50, top=40),
                                            size=Size(width=600, height=60),
                                            style=FontStyle(
                                                bold=True,
                                                fontSize={'magnitude': 32, 'unit': 'PT'},
                                                foregroundColor={'opaqueColor': {'rgbColor': {'red': 0.0, 'green': 0.0, 'blue': 0.0}}}
                                            ))

                # Description text box
                description_text = f"This is slide {i+1} of our presentation. It demonstrates a blank canvas with added elements."
                desc_id = self.add_text_box(pres_id, slide_id, description_text, 
                                          position=Position(left=50, top=110),
                                          size=Size(width=600, height=50),
                                          style=FontStyle(
                                              fontSize={'magnitude': 18, 'unit': 'PT'},
                                              foregroundColor={'opaqueColor': {'rgbColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2}}}
                                          ))

                # Calculate colors based on slide index
                if custom_colors:
                    # Use a more vibrant color scheme
                    hue = (i / num_slides) * 360  # Rotate through color wheel
                    saturation = 0.8
                    value = 0.9
                    rgb = self._hsv_to_rgb(hue, saturation, value)
                    shape_color = {'red': rgb[0], 'green': rgb[1], 'blue': rgb[2]}
                else:
                    # Use original color scheme
                    red = (i + 1) / num_slides
                    shape_color = {'red': red, 'green': 0.4, 'blue': 0.4}

                # Add shapes in a grid layout
                start_left = 50
                start_top = 180
                shape_width = 250
                shape_height = 150
                shapes_per_row = 2
                
                for idx, shape_type in enumerate(shapes_to_use):
                    row = idx // shapes_per_row
                    col = idx % shapes_per_row
                    left_pos = start_left + (col * (shape_width + 50))
                    top_pos = start_top + (row * (shape_height + 30))
                    
                    self.add_shape(pres_id, slide_id, shape_type.value,
                                 position=Position(left=left_pos, top=top_pos),
                                 size=Size(width=shape_width, height=shape_height),
                                 fill_color=shape_color)

                # Only add image if validation passed
                if is_valid_image:
                    try:
                        self.add_image(pres_id, slide_id, image_url,
                                     position=Position(left=600, top=180),
                                     size=Size(width=300, height=200))
                        logger.info(f"Successfully added image to slide {i+1}")
                    except Exception as e:
                        logger.error(f"Failed to add image to slide {i+1}: {str(e)}")

            presentation_url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
            return {
                "presentation_id": pres_id,
                "title": title,
                "url": presentation_url,
                "num_slides": num_slides
            }

        except Exception as e:
            logger.error(f"Error creating multi-style presentation: {str(e)}")
            raise

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> tuple:
        """Convert HSV color values to RGB."""
        h = float(h)
        s = float(s)
        v = float(v)
        h60 = h / 60.0
        h60f = float(int(h60))
        hi = int(h60f) % 6
        f = h60 - h60f
        p = v * (1 - s)
        q = v * (1 - f * s)
        t = v * (1 - (1 - f) * s)
        r, g, b = 0, 0, 0
        if hi == 0: r, g, b = v, t, p
        elif hi == 1: r, g, b = q, v, p
        elif hi == 2: r, g, b = p, v, t
        elif hi == 3: r, g, b = p, q, v
        elif hi == 4: r, g, b = t, p, v
        elif hi == 5: r, g, b = v, p, q
        return r, g, b 