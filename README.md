<div align="center">
  <img src="https://github.com/user-attachments/assets/b268ae9e-7c8a-4ade-95da-b4ac6fce6eea"/>
</div>
<div align="center">

# Treblle

<a href="https://docs.treblle.com/en/integrations" target="_blank">Integrations</a>
<span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
<a href="http://treblle.com/" target="_blank">Website</a>
<span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
<a href="https://docs.treblle.com" target="_blank">Docs</a>
<span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
<a href="https://blog.treblle.com" target="_blank">Blog</a>
<span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
<a href="https://twitter.com/treblleapi" target="_blank">Twitter</a>
<span>&nbsp;&nbsp;•&nbsp;&nbsp;</span>
<a href="https://treblle.com/chat" target="_blank">Discord</a>
<br />

  <hr />
</div>

API Intelligence Platform. 🚀

Treblle is a lightweight SDK that helps Engineering and Product teams build, ship & maintain REST-based APIs faster.

## Features

<div align="center">
  <br />
  <img src="https://github.com/user-attachments/assets/02afd9f5-ab47-48ff-929a-0f3fcddcca34"/>
  <br />
  <br />
</div>

- [API Monitoring & Observability](https://www.treblle.com/features/api-monitoring-observability)
- [Auto-generated API Docs](https://www.treblle.com/features/auto-generated-api-docs)
- [API analytics](https://www.treblle.com/features/api-analytics)
- [Treblle API Score](https://www.treblle.com/features/api-quality-score)
- [API Lifecycle Collaboration](https://www.treblle.com/features/api-lifecycle)
- [Native Treblle Apps](https://www.treblle.com/features/native-apps)


## treblle-flask

Treblle makes it super easy to understand what’s going on with your APIs and the apps that use them.
Just by adding Treblle to your API out of the box you get:

- Real-time API monitoring and logging
- Auto-generated API docs with OAS support
- API analytics
- Quality scoring
- One-click testing
- API management on the go and more...


## Requirements

- python 3.7+
- aiohttp

## Basic Usage

You can use Treblle with Flask by importing the Treblle class and passing your Flask app to the constructor, 
along with your Treblle API key and project ID.

```python
from flask import Flask
from treblle_flask import Treblle

app = Flask(__name__)
Treblle(app, TREBLLE_API_KEY="YOUR_API_KEY", TREBLLE_PROJECT_ID="YOUR_PROJECT_ID")

@app.route('/hello')
def hello():
    return {"hello": "world"}
```

Alternatively, set the following environment variables to configure Treblle without passing any arguments to the 
Treblle constructor:

- `TREBLLE_API_KEY`: Your Treblle API key
- `TREBLLE_PROJECT_ID`: Your Treblle project ID

That's it! You're all set to start monitoring your API with Treblle.


## Advanced Usage

A number of optional configuration options are available to customize the behavior of Treblle extension:

- `hidden_keys`: A list of keys that should be hidden from the request/response payloads in the Treblle dashboard. 
  Treblle will automatically hide any keys that contain the strings in this list, or use a default list with common
  sensitive keys if this option is not provided.
- `mask_auth_header`: A boolean flag that determines whether the Authorization header should be masked in the Treblle
  dashboard. The default value is `True`. Masking the Authorization header will keep the auth type (e.g. Bearer),
  visible, but will replace the actual secret with asterisks. If you intend to fo fully hide the header including the
  directive, just include it in the `hidden_keys` argument.
- `limit_request_body_size`: The maximum size of the request body that Treblle will attempt to capture. If the request
  body exceeds this size, it will be ignored to prevent excessive memory usage. The default value is 4MiB.
- `request_transformer`: A request body transformer function. If passed, this function will receive the original 
  request body as a bytestring, and should return a JSON-serializable object that will be sent to Treblle. You can use
  this function to mask sensitive data in a more customized fashion, remove excess data you don't wish to be logged,
  or perform any other transformations you require.
  - **Important:** This function will cause the entire request body to be loaded into memory.
  - **Important:** Using this function will override the default request body parsing logic - if the request body is a
    JSON-encoded string, transformer must return a parsed JSON object, not the string itself.
- `response_transformer`: A response body transformer function. If passed, this function will receive the original 
  response body as a bytestring, and should return a JSON-serializable object that will be sent to Treblle. You can use
  this function to mask sensitive data in a more customized fashion, remove excess data you don't wish to be logged,
  or perform any other transformations you require. 
  - **Important:** This function will not trigger for streaming responses.
  - **Important:** Using this function will override the default request body parsing logic - if the response body is a
    JSON-encoded string, transformer must return a parsed JSON object, not the string itself.
