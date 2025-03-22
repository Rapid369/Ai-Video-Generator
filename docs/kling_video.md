Set the REPLICATE_API_TOKEN environment variable

export REPLICATE_API_TOKEN=<paste-your-token-here>

Visibility

Copy
Learn more about authentication

Install Replicate’s Python client library

pip install replicate

Copy
Learn more about setup
Run kwaivgi/kling-v1.6-standard using Replicate’s API. Check out the model's schema for an overview of inputs and outputs.

import replicate

input = {
    "prompt": "a portrait photo of a woman underwater with flowing hair",
    "start_image": "https://replicate.delivery/pbxt/MNRKHnYUu5HjNqEerj2kxWRmUD3xWGaZ0gJmhqVbkra2jCbD/underwater.jpeg"
}

output = replicate.run(
    "kwaivgi/kling-v1.6-standard",
    input=input
)
with open("output.mp4", "wb") as file:
    file.write(output.read())
#=> output.mp4 written to disk

Run the model
Use the replicate.run() method to run the model:

input = {
    "prompt": "a portrait photo of a woman underwater with flowing hair",
    "start_image": "https://replicate.delivery/pbxt/MNRKHnYUu5HjNqEerj2kxWRmUD3xWGaZ0gJmhqVbkra2jCbD/underwater.jpeg"
}

output = replicate.run(
    "kwaivgi/kling-v1.6-standard",
    input=input
)
with open("output.mp4", "wb") as file:
    file.write(output.read())
#=> output.mp4 written to disk

Copy
You can learn about pricing for this model on the model page.

The run() function returns the output directly, which you can then use or pass as the input to another model. If you want to access the full prediction object (not just the output), use the replicate.predictions.create() method instead. This will return a Prediction object that includes the prediction id, status, logs, etc.

File inputs
This model accepts files as input, e.g. start_image. You can provide a file as input using a URL, a local file on your computer, or a base64 encoded object:

Option 1: Hosted file
Use a URL as in the earlier example:

start_image = "https://replicate.delivery/pbxt/MNRKHnYUu5HjNqEerj2kxWRmUD3xWGaZ0gJmhqVbkra2jCbD/underwater.jpeg";

Copy
This is useful if you already have a file hosted somewhere on the internet.

Option 2: Local file
You can provide Replicate with a file object and the library will handle the upload for you:

start_image = open("./path/to/my/start_image.jpeg", "rb");

Copy
Option 3: Data URI
Lastly, you can create a data URI consisting of the base64 encoded data for your file, but this is only recommended if the file is < 1mb:

import base64

with open("./path/to/my/start_image.jpeg", 'rb') as file:
  data = base64.b64encode(file.read()).decode('utf-8')
  start_image = f"data:application/octet-stream;base64,{data}"

Copy
Then pass the file as part of the input:

input = {
    "prompt": "a portrait photo of a woman underwater with flowing hair",
    "start_image": start_image
}

output = replicate.run(
    "kwaivgi/kling-v1.6-standard",
    input=input
)
with open("output.mp4", "wb") as file:
    file.write(output.read())
#=> output.mp4 written to disk

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
    "prompt": "a portrait photo of a woman underwater with flowing hair",
    "start_image": "https://replicate.delivery/pbxt/MNRKHnYUu5HjNqEerj2kxWRmUD3xWGaZ0gJmhqVbkra2jCbD/underwater.jpeg"
}

callback_url = "https://my.app/webhooks/replicate"
replicate.predictions.create(
  model="kwaivgi/kling-v1.6-standard",
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
    "prompt": "a portrait photo of a woman underwater with flowing hair",
    "start_image": "https://replicate.delivery/pbxt/MNRKHnYUu5HjNqEerj2kxWRmUD3xWGaZ0gJmhqVbkra2jCbD/underwater.jpeg"
}

prediction = replicate.predictions.create(
  model="kwaivgi/kling-v1.6-standard",
  input=input
)
#=> Prediction(id='z3wbih3bs64of7lmykbk7tsdf4', ...)

Copy
Cancel a prediction
You may need to cancel a prediction. Perhaps the user has navigated away from the browser or canceled your application. To prevent unnecessary work and reduce runtime costs you can use prediction.cancel() method to call the predictions.cancel endpoint.

input = {
    "prompt": "a portrait photo of a woman underwater with flowing hair",
    "start_image": "https://replicate.delivery/pbxt/MNRKHnYUu5HjNqEerj2kxWRmUD3xWGaZ0gJmhqVbkra2jCbD/underwater.jpeg"
}

prediction = replicate.predictions.create(
  model="kwaivgi/kling-v1.6-standard",
  input=input
)

prediction.cancel()

Copy
Async Python methods
asyncio is a module built into Python's standard library for writing concurrent code using the async/await syntax.

Replicate's Python client has support for asyncio. Each of the methods has an async equivalent prefixed with async_<name>.

input = {
    "prompt": "a portrait photo of a woman underwater with flowing hair",
    "start_image": "https://replicate.delivery/pbxt/MNRKHnYUu5HjNqEerj2kxWRmUD3xWGaZ0gJmhqVbkra2jCbD/underwater.jpeg"
}

prediction = replicate.predictions.create(
  model="kwaivgi/kling-v1.6-standard",
  input=input
)

prediction = await replicate.predictions.async_create(
  model="kwaivgi/kling-v1.6-standard",
  input=input
)

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
    "prompt": {
      "type": "string",
      "title": "Prompt",
      "x-order": 0,
      "description": "Text prompt for video generation"
    },
    "duration": {
      "enum": [
        5,
        10
      ],
      "type": "integer",
      "title": "duration",
      "description": "Duration of the video in seconds",
      "default": 5,
      "x-order": 5
    },
    "cfg_scale": {
      "type": "number",
      "title": "Cfg Scale",
      "default": 0.5,
      "maximum": 1,
      "minimum": 0,
      "x-order": 4,
      "description": "Flexibility in video generation; The higher the value, the lower the model's degree of flexibility, and the stronger the relevance to the user's prompt."
    },
    "start_image": {
      "type": "string",
      "title": "Start Image",
      "format": "uri",
      "x-order": 3,
      "description": "First frame of the video"
    },
    "aspect_ratio": {
      "enum": [
        "16:9",
        "9:16",
        "1:1"
      ],
      "type": "string",
      "title": "aspect_ratio",
      "description": "Aspect ratio of the video. Ignored if start_image is provided.",
      "default": "16:9",
      "x-order": 2
    },
    "negative_prompt": {
      "type": "string",
      "title": "Negative Prompt",
      "default": "",
      "x-order": 1,
      "description": "Things you do not want to see in the video"
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