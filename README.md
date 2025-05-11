# BloxMate

BloxMate is a comprehensive employee assistance platform that integrates multiple workplace tools and AI-powered assistants to enhance productivity and streamline onboarding processes.

## 🌟 Features

- **Intelligent Chatbot**: AI-powered assistant for workplace questions
- **LinkedIn Learning Integration**: Search and get enhanced descriptions of relevant LinkedIn Learning courses
- **Onboarding Assistant**: Streamlined process for new employees
- **Workplace Communications Helper**: Assist with drafting professional communications
- **Organization Chart Explorer**: Navigate company structure with natural language

## 🏗️ Project Structure

```
BloxMate/
├── public/              # Static files
├── src/                 # React frontend code
│   ├── components/      # React components
│   └── images/          # UI assets
└── server/              # Python backend
    ├── api.py           # API endpoints
    ├── app.py           # Main application entry point
    ├── linkedin.py      # LinkedIn Learning course finder
    ├── onboarding.py    # Onboarding assistance module
    ├── org_chart_bot.py # Organization chart explorer
    └── more...          # Additional backend modules
```

## 🚀 Getting Started

### Prerequisites

- Node.js (v16+)
- Python (v3.10+)
- npm or yarn

### Frontend Setup

```bash
# Install dependencies
npm install

# Start the development server
npm start
```

The application will be available at http://localhost:3000.

### Backend Setup

```bash
# Navigate to the server directory
cd server

# Install Python dependencies
pip install -r requirements.txt

# Start the Flask server
python app.py
```

The API server will run on http://localhost:5000.

## 🔧 Technologies Used

### Frontend
- React
- Material UI
- Chakra UI
- React Router

### Backend
- Python
- Flask
- Azure OpenAI
- SerpAPI (for LinkedIn course search)

## 📝 API Keys Setup

Some backend features require API keys to function:

1. Azure OpenAI API credentials
2. SerpAPI key

Add your keys to the appropriate configuration files or use environment variables.

## 📚 Main Features Explained

### LinkedIn Learning Course Finder
Uses SerpAPI to search for relevant LinkedIn Learning courses based on user queries and enhances the results with AI-generated descriptions.

### Onboarding Assistant
Helps new employees navigate company resources, policies, and procedures through an interactive question-answering interface.

### Organization Chart Explorer
Allows employees to navigate the company organization structure through natural language queries.

## 🤝 Contributing

Project by Saloni P and Vidhi V for Infoblox HackFest'25

