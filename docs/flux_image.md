
black-forest-labs / flux-pro 

State-of-the-art image generation with top of the line prompt following, visual quality, image detail and output diversity.

Set the REPLICATE_API_TOKEN environment variable

export REPLICATE_API_TOKEN=<paste-your-token-here>

Visibility

Copy
Learn more about authentication

Install Replicate’s Python client library

pip install replicate

Copy
Learn more about setup
Run black-forest-labs/flux-pro using Replicate’s API. Check out the model's schema for an overview of inputs and outputs.

import replicate

input = {
    "width": 1024,
    "height": 1024,
    "prompt": "The world's largest black forest cake, the size of a building, surrounded by trees of the black forest"
}

output = replicate.run(
    "black-forest-labs/flux-pro",
    input=input
)
with open("output.jpg", "wb") as file:
    file.write(output.read())
#=> output.jpg written to disk

Authentication
Whenever you make an API request, you need to authenticate using a token. A token is like a password that uniquely identifies your account and grants you access.

The following examples all expect your Replicate access token to be available from the command line. Because tokens are secrets, they should not be in your code. They should instead be stored in environment variables. Replicate clients look for the REPLICATE_API_TOKEN environment variable and use it if available.

To set this up you can use:

export REPLICATE_API_TOKEN=<paste-your-token-here>

Visibility

Copy
Some application frameworks and tools also support a text file named .env which you can edit to include the same token:

REPLICATE_API_TOKEN=<paste-your-token-here>

Visibility

Copy
The Replicate API uses the Authorization HTTP header to authenticate requests. If you’re using a client library this is handled for you.

You can test that your access token is setup correctly by using our account.get endpoint:

What is cURL?
curl https://api.replicate.com/v1/account -H "Authorization: Bearer $REPLICATE_API_TOKEN"
# {"type":"user","username":"aron","name":"Aron Carroll","github_url":"https://github.com/aron"}

Copy
If it is working correctly you will see a JSON object returned containing some information about your account, otherwise ensure that your token is available:

echo "$REPLICATE_API_TOKEN"
# "r8_xyz"

Copy
Setup
First you’ll need to ensure you have a Python environment setup:

python -m venv .venv
source .venv/bin/activate

Copy
Then install the replicate Python library:

pip install replicate

Copy
In a main.py file, import replicate:

import replicate

Copy
This will use the REPLICATE_API_TOKEN API token you’ve set up in your environment for authorization.

Run the model
Use the replicate.run() method to run the model:

input = {
    "width": 1024,
    "height": 1024,
    "prompt": "The world's largest black forest cake, the size of a building, surrounded by trees of the black forest"
}

output = replicate.run(
    "black-forest-labs/flux-pro",
    input=input
)
with open("output.jpg", "wb") as file:
    file.write(output.read())
#=> output.jpg written to disk

Copy
You can learn about pricing for this model on the model page.

The run() function returns the output directly, which you can then use or pass as the input to another model. If you want to access the full prediction object (not just the output), use the replicate.predictions.create() method instead. This will return a Prediction object that includes the prediction id, status, logs, etc.

File inputs
This model accepts files as input, e.g. image_prompt. You can provide a file as input using a URL, a local file on your computer, or a base64 encoded object:

Option 1: Hosted file
Use a URL as in the earlier example:

image_prompt = "https://example.com/path/to/image_prompt";

Copy
This is useful if you already have a file hosted somewhere on the internet.

Option 2: Local file
You can provide Replicate with a file object and the library will handle the upload for you:

image_prompt = open("./path/to/my/image_prompt", "rb");

Copy
Option 3: Data URI
Lastly, you can create a data URI consisting of the base64 encoded data for your file, but this is only recommended if the file is < 1mb:

import base64

with open("./path/to/my/image_prompt", 'rb') as file:
  data = base64.b64encode(file.read()).decode('utf-8')
  image_prompt = f"data:application/octet-stream;base64,{data}"

Copy
Then pass the file as part of the input:

input = {
    "width": 1024,
    "height": 1024,
    "prompt": "The world's largest black forest cake, the size of a building, surrounded by trees of the black forest",
    "image_prompt": image_prompt
}

