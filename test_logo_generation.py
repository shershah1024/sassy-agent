import os
from fal.toolkit import ImageGen

# Get the FAL API key from environment
fal_key = os.getenv('FAL_KEY')

# Initialize the image generator
image_generator = ImageGen(fal_key)

# Generate a logo
prompt = "A modern, minimalist tech company logo with abstract geometric shapes in blue and white"
result = image_generator.generate(
    prompt=prompt,
    size="1024x1024"
)

# Save the generated image
result.save("generated_logo.png")
print("Logo has been generated and saved as 'generated_logo.png'") 