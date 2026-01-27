
# Agentic Workspace

**Agentic Workspace** is a local, desktop-based AI assistant powered by Perplexity's `sonar-pro` model and the **Agno** (formerly PhiData) framework. It combines a sleek, modern UI with robust local memory and RAG (Retrieval-Augmented Generation) capabilities, packaged as a standalone desktop application.



## 🚀 Features

*   **Desktop Native**: Built with `pywebview` for a lightweight, native window experience (no browser tabs required).
*   **Intelligent Agent**: Uses **Perplexity Sonar Pro** for high-quality, up-to-date reasoning and search.
*   **Persistent Memory**:
    *   **Chat History**: Automatically saved to a local SQLite database (`~/.myapp/chat_history.db`).
    *   **Context Awareness**: The agent remembers past conversations and user details across sessions.
*   **Local Knowledge Base**: Integrated **LanceDB** vector database for future RAG capabilities (document storage).
*   **Interactive UI**:
    *   **Real-time Streaming**: Watch the agent "think" and type out responses.
    *   **Markdown Rendering**: Full support for code blocks, tables, and formatted text.
    *   **Checkpoints**: Bookmark interesting responses to a dedicated sidebar for quick access.
    *   **Smart Controls**: "Redo" generations, copy-to-clipboard, and in-app API key management.

## 🛠️ Tech Stack

*   **Framework**: [Agno](https://github.com/agno-ai/agno) (AI Agent orchestration)
*   **GUI**: [pywebview](https://pywebview.flowrl.com/) (Desktop window engine)
*   **Database**: SQLite (History) & LanceDB (Vector Knowledge)
*   **Frontend**: HTML5, CSS3, Vanilla JS (with `anime.js` for animations)
*   **Model Provider**: Perplexity API

## 📦 Installation

### Prerequisites
*   Python 3.10+
*   A [Perplexity API Key](https://www.perplexity.ai/)

### Steps

1.  **Clone the repository**
    ```bash
    git clone https://github.com/Lmao53and2/agentic_workspace.git
    cd agentic_workspace
    ```

2.  **Create a virtual environment**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # Mac/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables**
    Create a `.env` file in the root directory:
    ```ini
    PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxx
    ```
    *(Alternatively, you can enter your key directly in the app's UI settings)*

## 🖥️ Usage

Run the application:
```bash
python app.py
```

The application window will launch. If you haven't set your API key in the `.env` file, enter it in the top-right input field and click **Save**.

## 🧠 Project Structure

*   `app.py`: Main entry point. Initializes the database, API bridge, and GUI window.
*   `agents/workspace_agent.py`: Defines the Agno agent, including memory (SQLite) and knowledge (LanceDB) configuration.
*   `api/bridge.py`: Connects the Python backend to the JavaScript frontend, handling threading and streaming.
*   `database.py`: Handles raw SQLite operations for chat history persistence.
*   `ui/`: Contains the frontend assets (`index.html`, CSS, JS logic).

## 🔮 Future Roadmap

*   [ ] Drag-and-drop file upload for RAG (PDF/CSV analysis).
*   [ ] Multi-agent support (Researcher, Coder, Planner).
*   [ ] Voice input/output integration.
*   [ ] One-click executable generation with `pyinstaller`.


