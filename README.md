# treblle-flask

Treblle makes it super easy to understand what’s going on with your APIs and the apps that use them. Just by adding Treblle to your API out of the box you get:

- Real-time API monitoring and logging
- Auto-generated API docs with OAS support
- API analytics
- Quality scoring
- One-click testing
- API management on the go and more...


## Requirements

- requests

## Examples

### Basic Usage

You can use Treblle with Flask by importing the Treblle class and passing your Flask app to the constructor.

```python
from treblle_flask import Treblle

app = Flask(__name__)
Treblle(app)

@app.route('/hello')
def hello():
    return 'Hello, World!'
```

### Advanced Usage

You can also pass your Treblle API key and project ID to the Treblle constructor.

```python
from treblle_flask import Treblle

app = Flask(__name__)
Treblle(app, TREBLLE_API_KEY="YOUR_API_KEY", TREBLLE_PROJECT_ID="https://api.treblle.com")

@app.route('/hello')
def hello():
    return 'Hello, World!'
```

### Environment Variables

You can set the following environment variables to configure Treblle without passing any arguments to the Treblle constructor:

- `TREBLLE_API_KEY`: Your Treblle API key
- `TREBLLE_PROJECT_ID`: Your Treblle project ID