output = replicate.run(
    "black-forest-labs/flux-pro",
    input=input
)
with open("output.jpg", "wb") as file:
    file.write(output.read())
#=> output.jpg written to disk

Copy
Prediction lifecycle
Running predictions and trainings can often take significant time to complete, beyond what is reasonable for an HTTP request/response.

When you run a model on Replicate, the prediction is created with a “starting” state, then instantly returned. This will then move to "processing" and eventual one of “successful”, "failed" or "canceled".

Starting
Running
Succeeded
Failed
Canceled
You can explore the prediction lifecycle by using the prediction.reload() method update the prediction to it's latest state.

Show example
Webhooks
Webhooks provide real-time updates about your prediction. Specify an endpoint when you create a prediction, and Replicate will send HTTP POST requests to that URL when the prediction is created, updated, and finished.

It is possible to provide a URL to the predictions.create() function that will be requested by Replicate when the prediction status changes. This is an alternative to polling.

To receive webhooks you’ll need a web server. The following example uses AIOHTTP, a basic webserver built on top of Python’s asyncio library, but this pattern will apply to most frameworks.

Show example
Then create the prediction passing in the webhook URL and specify which events you want to receive out of "start" , "output" ”logs” and "completed".

input = {
    "width": 1024,
    "height": 1024,
    "prompt": "The world's largest black forest cake, the size of a building, surrounded by trees of the black forest"
}

callback_url = "https://my.app/webhooks/replicate"
replicate.predictions.create(
  model="black-forest-labs/flux-pro",
  input=input,
  webhook=callback_url,
  webhook_events_filter=["completed"]
)

# The server will now handle the event and log:
#=> Prediction(id='z3wbih3bs64of7lmykbk7tsdf4', ...)

Copy
The replicate.run() method is not used here. Because we're using webhooks, and we don’t need to poll for updates.

From a security perspective it is also possible to verify that the webhook came from Replicate, check out our documentation on verifying webhooks for more information.

Access a prediction
You may wish to access the prediction object. In these cases it’s easier to use the replicate.predictions.create() function, which return the prediction object.

Though note that these functions will only return the created prediction, and it will not wait for that prediction to be completed before returning. Use replicate.predictions.get() to fetch the latest prediction.

import replicate

input = {
    "width": 1024,
    "height": 1024,
    "prompt": "The world's largest black forest cake, the size of a building, surrounded by trees of the black forest"
}

prediction = replicate.predictions.create(
  model="black-forest-labs/flux-pro",
  input=input
)
#=> Prediction(id='z3wbih3bs64of7lmykbk7tsdf4', ...)

Copy
Cancel a prediction
You may need to cancel a prediction. Perhaps the user has navigated away from the browser or canceled your application. To prevent unnecessary work and reduce runtime costs you can use prediction.cancel() method to call the predictions.cancel endpoint.

input = {
    "width": 1024,
    "height": 1024,
    "prompt": "The world's largest black forest cake, the size of a building, surrounded by trees of the black forest"
}

prediction = replicate.predictions.create(
  model="black-forest-labs/flux-pro",
  input=input
)

prediction.cancel()

Copy
Async Python methods
asyncio is a module built into Python's standard library for writing concurrent code using the async/await syntax.

Replicate's Python client has support for asyncio. Each of the methods has an async equivalent prefixed with async_<name>.

input = {
    "width": 1024,
    "height": 1024,
    "prompt": "The world's largest black forest cake, the size of a building, surrounded by trees of the black forest"
}

prediction = replicate.predictions.create(
  model="black-forest-labs/flux-pro",
  input=input
)

