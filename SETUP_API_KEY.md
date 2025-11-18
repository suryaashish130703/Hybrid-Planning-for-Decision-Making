# Setting Up API Key

## Error: Missing GEMINI_API_KEY

If you see this error:
```
ValueError: Missing key inputs argument! To use the Google AI API, provide (`api_key`) arguments.
```

You need to set up your Gemini API key.

## Quick Setup

### Option 1: Create .env File (Recommended)

1. **Create a `.env` file** in the project root directory:
   ```
   C:\Users\surya\Downloads\S9 (1)\.env
   ```

2. **Add your API key:**
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

3. **Get your API key:**
   - Go to: https://aistudio.google.com/app/apikey
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy the key

4. **Paste it in `.env`:**
   ```
   GEMINI_API_KEY=AIzaSy...your_key_here
   ```

### Option 2: Set Environment Variable (Windows)

**Windows CMD:**
```cmd
set GEMINI_API_KEY=your_api_key_here
python agent.py
```

**Windows PowerShell:**
```powershell
$env:GEMINI_API_KEY='your_api_key_here'
python agent.py
```

**Windows (Permanent):**
1. Right-click "This PC" → Properties
2. Advanced system settings → Environment Variables
3. New → Variable name: `GEMINI_API_KEY`, Value: `your_key`
4. OK and restart terminal

### Option 3: Set Environment Variable (Linux/Mac)

```bash
export GEMINI_API_KEY=your_api_key_here
python agent.py
```

**Permanent (Linux/Mac):**
Add to `~/.bashrc` or `~/.zshrc`:
```bash
export GEMINI_API_KEY=your_api_key_here
```

## Verify Setup

After setting up, verify the key is loaded:

**Python test:**
```python
import os
from dotenv import load_dotenv
load_dotenv()
print("API Key:", os.getenv("GEMINI_API_KEY")[:10] + "..." if os.getenv("GEMINI_API_KEY") else "NOT SET")
```

## Alternative: Use Ollama (Local, No API Key)

If you don't want to use Gemini API, you can switch to Ollama (local models):

1. **Install Ollama:**
   - Download from: https://ollama.ai
   - Install and run Ollama

2. **Pull a model:**
   ```bash
   ollama pull phi4
   # or
   ollama pull gemma3:12b
   ```

3. **Update `config/profiles.yaml`:**
   ```yaml
   llm:
     text_generation: phi4  # Change from 'gemini' to 'phi4' or 'gemma3:12b'
     embedding: nomic
   ```

4. **Run agent:**
   ```bash
   python agent.py
   ```

## Troubleshooting

### .env file not loading?

Make sure:
- File is named exactly `.env` (not `.env.txt`)
- File is in the project root (same directory as `agent.py`)
- File contains: `GEMINI_API_KEY=your_key` (no spaces around `=`)

### Still getting error?

1. Check if `.env` file exists:
   ```bash
   dir .env  # Windows
   ls -la .env  # Linux/Mac
   ```

2. Check if key is loaded:
   ```python
   from dotenv import load_dotenv
   import os
   load_dotenv()
   print(os.getenv("GEMINI_API_KEY"))
   ```

3. Try setting environment variable directly:
   ```bash
   # Windows CMD
   set GEMINI_API_KEY=your_key && python agent.py
   ```

## Security Note

⚠️ **Never commit `.env` file to Git!**

The `.env` file should be in `.gitignore`:
```
.env
*.env
```

Your `.env.example` file (without real keys) can be committed.