prediction = await replicate.predictions.async_create(
  model="black-forest-labs/flux-pro",
  input=input

  Input schema
Table
JSON
{
  "type": "object",
  "title": "Input",
  "required": [
    "prompt"
  ],
  "properties": {
    "seed": {
      "type": "integer",
      "title": "Seed",
      "x-order": 10,
      "description": "Random seed. Set for reproducible generation"
    },
    "steps": {
      "type": "integer",
      "title": "Steps",
      "default": 25,
      "maximum": 50,
      "minimum": 1,
      "x-order": 5,
      "description": "Number of diffusion steps"
    },
    "width": {
      "type": "integer",
      "title": "Width",
      "maximum": 1440,
      "minimum": 256,
      "x-order": 3,
      "description": "Width of the generated image in text-to-image mode. Only used when aspect_ratio=custom. Must be a multiple of 32 (if it's not, it will be rounded to nearest multiple of 32). Note: Ignored in img2img and inpainting modes."
    },
    "height": {
      "type": "integer",
      "title": "Height",
      "maximum": 1440,
      "minimum": 256,
      "x-order": 4,
      "description": "Height of the generated image in text-to-image mode. Only used when aspect_ratio=custom. Must be a multiple of 32 (if it's not, it will be rounded to nearest multiple of 32). Note: Ignored in img2img and inpainting modes."
    },
    "prompt": {
      "type": "string",
      "title": "Prompt",
      "x-order": 0,
      "description": "Text prompt for image generation"
    },
    "guidance": {
      "type": "number",
      "title": "Guidance",
      "default": 3,
      "maximum": 5,
      "minimum": 2,
      "x-order": 6,
      "description": "Controls the balance between adherence to the text prompt and image quality/diversity. Higher values make the output more closely match the prompt but may reduce overall image quality. Lower values allow for more creative freedom but might produce results less relevant to the prompt."
    },
    "interval": {
      "type": "number",
      "title": "Interval",
      "default": 2,
      "maximum": 4,
      "minimum": 1,
      "x-order": 7,
      "description": "Interval is a setting that increases the variance in possible outputs letting the model be a tad more dynamic in what outputs it may produce in terms of composition, color, detail, and prompt interpretation. Setting this value low will ensure strong prompt following with more consistent outputs, setting it higher will produce more dynamic or varied outputs."
    },
    "aspect_ratio": {
      "enum": [
        "custom",
        "1:1",
        "16:9",
        "3:2",
        "2:3",
        "4:5",
        "5:4",
        "9:16",
        "3:4",
        "4:3"
      ],
      "type": "string",
      "title": "aspect_ratio",
      "description": "Aspect ratio for the generated image",
      "default": "1:1",
      "x-order": 2
    },
    "image_prompt": {
      "type": "string",
      "title": "Image Prompt",
      "format": "uri",
      "x-order": 1,
      "description": "Image to use with Flux Redux. This is used together with the text prompt to guide the generation towards the composition of the image_prompt. Must be jpeg, png, gif, or webp."
    },
    "output_format": {
      "enum": [
        "webp",
        "jpg",
        "png"
      ],
      "type": "string",
      "title": "output_format",
      "description": "Format of the output images.",
      "default": "webp",
      "x-order": 11
    },
    "output_quality": {
      "type": "integer",
      "title": "Output Quality",
      "default": 80,
      "maximum": 100,
      "minimum": 0,
      "x-order": 12,
      "description": "Quality when saving the output images, from 0 to 100. 100 is best quality, 0 is lowest quality. Not relevant for .png outputs"
    },
    "safety_tolerance": {
      "type": "integer",
      "title": "Safety Tolerance",
      "default": 2,
      "maximum": 6,
      "minimum": 1,
      "x-order": 8,
      "description": "Safety tolerance, 1 is most strict and 6 is most permissive"
    },
    "prompt_upsampling": {
      "type": "boolean",
      "title": "Prompt Upsampling",
      "default": false,
      "x-order": 9,
      "description": "Automatically modify the prompt for more creative generation"
    }
  }
}

Copy
Output schema
Table
JSON
{
  "type": "string",
  "title": "Output",
  "format": "uri"
}

Install Replicate’s Python client library
pip install replicate

Copy
Set the REPLICATE_API_TOKEN environment variable
export REPLICATE_API_TOKEN=<paste-your-token-here>

Visibility

Copy
Find your API token in your account settings.

Import the client
import replicate

Copy
Run black-forest-labs/flux-pro using Replicate’s API. Check out the model's schema for an overview of inputs and outputs.

output = replicate.run(
    "black-forest-labs/flux-pro",
    input={
        "steps": 25,
        "width": 1024,
        "height": 1024,
        "prompt": "Write this poem with cursive text on a background that fits the words:\n\nRoses are red\n  Violets are blue,\nSugar is sweet\n  And so are you."
    }
)
print(output)

Copy
To learn more, take a look at the guide on getting started with Python.